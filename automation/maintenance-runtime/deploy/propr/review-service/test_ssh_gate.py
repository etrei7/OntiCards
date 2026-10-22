import json,subprocess,unittest
from unittest.mock import patch
import ssh_gate

class GateTests(unittest.TestCase):
    def test_top_level_cleanup_failure_cannot_claim_no_invocation(self):
        with patch.object(ssh_gate,'main',side_effect=OSError('lock cleanup failed after invoke')):
            out=ssh_gate.safe_main()
            self.assertIsNone(out['model_started']);self.assertFalse(out['automatic_retry'])
            self.assertEqual(out['grant_revocation'],'unknown')
    def test_pre_invocation_invalid_is_no_model(self):
        with patch.object(ssh_gate,'bounded_input',side_effect=ValueError()),patch.object(subprocess,'run') as run:
            self.assertEqual(ssh_gate.main(),{'state':'invalid_request','model_started':False})
            run.assert_not_called()
    def test_unknown_native_outputs_never_claim_no_model(self):
        for text in ['','ONTICARDS_REVIEW_RESULT:{bad','ONTICARDS_REVIEW_RESULT:[]',
                     'ONTICARDS_REVIEW_RESULT:{"state":"native_posted","secret":"must never leave"}',
                     'ONTICARDS_REVIEW_RESULT:{"state":"native_posted"}\nONTICARDS_REVIEW_RESULT:{}']:
            with self.subTest(text=text),patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,text,'')):
                out=ssh_gate.invoke({})
                self.assertEqual(out['state'],'invocation_outcome_unknown')
                self.assertIsNone(out['model_started']);self.assertFalse(out['automatic_retry'])
                self.assertEqual(out['grant_revocation'],'unknown');self.assertNotIn('secret',json.dumps(out))
    def test_timeout_after_attempt_is_unknown(self):
        with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired('fixed',225)):
            self.assertIsNone(ssh_gate.invoke({})['model_started'])
    def test_process_failure_with_valid_json_is_unknown(self):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],1,'ONTICARDS_REVIEW_RESULT:{"state":"posted"}','')):
            self.assertEqual(ssh_gate.invoke({})['state'],'invocation_outcome_unknown')
    def test_safe_fixed_argv_ignores_original_shell(self):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,'ONTICARDS_REVIEW_RESULT:{"state":"native_posted","model_started":null}','')) as run:
            self.assertEqual(ssh_gate.invoke({})['state'],'native_posted')
            self.assertIsInstance(run.call_args.args[0],list)
            self.assertEqual(run.call_args.kwargs['env'],{'PATH':'/usr/bin:/bin','HOME':'/root'})
            self.assertNotIn('shell',run.call_args.kwargs)
if __name__=='__main__':unittest.main()
