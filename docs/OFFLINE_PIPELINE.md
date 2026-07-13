# 离线执行与回归管线

该管线不调用外部模型，使用每题已经登记的通过、边界和失败样例验证评测工程。

## 1. 生成fixture

```bash
creative-agent-eval materialize-fixtures --out-dir outputs/materialized_fixtures
```

## 2. 审计评测合同

```bash
creative-agent-eval audit-evaluation --out outputs/evaluation_audit.json
```

审计内容包括Case数量、Rubric数量、边界样例、工具声明、fixture覆盖、Oracle覆盖和边界样例与确定性检查的关系。

## 3. 生成实验矩阵

```bash
creative-agent-eval plan-experiment --out outputs/offline_plan.json
```

默认矩阵为36 Case × 4 Loop × 3边界标签，共432次离线运行。此矩阵用于验证运行器和结果结构，不代表模型实验。

## 4. 执行离线矩阵

```bash
creative-agent-eval run-offline-matrix --out-dir outputs/offline_matrix
```

输出：

- `traces.jsonl`：Loop运行轨迹；
- `boundary_regressions.jsonl`：边界样例与当前Oracle的关系；
- `summary.json`：运行数、Loop分布、标签分布和终止状态。

## 解释边界

- `supported`表示当前确定性检查能够支持样例标签的一部分；
- `underdetermined`表示仍需语义Judge或人工判断；
- `contradicted`表示样例与已实现的关键确定性检查冲突，应优先修订Case、Gold或Oracle。

全局的通过、边界、失败标签不会自动复制成每个Rubric Criterion的分数。只有与某个维度直接相关的确定性检查才会形成Criterion分数，其余维度保留为待复核。
