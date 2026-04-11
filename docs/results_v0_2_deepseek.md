# 实验结果摘要：v0.2 · DeepSeek 兼容 API（direct baseline）

> 本文档基于仓库内一次真实跑批产物整理，数字来自 `outputs/summaries/v0_2_deepseek/summary.json`（与 `site/showcase/assets/data/summary_v0_2_deepseek.json` 对齐）。可直接用于作品集文字材料，但请先阅读下方**口径说明**。

## 评测口径说明（必读）

当前 v0.2 摘要中的「通过 / 未通过」主要反映**规则检查结果**，表示输出是否满足结构、字段与基础约束要求；**不等同于**最终语义质量结论，**也不代表**无需人工复核。下文表格中的「规则通过 / 规则未通过」均指规则层，**不是**“任务语义质量已被充分验证”。

**本实验的重点**是 **workflow reliability 的基础验证**（能否在统一任务集上稳定跑通、落盘 trace、通过预设硬规则），**而不是**对最终业务质量下结论。

## 实验设置（简述）

- **候选策略**：`direct-v0.2`（单轮直答；OpenAI-compatible 真实调用）。
- **任务集**：`data/tasks/v1_tasks.jsonl`，共 **12** 条（extraction / rewrite / qa 各 4；难度含 easy / medium / hard）。
- **评分**：规则评分 + quality proxy（**代理指标**）+ failure taxonomy（**规则型初版**）。

## 关键数字（summary.json）

| 指标 | 值 |
|------|-----|
| 任务总数 | 12 |
| 规则通过任务数（passed） | 12 |
| 规则未通过任务数（failed） | 0 |
| 平均规则分（avg_rule_score） | 1.0 |
| 执行成功 trace 数 | 12 |
| 执行报错 trace 数 | 0 |

### 按任务类型（by_task_type）

| 类型 | 任务数 | 规则通过任务数 | 规则未通过任务数 |
|------|--------|----------------|------------------|
| extraction | 4 | 4 | 0 |
| rewrite | 4 | 4 | 0 |
| qa | 4 | 4 | 0 |

### 按难度（by_difficulty）

| 难度 | 任务数 | 规则通过任务数 | 规则未通过任务数 |
|------|--------|----------------|------------------|
| easy | 3 | 3 | 0 |
| medium | 6 | 6 | 0 |
| hard | 3 | 3 | 0 |

### Quality proxy 均值（代理指标）

- `required_item_coverage`：**1.0**
- `forbidden_violation_count_avg`：**0.0**
- `constraint_hit_rate`：**0.0**（实现为粗匹配，低值不等价于“违反约束”）
- `output_nonempty_rate`：**1.0**
- `json_valid_rate`：**1.0**
- `citation_presence_avg`：**0.5**（仅对标记为引用敏感的任务聚合）

### 失败归因分布（failure taxonomy，规则型初版）

- `ok`：**12**（其余类型计数为 0）

## 为什么「规则通过率」不是全部

规则通过率只能说明输出在**结构性合规**上是否达标，**不能**代表语义事实正确或业务可直接采信；**不能替代人工复核**。若要逼近质量定论，需要对照金标、抽检、人工标注，以及对 LLM-as-judge 保持审慎；**failure taxonomy** 初版与 **quality proxy** 应作为并列线索，而非单一“通过率叙事”。

## 四张图（一句话解释）

图表文件位于 `outputs/charts/v0_2_deepseek/`（展示页副本在 `site/showcase/assets/charts/v0_2_deepseek/`）。

1. **failure_type_distribution.png**：规则型 **failure taxonomy** 主标签计数；**quality proxy** 仅为代理指标。本次全部为 `ok` 表示未映射到更高优先级规则桶，**不等于**无幻觉。
2. **pass_rate_by_difficulty.png**：各难度下**规则层**通过比例（非语义评分）；三类难度本次均为 100%。**12/12 规则通过不代表**可直接生产部署或无需人工复核。
3. **pass_rate_by_task_type.png**：三类任务的**规则通过率**；本次均为 100%，仅为结构性合规统计。
4. **quality_proxy_overview.png**：**quality proxy** 代理指标均值；不替代语义评测。

## 保守结论（可直接引用）

- 在本次任务集与 direct 设置下，**规则层未出现结构性失败**，且执行侧 trace 无适配器报错，适合作为「端到端闭环可跑通 + 可复现记录」的**基础**展示证据。
- **不能**据此得出“语义全面正确”“可免人工复核”或“强于其他模型/策略”的结论。

## 当前局限（务必保留给读者）

1. **Quality proxy** 是启发式代理，**不是**最终语义质量裁判。
2. **Failure taxonomy** 是规则型初版映射，不做复杂智能判断。
3. **任务规模小**（12 条），覆盖真实业务仍远不足。
4. **仅 direct** 作为完整跑批对象；多 workflow 对照仍待补齐。
