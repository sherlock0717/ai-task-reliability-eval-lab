# 可靠性扰动与平行条件

首批36个Case为每题建立6类变体条件，共216个Variant Spec。变体按原始`case_id`和`problem_family`分组，后续划分数据集时必须作为同一问题族处理。

## 六类条件

| 类型 | 当前状态 | 目的 |
|---|---|---|
| `equivalent_wording` | planned | 检查等价措辞稳定性，需要后续生成与约束核对 |
| `constraint_order` | materialized | 保留原始文本，只调整非空行顺序 |
| `irrelevant_context` | materialized | 加入明确无关的记录信息，检查抗干扰能力 |
| `output_surface` | planned | 只改变输出容器或字段名，需要同步适配Oracle |
| `tool_order` | materialized | 保持工具集合不变，只调整声明顺序 |
| `tool_fault` | materialized | 首次工具调用模拟可恢复超时，检查恢复与重试 |

生成计划：

```bash
creative-agent-eval plan-variants --out outputs/variant_plan.json
```

## 状态含义

- `materialized`：已经生成确定性Prompt、工具顺序或异常情境配置；
- `planned`：只登记变换合同，尚未生成最终题面。

等价措辞和输出表面变体仍需要检查硬约束、交付单元和Gold是否保持一致。仓库不会仅凭自动改写将其直接列入正式测试集。

## 使用边界

1. 同一Case及其所有变体必须进入同一数据划分；
2. 无关信息不能提供额外解题线索；
3. 工具异常情境只能改变工具状态，不能改变任务Gold；
4. 输出表面变体不能改变需要完成的内容；
5. 扰动结果单独报告，不能与原题分数混成一个总分。
