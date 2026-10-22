import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { simpleGit } from 'simple-git';
import { performConflictResolution } from '../packages/core/src/git/conflictResolution.js';

test('real clean Git merge can still contain a semantic API conflict; exact verification detects it without changing main', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'semantic-conflict-'));
  const remote = path.join(root, 'remote.git');
  const work = path.join(root, 'work');
  const previous = process.env.ONTICARDS_MAINTENANCE_MODE;
  const runClient = (filename: string) => spawnSync(process.execPath, [filename], { cwd: work, encoding: 'utf8' });
  try {
    const bare = simpleGit(root); await bare.init(true, ['--initial-branch=main', remote]);
    await simpleGit(root).clone(remote, work); const git = simpleGit(work);
    await git.addConfig('user.name', 'Synthetic fixture author'); await git.addConfig('user.email', 'fixture@example.test');
    await writeFile(path.join(work, 'lib.mjs'), 'export const run = () => 7;\n');
    await writeFile(path.join(work, 'old-client.mjs'), 'import { run } from "./lib.mjs"; if(run()!==7)process.exit(1);\n');
    await git.add('.'); await git.commit('initial API'); await git.push('origin', 'main');
    await git.checkoutLocalBranch('codex/semantic');
    await writeFile(path.join(work, 'lib.mjs'), 'export const execute = () => 7;\n');
    await writeFile(path.join(work, 'old-client.mjs'), 'import { execute } from "./lib.mjs"; if(execute()!==7)process.exit(1);\n');
    await git.add('.'); await git.commit('rename API and its existing caller'); await git.push('origin', 'codex/semantic');
    assert.equal(runClient('old-client.mjs').status, 0);
    const prHead = (await git.revparse(['HEAD'])).trim();
    await git.checkout('main');
    await writeFile(path.join(work, 'new-client.mjs'), 'import { run } from "./lib.mjs"; if(run()!==7)process.exit(1);\n');
    await git.add('.'); await git.commit('independent new caller'); await git.push('origin', 'main');
    assert.equal(runClient('new-client.mjs').status, 0);
    const baseHead = (await git.revparse(['HEAD'])).trim(); await git.checkout('codex/semantic');
    process.env.ONTICARDS_MAINTENANCE_MODE = '1'; let resolverCalls = 0;
    const outcome = await performConflictResolution({ worktreePath: work, baseBranch: 'main', branchName: 'codex/semantic', expectedHeadSha: prHead,
      commitMessage: 'local fixture merge', resolveConflicts: async () => { resolverCalls++; } });
    assert.equal(outcome.status, 'clean'); assert.equal(resolverCalls, 0);
    const result = runClient('new-client.mjs');
    assert.notEqual(result.status, 0); assert.match(result.stderr, /does not provide an export named 'run'/);
    assert.equal((await simpleGit(remote).revparse(['refs/heads/main'])).trim(), baseHead);
    console.log('SEMANTIC_BOUNDARY=' + JSON.stringify({ git_merge: 'clean', verification: 'failed', external_writes: 0,
      model_calls: 0, resolver_calls: resolverCalls, main_unchanged: true, remaining_action: 'human review or existing CI checks; clean Git is not semantic proof' }));
  } finally {
    if (previous === undefined) delete process.env.ONTICARDS_MAINTENANCE_MODE; else process.env.ONTICARDS_MAINTENANCE_MODE = previous;
    await rm(root, { recursive: true, force: true });
  }
});
