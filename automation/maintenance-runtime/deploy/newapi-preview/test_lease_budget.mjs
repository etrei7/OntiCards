// Native quota admission regression: no real network, credential, token or supplier operation.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createModelLease} from './lease.mjs';

for (const remaining of [15445,44999,-1,1.5,null]) {
  test(`native quota ${remaining} rejects before token issuance or provider request`,async()=>{
    const originalRead=fs.readFile,originalFetch=globalThis.fetch,calls=[];
    const identity={repository:'stepll2026/OntiCards',pr:9999998,head:'1'.repeat(40),base:'2'.repeat(40),contract:'preview-v1'};
    identity.run_id=createHash('sha256').update(JSON.stringify(Object.fromEntries(Object.entries(identity).sort(([a],[b])=>a.localeCompare(b))))).digest('hex').slice(0,24);
    fs.readFile=async path=>{
      assert.equal(path,'/opt/onticards-preview-ci/secrets/newapi-account.json');
      return JSON.stringify({user_id:2,username:'onticards_preview',password:'fixture-only-not-a-real-password'});
    };
    globalThis.fetch=async(url,options)=>{
      calls.push({url,method:options.method});let data;
      if(url==='http://127.0.0.1:3000/api/user/login'&&options.method==='POST')data={user:{id:2,role:1},access_token:'fixture-only-no-token'};
      else if(url==='http://127.0.0.1:3000/api/user/self'&&options.method==='GET')data={quota:remaining,used_quota:84555,role:1,group:'onticards-preview'};
      else throw new Error('Unexpected request: token/provider must never be called');
      return {status:200,json:async()=>({success:true,data})};
    };
    try {
      await assert.rejects(()=>createModelLease(identity,'/opt/onticards-preview-ci/state/'+identity.run_id),error=>error.code==='budget_exhausted');
      assert.equal(calls.length,2);
      assert(calls.every(x=>!x.url.includes('/api/token')&&!x.url.includes('/v1/')));
    }finally{fs.readFile=originalRead;globalThis.fetch=originalFetch;}
  });
}
