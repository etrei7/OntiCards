"""Shared native-node configuration for bounded safe diagnostics; no HTTP client."""
def add_response_audit(builder,phase,http_node,event_expression):
 table='onticards_safe_model_responses_v1'
 names={key:phase+' '+label for key,label in [('ensure','ensure safe response audit'),('sanitize','sanitize model response'),('persist','persist safe model response'),('restore','restore response for validation')]}
 builder.table(names['ensure'],table,[('response_key','string'),('event_key','string'),('category','string'),('http_status','number'),('body_excerpt','string'),('body_truncated','boolean'),('usage','string'),('observed_at','string')])
 expression=r'''={{ (()=>{const r=$('HTTP_NODE').first().json,body=r.body||r,content=body.choices?.[0]?.message?.content,status=Number(r.statusCode||r.httpCode||r.error?.httpCode||0);const error=String(r.error?.message||r.error||body.error?.message||'');let category=typeof content==='string'?'assistant_content':status>=400?'http_error':/timeout|timed out/i.test(error)?'timeout':/JSON|parse/i.test(error)?'json_error':/ECONN|ENOTFOUND|socket|network/i.test(error)?'transport_error':'unknown_no_assistant_content';let text=typeof content==='string'?content:'';text=text.replace(/Bearer\s+[^\s"']+/gi,'Bearer [REDACTED]').replace(/(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]+/g,'[REDACTED_TOKEN]').replace(/\bsk-[A-Za-z0-9_-]{12,}/g,'[REDACTED_KEY]').replace(/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g,'[REDACTED_JWT]').replace(/((?:token|api[_-]?key|secret|password)["']?\s*[:=]\s*["']?)[^\s,"'\}]+/gi,'$1[REDACTED]');return {response_key:String($execution.id)+':PHASE',event_key:EVENT_EXPR,category,http_status:Number.isFinite(status)?status:0,body_excerpt:text.slice(0,16384),body_truncated:text.length>16384,usage:JSON.stringify(body.usage||{}),observed_at:$now.toISO()};})() }}'''
 # This raw Python template contains JavaScript regex escapes, not JSON escapes.
 expression=expression.replace('\\\\','\\').replace('HTTP_NODE',http_node).replace('PHASE',phase).replace('EVENT_EXPR',event_expression)
 builder.set(names['sanitize'],expression)
 builder.row(names['persist'],table,'upsert','response_key','={{ $json.response_key }}')
 builder.set(names['restore'],'={{ $("'+http_node+'").first().json }}')
 return names
