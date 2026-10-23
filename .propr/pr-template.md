## title
[AI维护] {{issue_title}} (#{{issue_number}})

## summary
关联 #{{issue_number}}。这是AI自动维护产生的变更；合并方式由后台保存的仓库设置决定，本PR文本不授予合并权限。

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
- 核对后台当前合并模式：OFF只给建议和证据；ON也必须重新满足当前版本测试、独立审查与仓库规则，才能由受信入口自动合并。

## trailer
由 ProPR 原生发布流程创建；未经过实际验证的内容不得标为通过。
