import { defineConfig } from '@playwright/test';

const evidence = process.env.ONTICARDS_EVIDENCE_DIR || '../evidence-browser';

export default defineConfig({
  testDir: './tests',
  workers: 1,
  retries: 0,
  timeout: 90_000,
  expect: {timeout: 15_000},
  reporter: [
    ['list'],
    ['html', {outputFolder: `${evidence}/html`, open: 'never'}],
    ['json', {outputFile: `${evidence}/results.json`}],
    ['junit', {outputFile: `${evidence}/results.xml`}],
  ],
  outputDir: `${evidence}/test-results`,
  metadata: {
    repository: 'stepll2026/OntiCards',
    task_id: process.env.ONTICARDS_TASK_ID || 'rootless-preview-candidate',
    run_id: process.env.ONTICARDS_RUN_ID || 'baseline-8abe9e20',
    tested_head_sha: process.env.ONTICARDS_TESTED_HEAD_SHA || '8abe9e20d58df2605b8a66c3a4296d3dcfe325a2',
    web_head_sha: process.env.ONTICARDS_WEB_HEAD_SHA || '8abe9e20d58df2605b8a66c3a4296d3dcfe325a2',
    tested_base_sha: process.env.ONTICARDS_TESTED_BASE_SHA || '8abe9e20d58df2605b8a66c3a4296d3dcfe325a2',
    environment: process.env.ONTICARDS_PREVIEW_URL || 'http://10.66.66.5:18110',
  },
  use: {
    // This sandbox remains enabled for PR pages; failure must not fall back to --no-sandbox.
    launchOptions: {chromiumSandbox: true},
    baseURL: process.env.ONTICARDS_PREVIEW_URL || 'http://10.66.66.5:18110',
    browserName: 'chromium',
    viewport: {width: 1440, height: 1000},
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',
    screenshot: 'only-on-failure',
    // Login requests contain credentials; capture sanitized screenshots and logs,
    // not a trace with raw authentication headers or request bodies.
    trace: 'off',
    video: 'off',
  },
});
