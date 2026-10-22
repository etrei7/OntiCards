// Explicit once-only model phase; native token lifecycle and fixed SSH controller.
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createModelLease} from './lease.mjs';
const root='/opt/onticards-preview-ci';
const [pr,head,base]=process.argv.slice(2);
if(process.argv.length!==5||!/^[1-9][0-9]{0,6}$/.test(pr??'')||!/^[a-f0-9]{40}$/.test(head??'')||!/^[a-f0-9]{40}$/.test(base??''))throw new Error('Rejected fixed identity');
const identity={repository:'stepll2026/OntiCards',pr:Number(pr),head,base,contract:'preview-v1'};
identity.run_id=createHash('sha256').update(JSON.stringify(Object.fromEntries(Object.entries(identity).sort(([a],[b])=>a.localeCompare(b))))).digest('hex').slice(0,24);
const dir=`${root}/state/${identity.run_id}`;
const download=JSON.parse(await fs.readFile(`${dir}/download.json`,'utf8'));
if(download.state!=='downloaded'||!/^[a-f0-9]{64}$/.test(download.manifest_sha256)||Object.entries(identity).some(([k,v])=>download.identity[k]!==v))throw new Error('Exact previously downloaded artifact required');
async function execute(program,args,input,timeout=1200000){
  return new Promise((resolve,reject)=>{
    const child=spawn(program,args,{env:{PATH:'/usr/bin:/bin',HOME:'/home/node',LANG:'C.UTF-8',HTTPS_PROXY:'http://127.0.0.1:17891',HTTP_PROXY:'http://127.0.0.1:17891',NO_PROXY:'127.0.0.1,localhost'},stdio:['pipe','pipe','pipe']});
    let out='',size=0;const timer=setTimeout(()=>{child.kill('SIGTERM');reject(new Error('Bounded native model phase timed out'));},timeout);
    child.stdout.on('data',b=>{size+=b.length;if(size>1024*1024){child.kill();reject(new Error('Unexpected output size'));}else out+=b;});
    child.stderr.on('data',()=>{});child.stdin.on('error',()=>{});
    child.on('error',reject);child.on('close',code=>{clearTimeout(timer);code===0?resolve(out):reject(new Error(`Native fixed model phase failed ${code}`));});
    child.stdin.end(input);
  });
}
// The native App-authenticated revision subworkflow runs immediately before this stage and revokes its token.
let recovery=null;
try{recovery=JSON.parse(await fs.readFile(`${dir}/approved-model-recovery.json`,'utf8'));}
catch(error){if(error.code!=='ENOENT')throw new Error('Operator recovery receipt unreadable');}
let native;
try { native=await createModelLease(identity,dir,recovery); }
catch(error) {
  if(error.code!=='budget_exhausted')throw error;
  const summary={identity,state:'budget_exhausted',model_state:'not_started',lease:'not_issued',
    evidence_status:'not_started',api_key_in_output:false,provider_calls:0,
    reason:'Remaining native account quota cannot cover the bounded lease; trusted operator allocation required; no automatic reset or reissue'};
  await fs.writeFile(`${dir}/model-phase-status.json`,JSON.stringify(summary,null,2),{mode:0o600});
  console.log(JSON.stringify(summary));
  process.exit(0);
}
let result,phaseError,revocation='pending';
try{
  const input=JSON.stringify(native.lease);if(Buffer.byteLength(input)>4096)throw new Error('Lease exceeds fixed input bound');
  result=JSON.parse(await execute('ssh',['-F',`${root}/ssh/config`,'-T','preview-test',`onticards-preview-v1 test-model ${pr} ${head} ${base} ${download.manifest_sha256}`],input));
  if(Object.entries(identity).some(([k,v])=>result.identity?.[k]!==v))throw new Error('Model result identity mismatch');
  await fs.writeFile(`${dir}/model-test-receipt.json`,JSON.stringify(result,null,2),{mode:0o600});
}catch(error){phaseError=error;
}finally{
  try{await native.revoke();revocation='disabled_verified';}
  catch{
    revocation='revocation_unknown';
    const receipt=JSON.parse(await fs.readFile(`${dir}/model-lease.json`,'utf8'));
    receipt.state=revocation;receipt.failure='Native revocation outcome unknown; trusted operator reconciliation required; no reissue';
    await fs.writeFile(`${dir}/model-lease.json`,JSON.stringify(receipt,null,2),{mode:0o600});
  }
}
let evidenceStatus='not_available';
if(result?.evidence_sha256){
 try{
  const file=`${dir}/model-evidence.tar`;
  await execute('sftp',['-F',`${root}/ssh/config`,'-b','-','preview-test-transfer'],`get /outbox/${identity.run_id}-model/evidence.tar ${file}\n`,120000);
  const {createReadStream}=await import('node:fs');const hash=createHash('sha256');
  for await(const block of createReadStream(file))hash.update(block);
  if(hash.digest('hex')!==result.evidence_sha256)throw new Error('Model evidence hash mismatch');
  evidenceStatus='downloaded_hash_verified';
 }catch{evidenceStatus='evidence_download_failed';}
}
const summary={identity,state:revocation==='revocation_unknown'?'model_lease_revocation_unknown':(phaseError?'model_phase_transport_or_execution_failed':result.state),
  model_state:result?.state??'unknown',lease:revocation,evidence_status:evidenceStatus,api_key_in_output:false,revision_validation:'native_authenticated_subworkflow_before_and_after'};
await fs.writeFile(`${dir}/model-phase-status.json`,JSON.stringify(summary,null,2),{mode:0o600});
console.log(JSON.stringify(summary));
