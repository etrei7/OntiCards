#!/bin/sh
set -eu
root=/opt/onticards-build/propr-daily-contract
mkdir -p "$root"
tar -xf /opt/onticards-build/daily-contract-sources.tar -C "$root"
docker run --rm --network none -e NODE_ENV=test -e LOG_LEVEL=error -v "$root/test/processAgentRunJob.test.ts:/build/test/processAgentRunJob.test.ts:ro" onticards-propr-policy7-tests sh -c 'node --import tsx --experimental-test-module-mocks --test --test-name-pattern="daily failure|configured daily|other definitions" test/processAgentRunJob.test.ts' > "$root/baseline-red-v2.log" 2>&1 || baseline=$?
test "${baseline:-0}" -ne 0
set --
for f in src/jobs/processAgentRunJob.ts src/jobs/agentRuns/dailyReportContract.ts test/processAgentRunJob.test.ts; do
 set -- "$@" -v "$root/$f:/build/$f:ro"
done
docker run --rm --network none -e NODE_ENV=test -e LOG_LEVEL=error "$@" onticards-propr-policy7-tests sh -c 'npm run build --workspace=packages/core && npm run build && node --import tsx --experimental-test-module-mocks --test test/processAgentRunJob.test.ts test/agentReportPrompt.test.ts' > "$root/candidate-v2.log" 2>&1
tail -n 12 "$root/candidate-v2.log"
