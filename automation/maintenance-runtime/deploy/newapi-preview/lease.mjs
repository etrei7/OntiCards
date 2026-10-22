// Thin trusted-CI adapter for New API v1.0.0-rc.22 native token lifecycle.
// The existing service owns quotas, expiry, model/IP restrictions and revocation.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const endpoint='http://127.0.0.1:3000';
const group='onticards-preview',model='onticards-preview-qwen3.8-max-0902';
const embeddingModel='onticards-preview-qwen3.7-text-embedding-flash';
const modelLimits=[model,embeddingModel].join(',');
const accountPath='/opt/onticards-preview-ci/secrets/newapi-account.json';
const quota=45000,lifetime=900;
async function request(method,path,body,headers={}) {
    let response,value;
    try {
        response=await fetch(endpoint+path,{method,headers:{'Content-Type':'application/json',...headers},
            body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(20000)});
        value=await response.json();
    } catch {throw new Error('Native New API request outcome unavailable; no automatic retry');}
    if(response.status!==200 || value?.success!==true) throw new Error(`Native New API rejected request (HTTP ${response.status}); no automatic retry`);
    return value.data;
}
function validate(identity,dir) {
    if(identity.repository!=='stepll2026/OntiCards' || !Number.isSafeInteger(identity.pr) || identity.pr<1 ||
       !/^[a-f0-9]{40}$/.test(identity.head??'') || !/^[a-f0-9]{40}$/.test(identity.base??'') || identity.contract!=='preview-v1') throw new Error('Rejected lease identity');
    const {run_id,...rest}=identity;
    if(Object.keys(rest).length!==5) throw new Error('Unexpected identity field');
    const canonical=Object.fromEntries(Object.entries(rest).sort(([a],[b])=>a.localeCompare(b)));
    const expected=createHash('sha256').update(JSON.stringify(canonical)).digest('hex').slice(0,24);
    if(run_id!==expected || dir!==`/opt/onticards-preview-ci/state/${expected}`) throw new Error('Lease run or state directory mismatch');
}
async function ordinaryAccount() {
    const account=JSON.parse(await fs.readFile(accountPath,'utf8'));
    if(account.user_id!==2 || account.username!=='onticards_preview') throw new Error('Unexpected native account');
    const login=await request('POST','/api/user/login',{username:account.username,password:account.password});
    if(login.user?.id!==2 || login.user.role!==1 || typeof login.access_token!=='string') throw new Error('Native ordinary identity mismatch');
    const headers={Authorization:'Bearer '+login.access_token,'New-Api-User':'2'};
    const api=(method,path,body)=>request(method,path,body,headers);
    const profile=await api('GET','/api/user/self');
    if(profile.role!==1 || profile.group!==group) throw new Error('Native account scope changed');
    return {api,profile};
}
export async function readModelBudget() {
    const {profile}=await ordinaryAccount();
    const available=Number.isSafeInteger(profile.quota)&&profile.quota>=quota;
    return {state:available?'budget_available':'budget_exhausted',required_quota:quota,
        remaining_quota:Number.isSafeInteger(profile.quota)?profile.quota:null,
        checked_at:new Date().toISOString(),token_creation_calls:0,provider_calls:0,
        account_quota_reset:false};
}
export async function createModelLease(identity,dir,recovery=null) {
    validate(identity,dir);
    if(recovery!==null && (!['session-profile-r1','session-precision-r2','gateway-rate-r3','preconsume-budget-r4'].includes(recovery.recovery_id)||recovery.previous_token_id!==({'session-profile-r1':8,'session-precision-r2':9,'gateway-rate-r3':10,'preconsume-budget-r4':11}[recovery.recovery_id])||
      identity.run_id!=='19aa3bbf395b323dc3869bd6'||Object.keys(recovery).length!==2)) throw new Error('Unreviewed recovery rejected');
    const {api,profile}=await ordinaryAccount();
    if(!Number.isSafeInteger(profile.quota)||profile.quota<quota) {
        const error=new Error('budget_exhausted: remaining native quota cannot cover this lease; trusted operator allocation required; no reset or reissue');
        error.code='budget_exhausted';
        throw error;
    }
    if(recovery?.recovery_id==='preconsume-budget-r4' && (profile.quota!==55851||profile.used_quota!==44149)) throw new Error('Final approved recovery account accounting changed; review before creating token');
    if(recovery){
        const priorReceipt=JSON.parse(await fs.readFile(dir+'/model-lease.before-'+recovery.recovery_id+'.json','utf8'));
        const priorToken=await api('GET','/api/token/'+recovery.previous_token_id);
        const expectedUsed=recovery.recovery_id==='gateway-rate-r3'?13970:recovery.recovery_id==='preconsume-budget-r4'?30100:0;
        if(priorReceipt.token_id!==recovery.previous_token_id||priorReceipt.state!=='disabled_verified'||priorReceipt.used_quota!==expectedUsed||
          priorToken.status!==2||priorToken.used_quota!==expectedUsed) throw new Error('Previous lease must remain disabled with verified unchanged accounting before the approved fixture recovery');
    }
    const name='oc-preview-'+identity.run_id+(recovery?'-'+recovery.recovery_id.split('-').at(-1):'');
    if(Buffer.byteLength(name)>50)throw new Error('Native token name bound exceeded before creation');
    const prior=await api('GET','/api/token/search?keyword='+encodeURIComponent(name));
    if(prior.total!==0 || prior.items?.length!==0) throw new Error('A lease already exists for this exact run; reconcile instead of issuing again');
    const record={identity,name,state:'posting_unknown',started_at:new Date().toISOString(),
        expires_at:Math.floor(Date.now()/1000)+lifetime,quota,quota_unit:'Native test accounting units; supplier USD unknown',
        model,embedding_model:embeddingModel,group,account_remaining_before:profile.quota,account_used_before:profile.used_quota,account_quota_reset:false,allow_ips:'10.66.66.5',automatic_reissue:false,
        operator_recovery:recovery};
    const receipt=dir+'/model-lease.json';
    await fs.writeFile(receipt,JSON.stringify(record,null,2),{flag:'wx',mode:0o600});
    const save=()=>fs.writeFile(receipt,JSON.stringify(record,null,2),{mode:0o600});
    async function revoke() {
        if(!record.token_id) throw new Error('No confirmed token ID; inspect unknown native creation, never issue again');
        await api('PUT','/api/token/?status_only=true',{id:record.token_id,status:2});
        const item=await api('GET','/api/token/'+record.token_id);
        if(item.status!==2) throw new Error('Native token revocation could not be verified');
        Object.assign(record,{state:'disabled_verified',revoked_at:new Date().toISOString(),
            used_quota:item.used_quota,remain_quota:item.remain_quota,provider_cost_usd:null});
        await save();
        return {...record};
    }
    try {
        await api('POST','/api/token/',{name,expired_time:record.expires_at,remain_quota:quota,unlimited_quota:false,
            model_limits_enabled:true,model_limits:modelLimits,allow_ips:record.allow_ips,group,cross_group_retry:false});
        const results=await api('GET','/api/token/search?keyword='+encodeURIComponent(name));
        if(results.total!==1 || results.items?.length!==1 || results.items[0].name!==name) throw new Error('Native created lease is ambiguous');
        const item=results.items[0];
        record.token_id=item.id;record.state='created';await save();
        if(item.status!==1 || item.user_id!==2 || item.group!==group || item.model_limits!==modelLimits || !item.model_limits_enabled ||
           item.allow_ips!==record.allow_ips || item.expired_time!==record.expires_at || item.remain_quota!==quota || item.unlimited_quota || item.cross_group_retry) throw new Error('Native token restriction mismatch');
        const key=(await api('POST',`/api/token/${item.id}/key`)).key;
        if(typeof key!=='string' || key.length<16) throw new Error('Native token key missing');
        const lease={...identity,token_id:item.id,expires_at:record.expires_at,
            base_url:'http://10.66.66.5:18134/v1',model,embedding_model:embeddingModel,api_key:'sk-'+key};
        record.state='issued';await save();
        return {lease,revoke};
    } catch(error) {
        record.failure='Native lease operation failed; no reissue';await save();
        if(record.token_id) {try {await revoke();} catch {record.state='revocation_unknown';await save();}}
        throw error;
    }
}
