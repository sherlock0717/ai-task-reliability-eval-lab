# 评分说明（v0.2）

本项目同时使用两类信号：**规则评分（硬检查）** 与 **质量代理指标（quality proxy，软/粗信号）**。两者都不等价于“最终语义正确性”或人类专家裁判。

## 1. Rule scoring（`src/scorers/rule_scorer.py`）

**性质**：可复现的硬规则，用于快速失败检测与回归对比。

| 检查项 | 含义 | 通过条件（简化） |
|--------|------|------------------|
| `expected_output_type` | 输出形态是否与任务约定一致 | `text`/`markdown` 非空；`json` 可解析为对象/数组或合法 JSON 字符串 |
| `must_include` | 必须出现的短语文本（锚点） | 每个短语都出现在输出（规范化文本 + 原文拼接）中 |
| `must_not_do` | 禁止出现的短语 | 任一短语出现则失败 |
| `json_parseable` | 当且仅当任务要求 JSON 时启用 | 输出可解析为 JSON |

**权重**：`json_parseable` 在非 JSON 任务上会跳过并不计入平均分母（与 v0.1 一致）。

## 2. Quality proxy scoring（`src/scorers/quality_proxy_scorer.py`）

**性质**：启发式代理指标，用于仪表盘与粗粒度 triage，**不是**语义金标准。

| 指标 | 含义 | 说明 |
|------|------|------|
| `required_item_coverage` | `must_include` 命中比例 | 与规则重叠，但用连续值表达覆盖度 |
| `forbidden_violation_count` | `must_not_do` 命中次数 | 计数型 |
| `output_nonempty` | 输出非空 | 布尔 |
| `json_valid` | JSON 语法有效 | 非 JSON 任务恒为 True（跳过语义） |
| `citation_presence` | 引用/条款样式信号 | 仅在 `metadata.proxy_expect_citation=true` 的任务上计算，否则为 `null` |
| `constraint_hit_rate` | 与 `constraints` 文本的粗匹配率 | 非常粗糙：短前缀是否在输出中出现 |

**重要**：`citation_presence` 只检测括号、`FAQ`、条款编号等**表面模式**，无法判断引用是否真实、恰当。

## 3. Failure taxonomy（`src/analysis/failure_taxonomy.py`）

**性质**：基于规则结果 + proxy + trace 的**确定性映射**，用于初步归因与统计，不是机器学习分类器。

## 4. 与“最终评测”区别

- **规则失败**通常意味着交付物明显不可用（格式不对、缺锚点、触发禁用语）。
- **规则通过 + proxy 低分**可能仍然语义错误——需要人工或更强的评测协议。
- **真实 LLM 运行**仍受 prompt、温度、模型与数据分布影响；本仓库不把分数解释为通用模型排名。
