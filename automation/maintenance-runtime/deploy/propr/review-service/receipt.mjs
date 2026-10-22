// Interpret the existing MCP operation envelope; never infer review completion.
export function projectReceipt(response, identity) {
  const row = response?.structuredContent?.data;
  const states = ['accepted', 'posted', 'queued', 'running', 'completed', 'failed', 'cancelled', 'unknown'];
  const lifecycles = ['accepted', 'running', 'completed', 'failed', 'cancelled', 'unknown'];
  const fail = () => { const e = new Error('NATIVE_RECEIPT_INVALID'); e.safeCode = e.message; throw e; };
  if (!row || !/^[a-f0-9-]{36}$/.test(row.operationId ?? '') || row.tool !== 'review_pull_request' ||
      !states.includes(row.state) || !lifecycles.includes(row.lifecycle?.state)) fail();
  const out = {state: 'native_' + row.state, operation_id: row.operationId, native_state: row.state,
    native_lifecycle: row.lifecycle.state, automatic_retry: false, model_started: null};
  const payload = row.result;
  if (row.state === 'posted') {
    if (response.isError === true || payload?.state !== 'posted' || payload.repository !== identity.repository ||
        payload.pullRequest !== identity.pr || payload.resolvedHead !== identity.head ||
        !Number.isSafeInteger(payload.commentId) || payload.commentId < 1 ||
        payload.url !== `https://github.com/${identity.repository}/pull/${identity.pr}#issuecomment-${payload.commentId}`) fail();
    Object.assign(out, {comment_id: payload.commentId, comment_url: payload.url, resolved_head: payload.resolvedHead});
  }
  const code = row.lifecycle?.failure?.code ?? payload?.error?.code;
  if (typeof code === 'string' && /^[A-Z][A-Z0-9_]{0,79}$/.test(code)) out.reason_code = code;
  return out;
}

export function projectFailure(error, mutationAttempted) {
  return {state: mutationAttempted ? 'submission_outcome_unknown' : 'review_admission_failed',
    reason_code: typeof error?.safeCode === 'string' ? error.safeCode : 'NATIVE_SERVICE_UNAVAILABLE',
    model_started: mutationAttempted ? null : false, automatic_retry: false};
}

export function requireRevocation(result) {
  if (result.grant_revocation === 'unknown') {
    return {...result, state: 'credential_cleanup_unknown', credential_cleanup_required: true, automatic_retry: false};
  }
  return result;
}

export async function findPriorOperation(db, {owner, repository, key, hash}) {
  const rows=await db('mcp_operations').where({owner_id:owner,repository,tool:'review_pull_request',idempotency_key:key})
    .select('id','state','lifecycle','payload_hash');
  if (!rows.length) return null;
  if (rows.length!==1 || rows[0].payload_hash!==hash) {
    const error=new Error('NATIVE_IDEMPOTENCY_CONFLICT'); error.safeCode=error.message; throw error;
  }
  return rows[0];
}
