# DeepSeek V4 创造性 Agent Loop 评测

这个仓库研究模型参数保持不变时，Agent 的生成、筛选、验证、修订和停止流程如何影响创造性任务表现。

首版围绕 DeepSeek V4 设计。当前包含 36 个试测 Case，每题具备正式题面、局部工具环境、结构化 Gold、Rubric 锚点和通过／边界／失败样例。仓库已经具备四种 Loop 的干跑能力和单 Case API 入口，尚未发布正式模型成绩。

## 研究主线

- 比较单次生成、批评修订、发散收敛和工具验证四种 Loop；
- 分开观察新颖性、适用性、约束满足、验证质量、恢复能力和停止判断；
- 保存运行轨迹，定位问题发生在模型生成、Harness、工具、Judge或任务设计中的具体环节；
- 根据稳定失败模式整理后续训练研究可使用的数据形态和候选方法。

## 36 个 Case

| Suite | 数量 | 内容 |
|---|---:|---|
| A 心理学构念探针 | 9 | 条件化发散、替代用途、发散—收敛连接 |
| B 约束创造问题解决 | 9 | 非常规资源使用、物理可行性和工具核验 |
| C 创造产品生成 | 9 | 产品机制、信息重构和受约束叙事 |
| D Loop 适应与恢复 | 9 | 约束突变、错误反馈、记忆误用和停止判断 |

[打开项目展示页](https://sherlock0717.github.io/ai-task-reliability-eval-lab/)可浏览每个 Case 的题面、Gold、Rubric 和边界样例。

## 当前执行能力

- 36 个 Case 均处于 `pilot`；
- `L0`、`L1`、`L2`、`L3` 已有统一运行接口和阶段级 Trace；
- Scripted Provider 可用边界样例完成离线干跑；
- 工具层已实现白名单、确定性 fixture 和基础检查工具；
- `benchmark/fixtures/B04.json` 提供首个可执行 fixture；
- DeepSeek Provider 支持 V4-Flash、V4-Pro、思考模式和非思考模式；
- GitHub Actions 提供单 Case、手动触发的 API 冒烟测试；
- 正式结果目录仍为空。

## Loop 条件

- `L0 one_shot`：解析任务后直接生成结果；
- `L1 critique_revise`：生成、批评、修订、验收；
- `L2 divergent_convergent`：多候选生成、比较、整合；
- `L3 tool_grounded`：识别关键假设、调用工具、依据证据修订。

## 本地校验与干跑

```bash
python -m pip install -e ".[dev]"
creative-agent-eval validate-registry
pytest
creative-agent-eval dry-run --case-id B04 --loop L3 \
  --fixture benchmark/fixtures/B04.json \
  --out outputs/dry_run/B04_L3.json
```

## API运行

密钥通过环境变量或GitHub Secret注入，不写入仓库。在线与本地步骤见 [`docs/ONLINE_API_RUN.md`](docs/ONLINE_API_RUN.md)。

当前在线工作流只执行一个 Case，并把 Trace 保存为 Artifact。批量实验会在 fixture、Oracle 和评分层完成后开放。

## 主要文件

- `docs/data/`：36 个完整 Case，页面和Python读取同一份数据；
- `benchmark/fixtures/`：确定性工具环境；
- `benchmark/schemas/case.schema.json`：Case数据结构；
- `configs/loops/`：四种Loop条件；
- `src/creative_agent_eval/loops/`：Loop执行；
- `src/creative_agent_eval/tools/`：工具注册和fixture；
- `src/creative_agent_eval/runtime/`：Trace结构；
- `src/creative_agent_eval/providers/`：Scripted与DeepSeek Provider；
- `docs/`：GitHub Pages和研究文档。

## 后续工程任务

1. 为其余35题补齐fixture；
2. 将`automatic_checks`映射为可执行Oracle；
3. 建立Criterion级评分结果；
4. 用108个边界样例做回归测试；
5. 建立实验矩阵、批量运行和结果分析；
6. 接入正式API跑批。

## 研究边界

心理学任务用于拆分可观察的任务表现。项目不会据此判断模型是否具有与人相同的心理特质。语义距离、模型Judge和人工评分承担不同作用，任何单项指标都不会直接成为“创造力总分”。
