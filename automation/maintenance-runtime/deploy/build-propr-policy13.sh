#!/usr/bin/env bash
set -euo pipefail
ROOT=/opt/onticards-build
SOURCE=$ROOT/propr-policy13-src
EVIDENCE=$ROOT/evidence/policy13
IMAGE=registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy13
TEST_IMAGE=onticards-propr-policy13-tests
mkdir -p "$EVIDENCE"
test -f "$SOURCE/.onticards-source-verified.json"
date -u +%FT%TZ > "$EVIDENCE/build-started-at.txt"
cp "$SOURCE/.onticards-source-verified.json" "$EVIDENCE/source-verified.json"
docker build --progress plain -f "$ROOT/Dockerfile.propr-policy-tests" \
  --build-arg GIT_SHA=42931b1502eb03ac299f14e306811736fab51eb4 \
  -t "$TEST_IMAGE" "$SOURCE" > "$EVIDENCE/build-tests.log" 2>&1
docker run --rm --network none -e NODE_ENV=test -e LOG_LEVEL=error "$TEST_IMAGE" \
  node --import tsx --experimental-test-module-mocks --test \
  test/nativeGitPreparation.test.ts packages/core/test/dockerAbortController.test.ts \
  test/gitHooksDisabled.test.ts test/taskSubmissionLifecycle.test.ts test/workflowPreviewPublication.test.ts \
  test/maintenancePublication.test.ts test/prTemplateDescription.test.ts packages/core/test/prTemplate.test.ts \
  test/processAgentRunJob.test.ts test/agentReportPrompt.test.ts \
  test/indexingPinnedRevision.test.ts test/indexingFreshFetch.test.ts test/summaryFileFilter.test.ts \
  test/summaryMinerBatchFallback.test.ts test/indexingRouteHelpers.test.ts test/configRoutes.followup.test.ts \
  packages/api/test/configRoutesIndexingSummarization.test.ts \
  packages/core/test/conflictResolution.test.ts test/processMergeConflictJob.test.ts \
  test/mergeConflictHelpers.test.ts test/mergeConflictDetector.test.ts \
  test/indexingPreparationDeadline.test.ts \
  test/indexingRunBudget.test.ts test/indexingDeadlineProcess.test.ts test/analysisGitAccess.test.ts \
  test/opencodeAgent.test.ts packages/core/test/dockerExecutionOwnership.test.ts \
  > "$EVIDENCE/regression-tests.log" 2>&1
tail -9 "$EVIDENCE/regression-tests.log"
REDIS_FIXTURE=onticards-policy13-build-redis
trap 'docker rm -f "$REDIS_FIXTURE" >/dev/null 2>&1 || true' EXIT
docker run -d --name "$REDIS_FIXTURE" --network none redis:7-alpine redis-server --save "" --appendonly no > "$EVIDENCE/redis-fixture-id.txt"
docker run --rm --network "container:$REDIS_FIXTURE" -e NODE_ENV=test -e LOG_LEVEL=error -e REDIS_HOST=127.0.0.1 "$TEST_IMAGE" \
  node --import tsx --experimental-test-module-mocks --test test/indexingQueueBudgetIntegration.test.ts \
  > "$EVIDENCE/redis-integration-tests.log" 2>&1
tail -9 "$EVIDENCE/redis-integration-tests.log"
# Run native admission in its own process: its deliberately flushed Redis fixture must not overlap another suite.
docker run --rm --network "container:$REDIS_FIXTURE" -e NODE_ENV=test -e LOG_LEVEL=error -e REDIS_HOST=127.0.0.1 -e REDIS_PORT=6379 "$TEST_IMAGE" \
  node --import tsx --experimental-test-module-mocks --test test/maintenanceLabelAdmission.test.ts \
  > "$EVIDENCE/label-admission-tests.log" 2>&1
tail -9 "$EVIDENCE/label-admission-tests.log"
docker run --rm --network "container:$REDIS_FIXTURE" -e NODE_ENV=test -e LOG_LEVEL=error -e REDIS_HOST=127.0.0.1 -e REDIS_PORT=6379 -e PROPR_REQUIRE_REDIS_INTEGRATION=1 "$TEST_IMAGE" \
  node --import tsx --experimental-test-module-mocks --test \
  test/maintenancePureLabelFailure.test.ts packages/core/test/instanceStorage.test.ts \
  test/issueJobDispatcher.test.ts test/issueJobDispatcher.handleDispatch.test.ts test/issueUsageLimitRetry.test.ts \
  test/errorHandler.test.ts test/providerReplacementOrigin.test.ts packages/core/test/taskSubmissionService.test.ts \
  packages/core/test/taskSubmissionIntakeQueue.test.ts packages/core/test/taskSubmissionIntake.test.ts packages/core/test/issueRetryRunReceipt.test.ts \
  > "$EVIDENCE/label-admission-regression-tests.log" 2>&1
tail -9 "$EVIDENCE/label-admission-regression-tests.log"
docker run --rm --network "container:$REDIS_FIXTURE" -e NODE_ENV=test -e LOG_LEVEL=error -e REDIS_HOST=127.0.0.1 "$TEST_IMAGE" \
  node --import tsx --experimental-test-module-mocks --test test/maintenanceReadOnlyReview.test.ts \
  > "$EVIDENCE/readonly-integration-tests.log" 2>&1
tail -9 "$EVIDENCE/readonly-integration-tests.log"

docker run --rm --network none -e NODE_ENV=test -e LOG_LEVEL=error "$TEST_IMAGE" \
  node --import tsx --experimental-test-module-mocks --test --test-concurrency=1 \
  test/prReviewValidation.test.ts test/prReviewRunnerBudget.test.ts test/reviewContextHelpers.test.ts \
  test/prCommentReviewFollowupScope.test.ts test/prCommentReviewCancellation.test.ts \
  test/prCommentAutomaticRetry.test.ts test/prCommentCleanupOrder.test.ts test/prCommentCollisionRecovery.test.ts \
  test/prCommentTaskStateFinalizers.test.ts test/prCommentUsageLimitResume.test.ts \
  test/followupHandoffAdoptionFence.test.ts test/followupHandoffCancelledClaims.test.ts \
  test/followupHandoffRecovery.test.ts test/followupHandoffOperatorSerialization.test.ts \
  test/followupHandoffSettlement.test.ts test/followupHandoffUsageLimitOwnership.test.ts \
  test/prContinuation.test.ts test/reviewCommentFormatter.test.ts test/reviewResultMetrics.test.ts \
  test/reviewScorePersistence.test.ts \
  packages/api/test/mcpOAuth.test.ts packages/api/test/mcpOperations.test.ts packages/api/test/agentRunGrants.test.ts \
  > "$EVIDENCE/review-boundary-regression-tests.log" 2>&1
tail -9 "$EVIDENCE/review-boundary-regression-tests.log"


docker rm -f "$REDIS_FIXTURE" >/dev/null
trap - EXIT
docker build --progress plain -f "$SOURCE/docker/Dockerfile.app.prod" \
  --build-arg GIT_SHA=42931b1502eb03ac299f14e306811736fab51eb4 \
  -t "$IMAGE" "$SOURCE" > "$EVIDENCE/build-production.log" 2>&1
docker push "$IMAGE" > "$EVIDENCE/push.log" 2>&1
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}' > "$EVIDENCE/repo-digests.json"
docker image inspect "$IMAGE" --format '{{.Id}}' > "$EVIDENCE/image-id.txt"
date -u +%FT%TZ > "$EVIDENCE/build-completed-at.txt"
printf 'policy13 compilation, regression and registry publication completed\n'
