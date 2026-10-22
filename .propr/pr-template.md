## title
[AI维护] {{issue_title}} (#{{issue_number}})

## summary
关联 #{{issue_number}}。这是 AI 自动维护产生的变更，最终合并由维护者操作。

{{summary}}

## run
### 运行记录

仓库：`{{repository}}`；分支：`{{branch}}`；会话：`{{session_id}}`。

执行器：{{agent}} / {{model}}；耗时：{{execution_time}}；工具可取得的 token 总量：{{tokens}}。

本实例使用已有百炼模型入口，实际金额以供应商账单为准，未取得的金额标为未知。运行完成不等于构建、部署、API 或浏览器验证通过；各项结果须附当前提交对应的真实证据。

## commits
### 提交

{{commits}}

## files_changed
### 修改范围

{{files_changed}}

## review_guidelines
### 维护者审阅

- 核对具体问题、复现结果、现成能力复用和必要新增范围。
- 核对报告中的 head、base、镜像 digest 与本次 PR 当前版本；版本变化后旧报告不能作为通过依据。
- 查看独立复核、实际测试命令、失败或未执行项及截图和报告链接。
- 在 GitHub 人工决定最终合并；AI 不批准或合并此 PR。

## trailer
由 ProPR 原生发布流程创建；未经过实际验证的内容不得标为通过。
