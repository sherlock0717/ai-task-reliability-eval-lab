# 方法论（v0.1）

## 评的是什么

本项目评估的是 **工作流策略（workflow policy）** 在固定任务分布下的表现：例如「单轮直答」「检索增强」「规划执行」「人工门禁」等策略如何影响 **可交付性、约束遵守、可追溯性**，而不是做 **通用模型排行榜**。同一任务上更换模型权重可能改变分数，但实验单元仍是「策略 + 任务 + 运行配置」的组合。

## v0.1 任务类型

- **extraction**：从给定材料中抽取结构化要点（办公/求职场景，如 JD 信息整理）。
- **rewrite**：在约束下改写为可交付文体（如简历要点、对外说明）。
- **qa**：在明确规则下作答；部分任务要求 **严格 JSON** 输出，便于后续程序消费与规则校验。

任务字段（含 `must_include` / `must_not_do` / `expected_output_type`）见 `data/tasks/task_schema.json` 与 `data/tasks/v1_tasks.jsonl`。

## Candidate 范围（v0.1）

仅实现 **direct** baseline：单轮调用、无检索、无多步规划、无人工确认。适配器层通过抽象基类预留其它 candidate，避免把 direct 逻辑散布在 runner 中。

## 评分思路（规则优先）

v0.1 使用 **可复现的规则检查** 作为基线信号：

1. **expected_output_type**：文本非空，或 JSON 可解析为对象/数组（依任务约定）。
2. **must_include / must_not_do**：字符串级检查（用于锚定关键信息、禁用套话或违规措辞）。
3. **JSON 可解析**：当 `expected_output_type` 为 `json` 时，要求输出可解析（解析结果可为 dict/list）。

规则分数 **不是** 语义质量的全貌；它用于快速失败检测与回归对比。后续可叠加 LLM-as-judge、人工评分或对照 `reference_answer`，但不在 v0.1 强制依赖外部平台。

## 可追溯性

每次运行写入 **trace**（输入快照、原始输出、规范化输出、错误、耗时、token 占位等），支持对失败样例做离线复盘与策略迭代。
