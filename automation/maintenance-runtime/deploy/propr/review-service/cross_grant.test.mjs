// Uses real isolated SQLite through the installed native Knex dependency.
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {findPriorOperation} from './receipt.mjs';
const require=createRequire('/usr/src/app/package.json');
const knex=require('knex');
const db=knex({client:'better-sqlite3',connection:{filename:':memory:'},useNullAsDefault:true});
let checks=0;
try {
  await db.schema.createTable('mcp_operations',t=>{for(const field of ['id','owner_id','grant_id','repository','tool','idempotency_key','state','lifecycle','payload_hash'])t.text(field);});
  const request={owner:'318866723',repository:'stepll2026/OntiCards',key:'review-fixture-only',hash:'exact-native-hash'};
  assert.equal(await findPriorOperation(db,request),null);checks++;
  for(const state of ['accepted','unknown','posted','failed','completed','cancelled']) {
    await db('mcp_operations').delete();
    await db('mcp_operations').insert({id:'old-native-operation',owner_id:request.owner,grant_id:'expired-previous-grant',repository:request.repository,tool:'review_pull_request',idempotency_key:request.key,state,lifecycle:state==='posted'?'accepted':state,payload_hash:request.hash});
    const recovered=await findPriorOperation(db,request);
    assert.equal(recovered.id,'old-native-operation');assert.equal(recovered.state,state);checks++;
    await assert.rejects(()=>findPriorOperation(db,{...request,hash:'different-payload'}),/NATIVE_IDEMPOTENCY_CONFLICT/);checks++;
  }
  assert.equal(await findPriorOperation(db,{...request,repository:'wrong/repository'}),null);checks++;
  assert.equal(await findPriorOperation(db,{...request,owner:'999'}),null);checks++;
  await db('mcp_operations').insert({id:'unexpected-duplicate',owner_id:request.owner,grant_id:'new-grant',repository:request.repository,tool:'review_pull_request',idempotency_key:request.key,state:'accepted',lifecycle:'accepted',payload_hash:request.hash});
  await assert.rejects(()=>findPriorOperation(db,request),/NATIVE_IDEMPOTENCY_CONFLICT/);checks++;
  console.log(JSON.stringify({passed:checks,total:checks,database:'isolated SQLite memory',production_rows_written:0,grant_changes:0,github_writes:0,model_calls:0}));
}finally{await db.destroy();}
