# DeepSeek V4 创造性 Agent Loop 评测

这个仓库关注一个具体问题：当模型参数保持不变时，Agent 的生成、筛选、验证、修订和停止流程会怎样影响创造性任务的完成质量。

首版围绕 DeepSeek V4 设计。当前已经完成 36 个试测 Case，每个 Case 都包含正式题面、局部工具环境、结构化 Gold、Rubric 锚点和通过／边界／失败样例。仓库暂未调用 API，也没有展示模型分数。

## 研究主线

- 比较单次生成、批评修订、发散收敛和工具验证四种 Loop；
- 分开观察新颖性、适用性、约束满足、验证质量、恢复能力和停止判断；
- 记录完整运行轨迹，定位问题发生在模型生成、Harness、工具、Judge 或任务设计中的哪个环节；
- 根据稳定失败模式整理可供后训练研究使用的数据形态和候选方法，相关结论只作为后续实验假设。

## 36 个 Case

| Suite | 数量 | 内容 |
|---|---:|---|
| A 心理学构念探针 | 9 | 条件化发散、替代用途、发散—收敛连接 |
| B 约束创造问题解决 | 9 | 非常规资源使用、物理可行性和工具核验 |
| C 创造产品生成 | 9 | 产品机制、信息重构和受约束叙事 |
| D Loop 适应与恢复 | 9 | 约束突变、错误反馈、记忆误用和停止判断 |

[打开项目展示页](https://sherlock0717.github.io/ai-task-reliability-eval-lab/)可浏览每个 Case 的题面、Gold、Rubric 和边界样例。

## 当前状态

- 36 个 Case 已进入 `pilot`；
- 题面和 Rubric 已具备首轮人工试做条件；
- Gold 采用“可接受解空间 + 禁止失败 + 说明性示例”的结构，不限定唯一措辞；
- 正式跑批前仍需完成双人复核、歧义修订、工具 fixture 实现和 DeepSeek 接口复核。

## Loop 条件

- `L0 one_shot`：解析任务后直接生成最终结果；
- `L1 critique_revise`：生成、独立批评、修订、验收；
- `L2 divergent_convergent`：并行候选、去重聚类、比较、整合；
- `L3 tool_grounded`：识别关键假设、调用工具、依据证据修订。

## 本地校验

```bash
python -m pip install -e ".[dev]"
creative-agent-eval validate-registry
pytest
```

## 主要文件

- `docs/data/`：按四个 Suite 拆分的 36 个完整 Case，页面与 Python 校验读取同一份数据；
- `benchmark/schemas/case.schema.json`：数据结构；
- `benchmark/rubrics/core_dimensions.yaml`：通用评分原则；
- `configs/loops/`：四种 Loop 条件；
- `docs/`：GitHub Pages 和研究文档；
- `src/creative_agent_eval/`：注册表校验与后训练诊断映射。

## 研究边界

心理学任务在这里用于拆分可观察的任务表现。项目不会据此判断模型是否具有与人相同的心理特质。语义距离、模型 Judge 和人工评分各自承担不同作用，任何单项指标都不会直接成为“创造力总分”。
