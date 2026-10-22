import { test, expect } from '@playwright/test';
import fs from 'node:fs';

function credentials() {
  const filename = process.env.ONTICARDS_PREVIEW_CREDENTIALS;
  if (!filename) throw new Error('ONTICARDS_PREVIEW_CREDENTIALS must identify the private synthetic account file');
  return JSON.parse(fs.readFileSync(filename, 'utf8'));
}

test('公开登录页与健康检查，有成功截图和无凭据trace', async ({ page, context, request }, testInfo) => {
  await context.tracing.start({ screenshots: true, snapshots: true });
  const health = await request.get('/console/api/healthz');
  expect(health.status()).toBe(200);
  expect((await health.json()).status).toBe('ok');
  await page.goto('/zh-CN/login');
  await expect(page.getByPlaceholder('请输入用户名')).toBeVisible();
  await expect(page.getByPlaceholder('请输入密码')).toBeVisible();
  await expect(page.getByRole('button', {name: '登录', exact: true})).toBeEnabled();
  await testInfo.attach('login-success-path', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
  const trace = testInfo.outputPath('public-login-trace.zip');
  await context.tracing.stop({path: trace});
  await testInfo.attach('public-login-trace', {path: trace, contentType: 'application/zip'});
});

test('真实数据卡片、问数总额250与治理报告详情', async ({page}, testInfo) => {
  const account=credentials();
  const productEvidence=process.env.ONTICARDS_PRODUCT_EVIDENCE_DIR || '../evidence-product';
  const source=JSON.parse(fs.readFileSync(`${productEvidence}/extract-schema.json`,'utf8')).data.datasource_info.id;
  const report=JSON.parse(fs.readFileSync(`${productEvidence}/governance-execute.json`,'utf8')).data.report_id;
  await page.goto('/login');
  await page.getByPlaceholder('请输入用户名').fill(account.username);
  await page.getByPlaceholder('请输入密码').fill(account.password);
  await page.getByRole('button',{name:'登录',exact:true}).click();
  await expect(page).toHaveURL(/\/overview/);
  await page.goto(`/workspaces/${source}?tab=cards`);
  await expect(page.getByPlaceholder('搜索卡片名称/摘要...')).toBeVisible();
  await expect(page.getByText('maintenance_orders',{exact:true}).first()).toBeVisible();
  await testInfo.attach('generated-data-card',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
  await page.goto(`/workspaces/${source}?tab=ask`);
  await page.getByPlaceholder('选择数据源，输入您的自然语言问题，系统将自动生成 SQL 并执行聚合查询').fill('查询 maintenance_orders 表的所有订单 amount 总和，以 total_amount 为列名。');
  const queryResponse=page.waitForResponse(r=>r.url().endsWith('/query_by_datacards_agg')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'执行查询',exact:true}).click();
  const response=await queryResponse;
  expect(response.status()).toBe(200);
  expect((await response.json()).data.final_rows).toEqual([{total_amount:250}]);
  await expect(page.getByText('250',{exact:true}).first()).toBeVisible({timeout:30_000});
  await testInfo.attach('real-query-total-250',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
  await page.goto(`/governance/reports/${report}`);
  await page.getByText('全库表的空值检测详情（NULL、空字符串、缺失率）',{exact:true}).click();
  await expect(page.getByText('maintenance_orders',{exact:false}).first()).toBeVisible();
  await testInfo.attach('governance-real-report',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
});

test('合成管理员真实登录及管理页面', async ({ page }, testInfo) => {
  const account = credentials();
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.name + ': ' + error.message.slice(0, 500)));
  await page.goto('/zh-CN/login');
  await page.getByPlaceholder('请输入用户名').fill(account.username);
  await page.getByPlaceholder('请输入密码').fill(account.password);
  const loginResponse = page.waitForResponse(response => response.url().endsWith('/console/api/login') && response.request().method() === 'POST');
  await page.getByRole('button', {name: '登录', exact: true}).click();
  const login = await loginResponse;
  expect(login.status()).toBe(200);
  expect((await login.json()).code).toBe(200);
  await expect(page).toHaveURL(/\/(?:zh-CN\/)?overview/);
  await page.waitForLoadState('networkidle');
  await testInfo.attach('overview-after-login', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});

  // Reuse the application's raw-JWT convention, keep token only in memory.
  const token = await page.evaluate(() => localStorage.getItem('console_token'));
  expect(token).toBeTruthy();
  const profile = await page.request.get('/console/api/user', {headers: {Authorization: token!}});
  expect(profile.status()).toBe(200);
  expect((await profile.json()).data.role).toBe('admin');

  await page.goto('/zh-CN/workspaces');
  await expect(page.getByText('管理您的数据源与连接', {exact: true})).toBeVisible();
  await testInfo.attach('workspaces-success-path', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});

  for (const [route, name] of [
    ['/query-history', 'query-history'],
    ['/governance', 'governance'],
    ['/governance/reports', 'governance-reports'],
  ]) {
    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await expect(page).toHaveURL(new RegExp(route.replaceAll('/', '\\/')));
    await expect(page.getByRole('heading').first()).toBeVisible();
    await page.waitForLoadState('networkidle');
    await testInfo.attach(name, {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
  }
  await testInfo.attach('page-errors', {body: JSON.stringify(failures, null, 2), contentType: 'application/json'});
  expect(failures).toEqual([]);
});
