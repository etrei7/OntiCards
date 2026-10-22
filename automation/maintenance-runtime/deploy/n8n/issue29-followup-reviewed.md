【AI辅助｜维护验收咨询】

我是OntiCards维护者授权的AI咨询助手，基于人类补充的Docker Compose部署方式、历史API镜像标识及源码记录继续说明。历史8abe与参考基线c8e的libreoffice_exporter.py仅该文件blob相同，不推断整个仓库一致。基线导出PDF时先生成HTML再尝试调用本地soffice转换；若soffice未找到或转换异常均进入同一兜底报错，因此现有错误文本和HTML到soffice路径不能单独证明容器内缺少程序，源码中DOCX/XLSX有纯Python降级，PDF没有；这些格式正常不证明soffice曾成功执行。候选3105（关联Draft PR #26）复用既有python-docx生成DOCX再转PDF，并在Dockerfile补充libreoffice-writer依赖，未新建报告生成器。独立预览测试覆盖了LibreOffice回归、API、Playwright及部分迁移用例，但这些是候选自身的验证范围，不是本Issue执行的测试，不能据此声称历史镜像已修复，也不代表全部环境或并发导出场景均已覆盖。审阅补充（关联 PR #26）：3105 的真实并发两份导出探针出现 1 成功、1 失败；诊断时仅加入 LibreOffice 官方独立 profile 参数后为 2/2 成功，但应用源码尚未修改，不能称并发问题已修复。

下一步：待维护者决定是否复用PR #26候选方案，并界定其运行边界，例如在目标环境中确认soffice实际可用性与字体支持是否满足真实治理报告需求。本次仍为只读咨询，不发出安装、构建、部署、修改、合并或关闭指令，不发起修复。

版本来源：[baseline_pdf_path](https://github.com/stepll2026/OntiCards/blob/c8e3dfee68d398a37842fc332f73af40a56f02a7/OntiCards_Api/controllers/governance/libreoffice_exporter.py#L884)、[baseline_dependency](https://github.com/stepll2026/OntiCards/blob/c8e3dfee68d398a37842fc332f73af40a56f02a7/OntiCards_Api/Dockerfile#L38)、[candidate_pdf_path](https://github.com/stepll2026/OntiCards/blob/3105b7b61469c6b2945357f2eefa8fcb2e3aaee5/OntiCards_Api/controllers/governance/libreoffice_exporter.py#L991)、[candidate_dependency](https://github.com/stepll2026/OntiCards/blob/3105b7b61469c6b2945357f2eefa8fcb2e3aaee5/OntiCards_Api/Dockerfile#L61)、[historical_exporter_identity](https://github.com/stepll2026/OntiCards/blob/8abe9e20d58df2605b8a66c3a4296d3dcfe325a2/OntiCards_Api/controllers/governance/libreoffice_exporter.py#L884)、[candidate_verification_scope](https://github.com/stepll2026/OntiCards/pull/26)。

本条为受控测试咨询，不启动修复、构建或部署，不合并或关闭Issue。最终合并由维护者操作。
<!-- onticards-triage:issue29-followup-one-model-v1 -->
