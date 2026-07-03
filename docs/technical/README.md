# 技术文档目录约定

本目录用于保存每一轮阶段性实现后的开发者技术文档。后续每完成一轮实现，都在本目录新增一份阶段文档，文件名建议使用：

```text
phase-N-<topic>-technical-doc.md
```

每份阶段文档至少覆盖：

- 本轮目标与交付范围
- 关键目录和模块职责
- 核心数据模型与接口契约
- 主流程调用链
- 关键规则、算法或策略
- 日志、审计、安全边界
- 测试覆盖与验证命令
- 已知限制和下一阶段扩展点

当前文档：

- [后端 Agent 第一版总技术文档](./first-version-backend-agent-technical-doc.md)
- [第一阶段 MVP 技术文档](./phase-1-mvp-technical-doc.md)
- [第二阶段持久化技术文档](./phase-2-persistence-technical-doc.md)
- [第三阶段 RAG/知识库工程化技术文档](./phase-3-rag-engineering-technical-doc.md)
- [第四阶段 LLM Provider 与结构化抽取技术文档](./phase-4-llm-provider-technical-doc.md)
- [第五阶段 Agent 节点化编排与长期记忆技术文档](./phase-5-agent-workflow-memory-technical-doc.md)
- [第六阶段 评估集、生产化与交付技术文档](./phase-6-evaluation-production-delivery-technical-doc.md)

跨会话上下文：

- [Codex 项目上下文](../context/codex-project-context.md)
