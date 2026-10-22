// Trusted n8n Execute Command adapter; native ssh/sftp perform transport and pinning.
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';

const root='/opt/onticards-preview-ci';
const config=`${root}/ssh/config`;
const [pr,head,base]=process.argv.slice(2);
if(!/^[1-9][0-9]{0,6}$/.test(pr??'') || !/^[a-f0-9]{40}$/.test(head??'') || !/^[a-f0-9]{40}$/.test(base??'') || process.argv.length!==5) throw new Error('Rejected fixed input');
const identity={repository:'stepll2026/OntiCards',pr:Number(pr),head,base,contract:'preview-v1'};
const canonical=Object.fromEntries(Object.entries(identity).sort(([a],[b])=>a.localeCompare(b)));
const run=createHash('sha256').update(JSON.stringify(canonical)).digest('hex').slice(0,24);
const dir=`${root}/state/${run}`;
await fs.mkdir(dir,{recursive:true,mode:0o700});
async function exec(program,args,input,timeout=5400_000){
  return await new Promise((resolve,reject)=>{
    const child=spawn(program,args,{stdio:['pipe','pipe','pipe'],env:{PATH:'/usr/bin:/bin',HOME:'/home/node',LANG:'C.UTF-8'}});
    let out='',err='',size=0;
    const timer=setTimeout(()=>{child.kill('SIGTERM');reject(new Error('Bounded native operation timed out'));},timeout);
    child.stdout.on('data',b=>{size+=b.length;if(size>1024*1024){child.kill();reject(new Error('Unexpected command output size'));}else out+=b;});
    child.stderr.on('data',b=>{err=(err+b).slice(-2048);});
    child.on('error',reject);child.on('close',code=>{clearTimeout(timer);code===0?resolve(out):reject(new Error(`Native ${path.basename(program)} failed ${code}`));});
    if(input)child.stdin.write(input);child.stdin.end();
  });
}
async function ssh(alias,command,input){return JSON.parse(await exec('/usr/bin/ssh',['-F',config,'-T',alias,command],input));}
async function sftp(alias,commands){await exec('/usr/bin/sftp',['-F',config,'-b','-',alias],commands+'\n',1800_000);}
async function digest(file){
  const {createReadStream}=await import('node:fs');
  const hash=createHash('sha256');for await(const chunk of createReadStream(file))hash.update(chunk);return hash.digest('hex');
}
function sameIdentity(result){const wanted={...identity,run_id:run};if(!result.identity||Object.keys(result.identity).length!==Object.keys(wanted).length||Object.entries(wanted).some(([k,v])=>result.identity[k]!==v))throw new Error('Remote identity mismatch');}
const built=await ssh('preview-build',`onticards-preview-v1 build ${pr} ${head} ${base}`);sameIdentity(built);
if(built.state!=='built'||!/^[a-f0-9]{64}$/.test(built.manifest_sha256??''))throw new Error('Build not complete; same head/base is not silently retried');
const publication=await ssh('preview-publish',`onticards-artifact-v1 publish ${pr} ${head} ${base} ${built.manifest_sha256}`);sameIdentity(publication);
await fs.writeFile(`${dir}/publication.json`,JSON.stringify(publication,null,2),{mode:0o600});
if(publication.state!=='published')throw new Error('Registry publication incomplete; no automatic retry');
const publicationInput=JSON.stringify(publication),publicationSha=createHash('sha256').update(publicationInput).digest('hex');
const download=await ssh('preview-fetch',`onticards-artifact-v1 fetch ${pr} ${head} ${base} ${publicationSha}`,publicationInput);sameIdentity(download);
await fs.writeFile(`${dir}/download.json`,JSON.stringify(download,null,2),{mode:0o600});
if(download.state!=='downloaded'||!/^[a-f0-9]{64}$/.test(download.manifest_sha256??''))throw new Error('Exact registry digest download incomplete; no automatic retry');
const tested=await ssh('preview-test',`onticards-preview-v1 test ${pr} ${head} ${base} ${download.manifest_sha256}`);sameIdentity(tested);
await fs.writeFile(`${dir}/receipt.json`,JSON.stringify(tested,null,2),{mode:0o600});
if(tested.evidence_sha256){
  await sftp('preview-test-transfer',`get /outbox/${run}/evidence.tar ${dir}/evidence.tar`);
  if(await digest(`${dir}/evidence.tar`)!==tested.evidence_sha256)throw new Error('Evidence hash mismatch');
}
console.log(JSON.stringify({run_id:run,repository:identity.repository,pr:Number(pr),head,base,state:tested.state,api_and_non_model_browser_only:true,evidence_directory:dir,artifact_sha256:tested.evidence_sha256??null}));
