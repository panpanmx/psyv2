# Context Documents

本目录用于保存跨会话上下文文档，帮助 Codex 或开发者在上下文压缩、会话切换、长时间暂停后快速恢复项目状态。

建议新会话开始时优先阅读：

1. [Codex Project Context](./codex-project-context.md)
2. [后端 Agent 第一版总技术文档](../technical/first-version-backend-agent-technical-doc.md)
3. [第一阶段 MVP 技术文档](../technical/phase-1-mvp-technical-doc.md)
4. [第二阶段持久化计划](../superpowers/plans/2026-06-24-second-phase-persistence.md)
5. [第三阶段 RAG/知识库工程化技术文档](../technical/phase-3-rag-engineering-technical-doc.md)
6. [第四阶段 LLM Provider 与结构化抽取技术文档](../technical/phase-4-llm-provider-technical-doc.md)
7. [第五阶段 Agent 节点化编排与长期记忆技术文档](../technical/phase-5-agent-workflow-memory-technical-doc.md)
8. [第六阶段 评估集、生产化与交付技术文档](../technical/phase-6-evaluation-production-delivery-technical-doc.md)

维护规则：

- 每完成一个阶段，实现者必须更新 `codex-project-context.md` 的当前状态、验证命令、下一步计划和已知限制。
- 每新增阶段技术文档，要在本 README 和 `docs/technical/README.md` 里补链接。
- 不要把密钥、真实用户数据、完整敏感对话写入上下文文档。
