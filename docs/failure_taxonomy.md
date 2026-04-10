# 失败归因初版（v0.2）

## 目标

在 **不做复杂智能判断** 的前提下，为每次任务运行给出一个 **primary failure type**，便于汇总图表与人工复盘。分类逻辑见 `src/analysis/failure_taxonomy.py`。

## 标签定义

| `primary` | 何时触发（简化） |
|-----------|------------------|
| `format_failure` | 适配器非成功、JSON 无效、输出类型不满足、JSON 规则失败等 |
| `missing_required_info` | 规则 `must_include` 未满足 |
| `forbidden_content` | 规则 `must_not_do` 触发 |
| `empty_output` | 原始输出为空或仅空白 |
| `likely_grounding_issue` | 输入材料读取失败（`input_snapshot.resolved_files` 含 `error`），输出可能未基于原文 |
| `needs_human_review` | 规则通过但存在 proxy 红旗（如低引用信号），或其它未落入上述桶的情况 |
| `ok` | 规则检查通过且未触发上述风险规则 |

## 限制

- 不检测幻觉事实、不验证引用真实性。
- `likely_grounding_issue` 仅反映**文件是否读入**，不反映模型是否“真正理解”附件。
- 后续可接入：LLM-as-judge（需谨慎）、人工标注、对照 `reference_answer`。
