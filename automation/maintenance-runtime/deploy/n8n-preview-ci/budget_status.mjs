// Trusted native NewAPI account admission only; no lease creation or provider call.
import {readModelBudget} from './lease.mjs';
try { console.log(JSON.stringify(await readModelBudget())); }
catch(error) { const message=String(error?.message??''); const reason_code=/HTTP 429/.test(message)?'native_rate_limited':/HTTP 40[13]/.test(message)?'native_auth_rejected':/EACCES|ENOENT/.test(message)?'credential_file_unavailable':/scope changed|identity mismatch/.test(message)?'native_scope_mismatch':/outcome unavailable/.test(message)?'native_transport_unknown':'native_account_unverified'; console.log(JSON.stringify({state:'budget_unverifiable',checked_at:new Date().toISOString(),
  token_creation_calls:0,provider_calls:0,reason_code,reason:'Native account scope or balance could not be verified; operator review required'})); }
