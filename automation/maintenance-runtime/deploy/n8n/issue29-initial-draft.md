【AI辅助｜维护验收咨询】

基线 [c8e] 的 PDF 导出依赖本地 soffice 将 HTML 转为 PDF，但 Dockerfile 未安装 libreoffice-writer；候选 [3105] 已改为先用 python-docx 生成 DOCX 再转 PDF 并在 Dockerfile 中补充了该依赖。历史镜像是否包含这些修复未知，需人类补充部署方式和实际 API 镜像标识后才能继续核实。

下一步：请在本 Issue 补充当时的部署方式（如容器、裸机等）以及实际运行的 API 镜像名称或不可变 ID，以便使用只读检查确认运行环境中的 soffice 状态。

最少只读检查（确认部署方式后，在对应API运行环境内查询，不在本流程执行）：`command -v soffice`；`soffice --version`。

版本来源：[baseline_pdf_path](https://github.com/stepll2026/OntiCards/blob/c8e3dfee68d398a37842fc332f73af40a56f02a7/OntiCards_Api/controllers/governance/libreoffice_exporter.py#L884)、[baseline_dependency](https://github.com/stepll2026/OntiCards/blob/c8e3dfee68d398a37842fc332f73af40a56f02a7/OntiCards_Api/Dockerfile#L38)、[candidate_pdf_path](https://github.com/stepll2026/OntiCards/blob/3105b7b61469c6b2945357f2eefa8fcb2e3aaee5/OntiCards_Api/controllers/governance/libreoffice_exporter.py#L991)、[candidate_dependency](https://github.com/stepll2026/OntiCards/blob/3105b7b61469c6b2945357f2eefa8fcb2e3aaee5/OntiCards_Api/Dockerfile#L61)。

本条为受控测试咨询，不启动修复、构建或部署，不合并或关闭Issue。最终合并由维护者操作。
<!-- onticards-triage:issue29-one-model-v1 -->
