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

## 4. 生成可靠性变体计划

```bash
creative-agent-eval plan-variants --out outputs/variant_plan.json
```

每题登记等价措辞、约束顺序、无关信息、输出表面、工具顺序和工具异常六类条件，共216个Variant Spec。其中约束顺序、无关信息、工具顺序和工具异常已经生成确定性配置；等价措辞和输出表面仍保留为待核对计划。

## 5. 执行离线矩阵

```bash
creative-agent-eval run-offline-matrix --out-dir outputs/offline_matrix
```

输出：

- `traces.jsonl`：Loop运行轨迹；
- `boundary_regressions.jsonl`：边界样例与当前Oracle的关系；
- `case_scores.jsonl`：结合最终输出和Trace形成的Criterion级评分；
- `trace_evaluations.jsonl`：验证、恢复和停止相关的Trace检查；
- `ledger.json`：每个Run的完成状态、失败信息和尝试次数；
- `summary.json`：已完成、失败、剩余数量以及Loop、标签、Criterion与Trace检查分布。

## 6. 断点续跑和运行上限

先执行一部分：

```bash
creative-agent-eval run-offline-matrix \
  --out-dir outputs/offline_matrix \
  --max-runs 60
```

继续尚未完成的Run：

```bash
creative-agent-eval run-offline-matrix \
  --out-dir outputs/offline_matrix \
  --max-runs 60 \
  --resume
```

限制本轮允许出现的失败数：

```bash
creative-agent-eval run-offline-matrix \
  --out-dir outputs/offline_matrix \
  --resume \
  --max-failures 3
```

`--resume`会跳过账本中已经完成的Run。失败Run可以在后续调用中重新尝试，账本会累计尝试次数。

## 7. 工具异常与恢复Trace

工具验证Loop支持确定性异常注入。可恢复异常会形成以下事件：

```text
tool_requested
→ tool_failed
→ tool_retry
→ tool_requested
→ tool_returned
→ revalidation_started
→ revision_created
→ revalidation_completed
→ stop_decision
```

该事件链可用于检查异常是否被识别、是否发生重试、是否获得有效工具结果，以及最终答案是否经过重新验证。空结果会保留为成功返回的特殊结果，不自动触发重试。

## 解释边界

- `supported`表示当前确定性检查能够支持样例标签的一部分；
- `underdetermined`表示仍需语义Judge或人工判断；
- `contradicted`表示样例与已实现的关键确定性检查冲突，应优先修订Case、Gold或Oracle。

全局的通过、边界、失败标签不会自动复制成每个Rubric Criterion的分数。只有与某个维度直接相关的输出或Trace证据才会形成Criterion分数，其余维度保留为待复核。
