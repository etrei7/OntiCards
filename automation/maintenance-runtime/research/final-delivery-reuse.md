# 最终交付封装复用说明

2026-10-23。复用本轮已经实际验证的 Python 标准库 zipfile/hashlib、Gitleaks 8.30.1、Git 原生对象读取，以及现有 Nginx 只读报告目录。官方来源为 https://docs.python.org/3/library/zipfile.html 、https://github.com/gitleaks/gitleaks 和 https://nginx.org/en/docs/http/ngx_http_core_module.html 。此次不重新选型或创建网站/认证/产物服务。

现有 `deploy/n8n-preview-ci/package_pr26_evidence.py` 与 `publish_static_pr26_evidence.py` 已证明：显式白名单、逐文件哈希、归档路径检查、Nginx 配置原位修改及语法验证、HTTP 全文件回读和 POST 拒绝可用于本环境。

剩余缺口仅为把三个组件的审阅白名单、确切 PR30 提交、已有公开业务测试产物和日报修正版组合为一次可下载的交付快照。新增脚本只做这个项目的清单映射、文本索引和已有发布器的参数冻结，不实现通用产物管理平台，不收集整个工作区。配置密钥、PEM、数据库、私有环境文件、原始运行转录、HAR/trace 不纳入。

验证方法：源文件必须匹配三份白名单及 Git 提交对象；已公开测试文件必须匹配原发布回执；Gitleaks 无配置排除执行全扫描，保留原始退出码与发现数；只有逐文件完整SHA、路径、rule、行列范围均匹配且已独立复核的非秘密可分类为误报，未复核发现必须为零；ZIP 成员与最终 manifest 完全一致；复用 Nginx 的原位配置及只读 HTTP 回读逐文件验证，原有入口保留。

交付同时保留三份组件源清单，便于核对映射与原始文件哈希。最终 PR30 发布后的自动评审激活回执作为运行证据附入下载包，不回写同一源码提交，避免提交 SHA 自引用。封装工具依赖 Git/Python/Gitleaks 及已有验证产物，不能把封装验证等同于维护者全新安装验收。

最终全量封装第一次扫描命中30项generic-api-key：包含事件去重标识、公开源码摘要和测试字段，未直接放行。2026-10-23补查[Gitleaks原生配置与gitleaksignore](https://github.com/gitleaks/gitleaks#4-gitleaksignore)：原生fingerprint忽略不绑定整个文件字节。为保留原始发现并阻止同位置新值被误放行，新增review_secret_findings.py仅分类其原生JSON结果，使用独立逐项复核表和完整文件SHA；不替代扫描器、不修改历史证据、不添加全目录或全规则豁免。原始失败及分类回执随包保留。
