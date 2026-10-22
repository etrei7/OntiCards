// Pure upstream cron/prompt calls: no scheduler, queue, model, or DB mutations.
import { writeFile } from 'node:fs/promises';
import { nextCronOccurrence } from '@propr/shared';
import { buildAgentReportPrompt } from './dist/src/jobs/agentRuns/reportPrompt.js';
const cases = [
  ['2026-10-22T01:04:59Z', '2026-10-22T01:05:00.000Z'],
  ['2026-10-22T01:05:00Z', '2026-10-23T01:05:00.000Z'],
  ['2026-10-31T01:05:00Z', '2026-11-01T01:05:00.000Z'],
  ['2026-12-31T01:05:00Z', '2027-01-01T01:05:00.000Z'],
  ['2024-02-28T01:05:00Z', '2024-02-29T01:05:00.000Z'],
  ['2024-02-29T01:05:00Z', '2024-03-01T01:05:00.000Z'],
];
const checks = cases.map(([from, expected]) => {
  const next = nextCronOccurrence('5 1 * * *', new Date(from));
  const shanghaiTime = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit', hour12: false }).format(next);
  return { from, expected, actual: next.toISOString(), shanghaiTime, passed: next.toISOString() === expected && shanghaiTime === '09:05' };
});
const run = { id: 'synthetic-calendar-check', trigger: 'schedule', triggerSource: 'schedule:5 1 * * *', createdAt: Date.parse('2027-01-01T01:05:00Z') };
const prompt = buildAgentReportPrompt({
  definition: { name: 'Local calendar fixture', prompt: 'Read the native Task timestamp.', repositories: [], capabilities: [], includePreviousReports: false },
  run, previousReports: [], attachments: [], workspace: { repositoriesReadable: false, primaryRepository: '', contextRepositories: [] },
});
checks.push({ check: 'native Task contains the real UTC createdAt and separate Run ID', passed: prompt.includes('Run: synthetic-calendar-check, triggered by schedule (schedule:5 1 * * *) at 2027-01-01T01:05:00.000Z.') });
const result = { passed: checks.every(x => x.passed), checks, modelCalls: 0, triggeredRuns: 0, schedulerEnabled: false, nativePrompt: prompt };
await writeFile('/usr/src/app/data/daily-native-schedule-validation.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify({ passed: result.passed, checks: checks.length }));
process.exit(result.passed ? 0 : 1);
