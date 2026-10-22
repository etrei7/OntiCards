"""Run shipped native Stop against isolated real Redis/SQLite, never production data."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

APP = 'registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy12@sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa'
REDIS = 'redis:7-alpine@sha256:e7723ff73d963f5cc6d9c4643ea3d989527a402a319239054e9472a7fb9219a2'
OUT = Path('/opt/onticards-maintenance/evidence/ac11-prequeue-stop-native.json')
CODE = r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import express from 'express';
import {createClient} from 'redis';
import {db,runMigrations,closeConnection} from './packages/core/dist/db/connection.js';
import {getStateManager,closeStateManager} from './packages/core/dist/utils/workerStateManager.js';
import {getIssueQueue,shutdownQueue} from './packages/core/dist/queue/taskQueue.js';
import {createDockerRoutes} from './dist/packages/api/routes/dockerRoutes.js';
const checks=[];function check(name,condition,observed){assert.ok(condition,name);checks.push({name,passed:true,...(observed===undefined?{}:{observed})});}
await runMigrations();
const redis=createClient({url:`redis://${process.env.REDIS_HOST}:6379`});await redis.connect();
const info=await redis.info('server');
const manager=getStateManager(),queue=await getIssueQueue();
const states=['waiting','delayed','active','prioritized','waiting-children','completed','failed'];
check('isolated queue starts empty',(await queue.getJobs(states)).length===0);
const app=express();
// Same bounded auth harness as upstream stopTaskRoutes.test.ts; production OAuth is not changed.
app.use('/api',(req,res,next)=>{if(req.get('x-fixture-actor')!=='ac11-test'){res.status(401).json({error:'Unauthorized'});return;}req.user={username:'ac11-test'};next();});
const routes=createDockerRoutes({redisClient:redis});
app.post('/api/task/:taskId/stop',routes.stopTask);app.post('/api/task/:taskId/cancel',routes.stopTask);
const server=app.listen(0,'127.0.0.1');await new Promise(r=>server.once('listening',r));
const origin=`http://127.0.0.1:${server.address().port}`;
const post=(id,suffix='stop',auth=true)=>fetch(`${origin}/api/task/${encodeURIComponent(id)}/${suffix}`,{method:'POST',headers:auth?{'x-fixture-actor':'ac11-test'}:{}});
const tasks=[];
for(const [index,suffix] of ['stop','cancel'].entries()){
 const id=`ac11-prequeue-${suffix}-${process.env.FIXTURE_RUN}`;
 const initial=await manager.createTaskStateIfAbsent(id,{repoOwner:'onticards-fixture',repoName:'prequeue',number:90001+index,type:'issue'},`ac11-${suffix}`);
 check(`${suffix}: native pending created`,initial.state==='pending');
 const task=await db('tasks').where({task_id:id}).first();check(`${suffix}: SQLite task exists before queue`,!!task&&task.job_id===null);
 check(`${suffix}: no BullMQ job created`,(await queue.getJobs(states)).length===0);
 const unauth=await post(id,suffix,false);check(`${suffix}: auth harness denies before mutation`,unauth.status===401&&(await manager.getTaskState(id)).state==='pending');
 const response=await post(id,suffix),body=await response.json();check(`${suffix}: native route succeeds without job/container`,response.status===200&&body.success===true&&body.containerStopped===false,{status:response.status,body});
 const state=await manager.getTaskState(id);check(`${suffix}: actual Redis terminal state`,state.state==='cancelled');
 const abort=JSON.parse(await redis.get(`worker:abort:${id}`));const ttl=await redis.ttl(`worker:abort:${id}`);
 check(`${suffix}: abort signal retained with user and bounded TTL`,abort.requestedBy==='ac11-test'&&ttl>0&&ttl<=3600,{ttl_seconds:ttl,requestedBy:abort.requestedBy});
 const history=await db('task_history').where({task_id:id}).orderBy('history_id','asc');const last=history.at(-1);const meta=JSON.parse(last.metadata);
 check(`${suffix}: SQLite terminal history persisted`,last.state==='cancelled'&&meta.cancellationReason==='cancelled_by_user',{states:history.map(x=>x.state),cancellationReason:meta.cancellationReason});
 const late=await manager.updateTaskState(id,'processing');check(`${suffix}: late worker transition cannot revive cancelled task`,late.state==='cancelled');
 const repeat=await post(id,suffix);check(`${suffix}: repeated Stop is rejected without revival`,repeat.status===400&&(await manager.getTaskState(id)).state==='cancelled',{status:repeat.status});
 check(`${suffix}: no queue entry or Agent created`,(await queue.getJobs(states)).length===0&&!state.history.some(x=>x.metadata?.containerId));
 tasks.push({task_id:id,final_state:state.state,job_id:task.job_id,history:history.map(x=>({state:x.state,reason:x.reason})),abort_ttl_seconds:ttl});
}
const missing=await post(`missing-${process.env.FIXTURE_RUN}`);check('unknown task returns 404',missing.status===404);
check('only two synthetic task records exist',Number((await db('tasks').count('* as count').first()).count)===2);
await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));
await redis.quit();await shutdownQueue();await closeStateManager();await closeConnection();
const paths=['packages/core/dist/services/taskCancellation.js','packages/core/dist/utils/workerStateManager.js','dist/packages/api/routes/dockerRoutes.js'];
console.log('AC11_RESULT='+JSON.stringify({passed:true,checks,checks_passed:checks.length,tasks,redis_version:info.match(/redis_version:([^\r\n]+)/)?.[1],compiled_files:Object.fromEntries(paths.map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')]))}));
process.exit(0);
'''

def call(args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kwargs)

def main():
    run = uuid.uuid4().hex[:12]
    redis_name, app_name = ['onticards-ac11-' + x + '-' + run for x in ('redis', 'probe')]
    result = {'schema': 'onticards-ac11-native-prequeue-stop-v1', 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'app_image': APP, 'redis_image': REDIS, 'run_id': run}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Only existing, pinned images: no pull/build and no production volumes or ports.
        for label, image in [('app', APP), ('redis', REDIS)]:
            result[label + '_image_id'] = json.loads(call(['docker', 'image', 'inspect', image]).stdout)[0]['Id']
        # Share the isolated loopback namespace; no Docker address-pool allocation needed.
        call(['docker', 'run', '-d', '--pull=never', '--name', redis_name, '--network', 'none', '--tmpfs', '/data:rw,noexec,nosuid,size=32m', '--memory', '128m', REDIS, 'redis-server', '--save', '', '--appendonly', 'no'])
        call(['docker', 'exec', redis_name, 'redis-cli', 'ping'])
        env = {'REDIS_HOST':'127.0.0.1','REDIS_PORT':'6379','GITHUB_ISSUE_QUEUE_NAME':'ac11-'+run,'INDEXING_QUEUE_NAME':'ac11-index-'+run,'DB_FILENAME':'/fixture/propr.sqlite','NODE_ENV':'production','PROPR_DEMO_MODE':'true','FIXTURE_RUN':run}
        command=['docker','run','--pull=never','--name',app_name,'--network','container:'+redis_name,'--tmpfs','/fixture:rw,nosuid,size=128m,mode=1777','--memory','512m','--cpus','1','-i']
        command += [part for key,value in env.items() for part in ['-e',key+'='+value]]
        command += [APP,'node','--input-type=module']
        completed=subprocess.run(command,input=CODE,text=True,capture_output=True,timeout=90)
        # Probe contains no credential and has no external network route. Retain red diagnostics if native assertions fail.
        result['exit_code']=completed.returncode
        lines=[x for x in completed.stdout.splitlines() if x.startswith('AC11_RESULT=')]
        if completed.returncode or len(lines)!=1:
            result.update(passed=False,error_category='native_probe_failed',diagnostic_stdout=completed.stdout[-14000:],diagnostic_stderr=completed.stderr[-10000:])
        else:
            result.update(json.loads(lines[0].split('=',1)[1]))
        inspection=json.loads(call(['docker','inspect',app_name]).stdout)[0]
        redis_inspection=json.loads(call(['docker','inspect',redis_name]).stdout)[0]
        result['isolation']={'redis_network':redis_inspection['HostConfig']['NetworkMode'],'network_mode':inspection['HostConfig']['NetworkMode'],'external_network':False,'host_ports':inspection['HostConfig']['PortBindings'] or {},'bind_mounts':inspection['HostConfig']['Binds'] or [],'model_calls':0,'github_requests':0,'workers_started':0,'production_data_mounted':False,'auth':'upstream test-style bounded actor middleware; no production OAuth bypass','native_demo_mode':'only isolated module fixture; no production configuration changed'}
    finally:
        for name in [app_name,redis_name]:
            subprocess.run(['docker','rm','-f',name],capture_output=True,text=True)
        result['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        result['probe_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['ephemeral_containers_removed']=all(subprocess.run(['docker','inspect',name],capture_output=True).returncode!=0 for name in [app_name,redis_name])
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':result.get('passed',False),'checks_passed':result.get('checks_passed',0),'evidence':str(OUT)}))
    return 0 if result.get('passed') else 1

if __name__=='__main__':
    raise SystemExit(main())
