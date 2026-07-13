# DeepSeek V4 创造性 Agent Loop 评测

这个仓库研究模型参数保持不变时，Agent 的生成、筛选、验证、修订和停止流程如何影响创造性任务表现。

首版围绕 DeepSeek V4 设计。当前包含36个试测Case，每题具备正式题面、局部工具环境、结构化Gold、Rubric锚点和通过／边界／失败样例。仓库已经具备四种Loop的离线运行、fixture生成、评测合同审计、可靠性变体计划和单Case API入口，尚未发布正式模型成绩。

## 数据来源说明

四个Suite、任务族和公开来源筛选在逐题生成前已经确定。当前36题的题面、工具环境、Gold、Rubric和边界样例均由AI助手生成首稿，尚未完成用户逐题审定或独立专家验证。

公开研究和Benchmark用于方法、构念、任务结构与错误分类参考，没有题目被登记为公开Benchmark原题。当前题集应理解为`adapted_parallel`与`original_diagnostic`试测数据。

详细说明见[`docs/DATA_PROVENANCE_AUDIT.md`](docs/DATA_PROVENANCE_AUDIT.md)，逐题审定方法见[`docs/CASE_REVIEW_GUIDE.md`](docs/CASE_REVIEW_GUIDE.md)。

## 研究主线

- 比较单次生成、批评修订、发散收敛和工具验证四种Loop；
- 分开观察新颖性、适用性、约束满足、验证质量、恢复能力和停止判断；
- 保存运行轨迹，定位问题发生在模型生成、Harness、工具、Judge或任务设计中的具体环节；
- 根据稳定失败模式整理后续训练研究可使用的数据形态和候选方法。

## 36个Case

| Suite | 数量 | 内容 |
|---|---:|---|
| A 心理学构念探针 | 9 | 条件化发散、替代用途、发散—收敛连接 |
| B 约束创造问题解决 | 9 | 非常规资源使用、物理可行性和工具核验 |
| C 创造产品生成 | 9 | 产品机制、信息重构和受约束叙事 |
| D Loop适应与恢复 | 9 | 约束突变、错误反馈、记忆误用和停止判断 |

[打开项目展示页](https://sherlock0717.github.io/ai-task-reliability-eval-lab/)可浏览每个Case的题面、Gold、Rubric和边界样例。

## 当前执行能力

- 36个Case均处于`pilot`；
- `L0`、`L1`、`L2`、`L3`已有统一运行接口和阶段级Trace；
- Scripted Provider可用边界样例完成离线干跑；
- 36题都可从题面、Gold和工具声明生成确定性基线fixture；
- `benchmark/fixtures/B04.json`保留为首个手工Case级fixture；
- 171条Rubric Criterion进入统一评分合同；
- 108个通过／边界／失败样例进入回归管线；
- 默认离线实验矩阵为36 Case × 4 Loop × 3标签，共432次运行；
- 每题建立6类可靠性变体合同，共216个Variant Spec；
- 自动检查按确定性、结构化输出、Trace依赖、Case fixture依赖和语义判断五类管理；
- 离线运行支持账本、断点续跑、失败上限和CI Artifact；
- CI可导出36题完整人工审阅包；
- DeepSeek Provider支持V4-Flash、V4-Pro、思考模式和非思考模式；
- GitHub Actions提供单Case、手动触发的API冒烟测试；
- 正式模型结果目录仍为空。

## Loop条件

- `L0 one_shot`：解析任务后直接生成结果；
- `L1 critique_revise`：生成、批评、修订、验收；
- `L2 divergent_convergent`：多候选生成、比较、整合；
- `L3 tool_grounded`：识别关键假设、调用工具、依据证据修订。

## 离线校验与运行

```bash
python -m pip install -e ".[dev]"
creative-agent-eval validate-registry
creative-agent-eval materialize-fixtures --out-dir outputs/materialized_fixtures
creative-agent-eval audit-evaluation --out outputs/evaluation_audit.json
creative-agent-eval plan-experiment --out outputs/offline_plan.json
creative-agent-eval plan-variants --out outputs/variant_plan.json
creative-agent-eval run-offline-matrix --out-dir outputs/offline_matrix
python scripts/export_review_pack.py --out-dir outputs/review_pack
pytest
```

离线管线说明见[`docs/OFFLINE_PIPELINE.md`](docs/OFFLINE_PIPELINE.md)，扰动条件见[`docs/VARIANT_PROTOCOL.md`](docs/VARIANT_PROTOCOL.md)。这些流程验证数据结构、Loop、Trace、fixture、Oracle和评分合同，不产生模型能力结论。

## API运行

密钥通过环境变量或GitHub Secret注入，不写入仓库。在线与本地步骤见[`docs/ONLINE_API_RUN.md`](docs/ONLINE_API_RUN.md)。

当前在线工作流只执行一个Case，并把Trace保存为Artifact。未配置Secret时工作流会正常结束且不发送API请求。

## 主要文件

- `docs/data/`：36个完整Case，页面和Python读取同一份数据；
- `benchmark/provenance/`：题族来源和生成方式登记；
- `benchmark/fixtures/`：手工fixture和生成规则说明；
- `benchmark/schemas/case.schema.json`：Case数据结构；
- `configs/loops/`：四种Loop条件；
- `src/creative_agent_eval/loops/`：Loop执行；
- `src/creative_agent_eval/tools/`：工具注册、fixture和生成器；
- `src/creative_agent_eval/evaluation/`：Oracle、Criterion评分与评测审计；
- `src/creative_agent_eval/review_pack.py`：完整审阅包生成；
- `src/creative_agent_eval/experiments.py`：离线实验矩阵；
- `src/creative_agent_eval/variants.py`：可靠性变体合同；
- `src/creative_agent_eval/offline.py`：离线批量运行与账本；
- `src/creative_agent_eval/runtime/`：Trace结构；
- `src/creative_agent_eval/providers/`：Scripted与DeepSeek Provider；
- `docs/`：GitHub Pages和研究文档。

## 后续工程任务

1. 完成用户对36题的逐题审定，记录`保留 / 修改 / 移除 / 重做`；
2. 为需要精确物理参数、语义关系或状态转移的Case补充手工fixture；
3. 将Trace依赖和Case fixture依赖的检查逐步实现为专用Oracle；
4. 完成等价措辞与输出表面两类待生成变体的约束核对流程；
5. 建立Trace、离线审计与变体计划的展示页面；
6. 增加正式批量实验的预算控制和结果分析；
7. 接入正式API跑批与统计分析。

## 研究边界

心理学任务用于拆分可观察的任务表现。项目不会据此判断模型是否具有与人相同的心理特质。语义距离、模型Judge和人工评分承担不同作用，任何单项指标都不会直接成为“创造力总分”。
