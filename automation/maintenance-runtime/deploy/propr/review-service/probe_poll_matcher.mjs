// Native matcher/policy only; does not enqueue a job, publish or execute review.
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
const require=createRequire('/usr/src/app/package.json');
const core=await import(require.resolve('@propr/core'));
const body='/review onticards-qwen:opencode-bailian/qwen3.8-max-0902\n\n由 OntiCards AI 维护流程自动触发。';
try {
  const author=core.filterCommentByAuthor('stepll2026','User');
  const trigger=core.checkCommentTrigger(body);
  const hasLabel=await core.hasValidTriggerLabel([]);
  const command=core.parseSlashCommand(body);
  const gate=await core.createFollowupGateEvaluator({repoOwner:'stepll2026',repoName:'OntiCards',pullRequestNumber:26});
  const decision=await gate.decide({authorId:318866723,authorLogin:'stepll2026',systemAuthored:false});
  const result={at:new Date().toISOString(),no_ai_label:hasLabel===false,author_allowed:!author.shouldFilter,trigger_matched:trigger.isTriggered,
    native_command:command?.command,model_argument:command?.args?.[0],assignment_allowed:decision.allowed,assignment_reason:decision.reason,
    polling_eligible:!author.shouldFilter&&(hasLabel||trigger.isTriggered)&&decision.allowed,worker_validation_proven:false,
    worker_gap:'policy12 still requires processing label; policy13 worker-specific fixture required',queued_jobs:0,model_calls:0,github_writes:0};
  assert(result.no_ai_label&&result.polling_eligible&&result.native_command==='review');
  console.log('ONTICARDS_POLL_PROBE:'+JSON.stringify(result));
}catch(error){process.exitCode=1;console.error('Native poll matcher assertion failed');}finally{await core.db.destroy();process.exit(process.exitCode||0);}
