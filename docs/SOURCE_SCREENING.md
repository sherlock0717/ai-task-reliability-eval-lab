# 公开研究与数据集筛选

筛选依据包含研究贴合度、构念效度、许可边界、自动验证能力和诊断价值。首批题面均为重新撰写，避免把公开测试题直接复制进仓库。

## 采用

| 资料 | 用途 | 许可与处理 |
|---|---|---|
| MacGyver | 约束创造问题、物理不可行错误、发散—收敛反思 | 官方仓库为 Apache-2.0；本项目只借鉴任务结构，并重新撰写9题 |
| CDAT | 条件化新颖性与适切性门槛 | 借鉴方法；A01—A03采用自写中文情境和独立Gold |
| Reflexion | 反馈、反思和外部记忆的Loop结构 | 仅借鉴公开论文方法 |
| DeepSeek官方API文档 | 模型配置、思考模式、工具调用和轨迹记录 | 正式跑批前复核接口版本 |

## 改造

| 资料 | 改造内容 |
|---|---|
| Alternative Uses Task | 更换低污染物品，加入资源、安全和说明要求 |
| DAT | 仅保留语义发散指标，增加情境适切性和随机基线 |
| DRAT | 自建目标词、义域关系表和泄漏检查 |
| WritingBench及创造写作榜单 | 借鉴实例Rubric、盲评和顺序反转，题面全部重写 |
| SemDis | 作为语义距离工具参考，不直接给出最终创造力结论 |

## 仅参考

- GEPA、TextGrad、DSPy/MIPROv2：用于后续Prompt与Loop搜索对照；
- DPO、奖励模型、过程奖励和Agent RL研究：用于形成后训练候选路径；
- CreativityPrism及跨领域创造力评测：用于多维结果组织；
- AGC-Bench等综合创造力Benchmark：用于任务覆盖审查。

## 排除

| 资料或做法 | 原因 |
|---|---|
| TTCT正式题和商业评分材料 | 标准化测验受版权和施测规范限制 |
| 创造人格、创造自我效能等自陈量表直接用于模型 | 构念依赖人的持续自我经验，模型回答缺少同等解释基础 |
| 纯自由写作 | 自动核验弱，Loop失败难定位 |
| 单一LLM Judge | 容易受长度、风格、顺序和自评偏差影响 |
| 只用语义距离排序 | 随机词也可能获得较高发散分 |
| 许可不明的原始长文本 | 无法保证公开再分发边界 |

## 主要来源

- MacGyver: Are Large Language Models Creative Problem Solvers? https://arxiv.org/abs/2311.09682
- MacGyver repository: https://github.com/allenai/MacGyver
- Beyond Divergent Creativity / CDAT: https://arxiv.org/abs/2601.20546
- Assessing the Creativity of Large Language Models / DRAT: https://arxiv.org/abs/2605.13450
- Reflexion: https://arxiv.org/abs/2303.11366
- GEPA: https://arxiv.org/abs/2507.19457
