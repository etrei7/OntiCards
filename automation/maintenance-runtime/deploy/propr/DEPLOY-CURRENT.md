# 当前版本重建与恢复

本文对应policy13和独立日报alias；历史带固定revision、run_id或SHA的单次验收脚本只用于审阅，不应批量重放。持续CI与普通对话分别按`../n8n-preview-ci/README.md`和`../n8n/RUNBOOK-current.md`部署。

## 构建机上的源码与镜像

先准备ProPR官方仓库的干净checkout，核对上游`42931b1502eb03ac299f14e306811736fab51eb4`，在kol-stage2创建新的独立worktree。使用当前交付的`../propr-maintenance-policy13.patch`执行原生`git apply --check`及`git apply --index`，补丁SHA256必须为91c2d151fd95ff6fcd634fc73d553a6fcc84674f481b3a7ce7b48eb11ea0273b；`git write-tree`必须得到0af2178f1461819a893d6705a0e23dcad6330595。保留上游LICENSE/NOTICE。不要顺序应用policy8/9/10/11/12/13全量补丁。

已验证的 `../prepare-propr-policy13-source.py` 可从固定上游 Git 对象、完整补丁和 `propr-policy13-patch-validation.json` 重构新源码及验证标记，无旧policy私有tar依赖。具体映射：交付 deploy/propr-maintenance-policy13.patch 复制为 /opt/onticards-build/propr-policy13.patch；evidence/propr-policy13-patch-validation.json 放同一buildroot；官方上游Git对象位于 buildroot/propr-src；Dockerfile.propr-policy-tests 放buildroot。新目标 propr-policy13-src 必须不存在，不能复用旧目录或手工伪造验证标记。

官方`docker/Dockerfile.app.prod`构建API/worker/daemon同一镜像；交付的`../Dockerfile.propr-policy-tests`和`../build-propr-policy13.sh`记录本次完整构建、679既有分组、20只读/版本/权限边界及265相关回归，共964项无跳过的命令。原脚本固定源码目录`/opt/onticards-build/propr-policy13-src`并要求已验证标记`.onticards-source-verified.json`；在新目录先完成上述原生SHA/patch/tree核验，再生成包含upstream、patch_sha256、tree的标记，避免使用旧标记冒充新源码验证。构建新版本应换新tag，不能覆写本次已发布tag。镜像使用registry digest固定，见manifest。

UI兼容改动单独在上游propr-ui应用`../propr-ui-http-compat.patch`，沿用已有npm/静态构建。当前已验证UI镜像可直接按digest拉取，无需重建。Agent镜像沿用原生bundle，OpenCode1.18.31；测试机禁止自动补建缺失镜像，必须先由打包机提供。

## 5机上的配置与凭据

当前目录为`/opt/onticards-maintenance/propr`。备份SQLite、Redis和现有配置后，按manifest拉取已核digest；使用`compose.yaml`、`gitconfig`和实际Nginx配置。`runtime.env.example`不含秘密，安全默认max provider replacements为0，原生settings也须保持0。以下实际值只在服务器填写，文件0600并限制目录访问：

- `github.env`：`GH_AUTH_MODE=app`、`GH_APP_ID=5422414`、`GH_INSTALLATION_ID=174029282`、`GH_PRIVATE_KEY_PATH=/run/propr-secrets/github-app.pem`；PEM为已安装单仓App下载的私钥。
- `oauth.env`：GitHub App的`GH_OAUTH_CLIENT_ID`、`GH_OAUTH_CLIENT_SECRET`及`GH_OAUTH_CALLBACK_URL`；回调精确为`http://10.66.66.5:18123/api/auth/github/callback`。不能把token或private key粘进版本库。
- `runtime.env`中另外生成独立高熵`SESSION_SECRET`、`SYSTEM_TASK_SECRET`、`PROPR_CREDENTIAL_ENCRYPTION_KEY`；恢复旧加密数据必须保留原加密key，不能随意重生成。
- `/opt/onticards-maintenance/secrets/model.env`提供`LLM_BASE_URL`和`DASHSCOPE_API_KEY`给原有初始化；模型仍为qwen3.8-max-0902。现有服务恢复不要重跑`init_runtime.py`覆盖配置。

初次初始化复用`init_runtime.py`、`seed_config.mjs`的原生配置store；既有实例则在原生UI/配置服务中核对单仓、AI标签、并发1、每次600秒、3轮、max_provider_replacements0、INFRALOST禁止替代。已有init脚本是早期受控起点，不代表会完整重建数据库中的当前运行历史。不能为了复现而重置现有任务预算、删除历史或复制含秘密数据库进公开包。

## 日报独立配置

编码alias `onticards-qwen`保持原知识配置。新增原生alias `onticards-daily-qwen`使用同一镜像/provider/model，其configPath为`/opt/onticards-maintenance/propr/opencode/daily`。只放opencode.json（instructions为空）、供应商key文件、daily_input_contract.py及独立只读report-inputs bind；不复制instructions/AGENTS或历史会话。模型配置目录按上游需要可写，事实目录必须通过systemd bind,ro。

`deploy_daily_isolated_alias.py`和`configure_daily_isolated_alias.mjs`记录实际配置动作与无模型验证；该脚本绑定本次definition revision12→13，其他新实例应通过同一原生store/UI选择本实例definition，不伪造历史revision。保存后复用现成`agents_update`事件刷新registry。原生Schedule保持UTC `5 1 * * *`、dry_run、无仓库能力、无前次报告。真实debug config的instructions=[]与helper READY是配置验证，语义质量由报告审阅验证。

## 确定性采集器

仓库根目录的`automation/onticards`和`automation/tests`是当前采集器源码，`automation/deploy`为systemd安装模板；其他维护组件保留在`automation/maintenance-runtime`的`deploy/research/evidence`目录中。部署采集器至`/opt/onticards-maintenance/reporting`，使用现有venv、requirements锁文件与低权限用户。安装主unit/timers后还需`collector-app.conf`和`native-activity.conf`两个drop-in：前者LoadCredential给单仓只读App鉴权，后者以root ExecStartPre导出安全原生任务快照，低权限采集器不读ProPR数据库。`python -m pytest tests -q`在Linux37项通过。00:00快照、09:00采事实、09:05AI归纳三者不是重复发布。

启动/恢复先检查镜像和配置、运行`docker compose config --quiet`、确认无进行中任务及单仓授权，再用`docker compose up -d --no-build`。核对健康、Schedule、队列、两个n8n职责范围和后续自然执行。完整保留历史失败，禁止把本次测试结果当成新源码重新验证后的证据。

## 自动 review 的服务接线与首次基线

沿用[原生CI安装说明](../n8n-preview-ci/README.md#自动语义审查接线)，其 install_service.py 仅接受精确policy12或13作为TLS/SSH安装底座，activate_review_admission.py只接受上述policy13三服务全running；备份和既有Nginx门户必须保留。模板inactive/dry_run，正式启用须在最终PR30head进入完整intake之后先prepare再apply；固定版本baseline不调用SSH/模型，成功读回才写enabled回执，失败保持disabled/exit2。未来只读review不能触发写入型恢复，不添加AI编码标签，不扩execute/fix/merge scope。当前还没有本接线自动模型审查成功案例，不能用只读握手代替。
