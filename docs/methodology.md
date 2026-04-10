# 方法论（v0.2）

## 评的是什么

本项目评估的是 **工作流策略（workflow policy）** 在固定任务分布下的表现：例如「单轮直答」「检索增强」「规划执行」「人工门禁」等策略如何影响 **可交付性、约束遵守、可追溯性**，而不是做 **通用模型排行榜**。同一任务上更换模型权重可能改变分数，但实验单元仍是「策略 + 任务 + 运行配置」的组合。

## v0.2：mock / real LLM 双模式

- **Mock（默认）**：`USE_REAL_LLM=false` 或未配置 API 时，`DirectAdapter` 使用 `SmartMockTextGenerator`，保证无密钥也可跑通实验闭环并落盘 trace。
- **Real LLM（可选）**：`USE_REAL_LLM=true` 且 `OPENAI_COMPAT_*` 配置齐全时，通过 **OpenAI-compatible** HTTP 客户端调用 `/v1/chat/completions`（见 `src/clients/openai_compatible.py`）。trace 记录 `provider`、`model_name`、`is_mock`。

**注意**：真实模型运行结果受 **prompt、温度、模型、服务端** 影响；本仓库不把单次分数解释为稳定能力排名。

## 任务与数据

- 任务集：`data/tasks/v1_tasks.jsonl`（v0.2：12 条；含 extraction / rewrite / qa）。
- 素材：`data/fixtures/**` 以 `.md` / `.txt` 为主，便于 GitHub 阅读。

## 评分与归因

- **Rule scoring**：硬规则检查（类型、锚点短语、禁用短语、JSON 可解析）。
- **Quality proxy**：轻量启发式指标（覆盖度、引用样式信号等），见 `docs/rubric.md`。
- **Failure taxonomy**：规则型映射到初步失败类型，见 `docs/failure_taxonomy.md`。

## 可追溯性

每次运行写入 **trace**（输入快照、原始输出、规范化输出、错误、耗时、token、provider/model/is_mock 等），支持离线复盘与策略迭代。

## 刻意不做

复杂前端、数据库、外部通用评测平台、通用 SaaS 化——保持仓库可作为短期 GitHub 展示项目。
