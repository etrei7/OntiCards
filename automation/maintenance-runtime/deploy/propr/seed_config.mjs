// Deployment-only configuration through ProPR's existing stores; no agent or scheduler loop.
import { randomUUID } from 'node:crypto';
import { writeFile, readFile } from 'node:fs/promises';
import { runMigrations, closeConnection, db } from './packages/core/dist/db/connection.js';
import { saveAgents, loadAgents, saveAgentTankSettings } from './packages/core/dist/config/configManagerAgents.js';
import { getConfig, saveConfig } from './packages/core/dist/config/configStore.js';
import { createAgentDefinition, listAgentDefinitions, updateAgentDefinition } from './packages/core/dist/services/agents/agentDefinitionStore.js';
import { computeContentHash, generateAgentBundleImageTag, getDefaultAgentCliVersionMatrix } from './packages/core/dist/agents/version/versionService.js';

const repository = 'stepll2026/OntiCards';
const ownerId = '318866723';
const model = 'opencode-bailian/qwen3.8-max-0902';
const alias = 'onticards-qwen';
const enableRepository = process.argv.includes('--enable-repository');
await runMigrations();
const existingAgents = await loadAgents();
const existingMaintenanceAgent = existingAgents.find(a => a.alias === alias);
const bundle = generateAgentBundleImageTag(getDefaultAgentCliVersionMatrix(), computeContentHash());
await saveAgents([{
  id: existingMaintenanceAgent?.id ?? randomUUID(), type: 'opencode', alias, enabled: true,
  dockerImage: bundle, configPath: '/opt/onticards-maintenance/propr/opencode',
  supportedModels: [model], defaultModel: model, modelCustomLabels: { [model]: 'llm-qwen3-8-max' },
  cliVersionType: 'default', cliVersionResolved: '1.18.31',
  envVars: { ...existingMaintenanceAgent?.envVars, OPENCODE_DISABLE_MODELS_FETCH: '1' },
}]);
const previousRepos = await getConfig('repos_to_monitor', []);
await saveConfig('repos_to_monitor', [{
  id: previousRepos.find(r => r.name === repository)?.id ?? randomUUID(), name: repository,
  enabled: enableRepository, contextRepositories: 'none',
  autoFollowupOnFailedCi: false, cancelCiDuringFollowup: false,
  autoResolveMergeConflicts: true, autoAssignPullRequests: false,
  visualPreview: { enabled: false, types: ['image'] },
}]);
await saveConfig('settings', { ...await getConfig('settings', {}), default_agent_alias: alias, worker_concurrency: 1,
  analysis_model_fast: model, planner_context_model: model, planner_generation_model: model });
for (const [key, value] of Object.entries({
  primary_processing_labels: ['AI'], ai_primary_tag: 'AI', pr_label: 'AI',
  pr_review_model: model, ultrafix_max_cycles: 3, ultrafix_pause_seconds: 60,
  ultrafix_ci_wait_timeout_ms: 1800000, auto_resolve_merge_conflicts: true,
  // Native USD prices do not cover this private Bailian endpoint. Do not present unknown cost as zero spent.
  default_max_cost_usd: 0,
})) await saveConfig(key, value);
await saveAgentTankSettings({ mode: 'disabled' });
// This known account is already the instance bootstrap administrator; persist its exact GitHub ID for schedule ownership.
await db('instance_members').insert({ github_user_id: ownerId, github_username: 'stepll2026', role: 'admin', source: 'local' })
  .onConflict('github_user_id').ignore();
const definitions = await listAgentDefinitions(ownerId);
const dailyPrompt = await readFile('/usr/src/app/data/daily-prompt.txt', 'utf8');
let daily = definitions.definitions.find(d => d.name === 'OntiCards 中文维护日报');
if (!daily) daily = await createAgentDefinition({
  ownerId, name: 'OntiCards 中文维护日报',
  description: '读取已有确定性日报事实，生成中文维护者待办；只保存 ProPR 报告，不发消息、不写 GitHub。',
  prompt: dailyPrompt,
  repositories: [], capabilities: [], autonomyMode: 'dry_run',
  agentAlias: alias, modelName: model,
  scheduleCron: '5 1 * * *', scheduleEnabled: false,
  includePreviousReports: true, previousReportsLimit: 1, enabled: true,
});
else daily = await updateAgentDefinition(daily.id, ownerId, { prompt: dailyPrompt, modelName: model });
await writeFile('/usr/src/app/data/deployment-config.json', JSON.stringify({
  repository, repositoryEnabled: enableRepository, bundle, model, agentAlias: alias,
  dailyDefinitionId: daily.id, dailyScheduleUtc: '5 1 * * *', dailyScheduleEnabled: daily.scheduleEnabled,
  limits: { steps: 24, timeoutSeconds: 600, workerConcurrency: 1, ultrafixMaxCycles: 3 },
  costAccounting: 'Bailian provider billing; native USD price unknown, no claimed USD cap',
}, null, 2));
console.log(JSON.stringify({ configured: true, repositoryEnabled: enableRepository, bundle, dailyDefinitionId: daily.id }));
await closeConnection();
process.exit(0);
