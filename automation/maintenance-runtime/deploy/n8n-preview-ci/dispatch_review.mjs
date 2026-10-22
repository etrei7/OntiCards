// Trusted n8n adapter to the one fixed, host-pinned OpenSSH capability.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
const [pr,head,base,mode]=process.argv.slice(2);
if(process.argv.length!==6||!/^[1-9][0-9]{0,6}$/.test(pr??'')||!/^[a-f0-9]{40}$/.test(head??'')||!/^[a-f0-9]{40}$/.test(base??'')||!['dry_run','review','status'].includes(mode))throw new Error('Invalid fixed review identity');
const request={repository:'stepll2026/OntiCards',pr:Number(pr),head,base,mode};
request.idempotency_key='review-'+createHash('sha256').update(JSON.stringify([request.repository,request.pr,head,base])).digest('hex');
let result;
try {
  const text=await new Promise((resolve,reject)=>{
    const child=spawn('/usr/bin/ssh',['-F','/opt/onticards-preview-ci/ssh/review_config','-T','automatic-review','onticards-fixed-review-v1'],
      {stdio:['pipe','pipe','pipe'],env:{PATH:'/usr/bin:/bin',HOME:'/home/node',LANG:'C.UTF-8'}});
    let out='',size=0;const timer=setTimeout(()=>{child.kill('SIGTERM');reject(new Error('timeout'));},240000);
    child.stdout.on('data',b=>{size+=b.length;if(size>16384){child.kill();reject(new Error('size'));}else out+=b;});
    child.stderr.resume();child.on('error',reject);child.on('close',code=>{clearTimeout(timer);code===0?resolve(out):reject(new Error('transport'));});
    child.stdin.end(JSON.stringify(request));
  });
  result=JSON.parse(text);
  if(!result||typeof result.state!=='string'||(result.repository!==undefined&&Object.entries(request).some(([k,v])=>result[k]!==v)))throw new Error('identity');
}catch{
  result={state:'submission_outcome_unknown',model_started:mode==='review'?null:false,automatic_retry:false};
}
console.log(JSON.stringify({...request,...result}));
