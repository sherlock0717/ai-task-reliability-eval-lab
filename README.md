# AI Task Reliability Eval Lab

本仓库不是通用大模型平台，而是一套用于比较 **AI 工作流策略（workflow policy）** 可靠性的本地实验工程：给定同一批贴近办公/求职/知识工作的任务样本，用不同候选策略（candidate）跑任务、落盘 trace、做可复现的规则评分，并输出汇总结果。

## v0.1 范围（求职展示版 / 最小闭环）

- **任务**：从 `data/tasks/v1_tasks.jsonl` 读取样本；任务结构由 `data/tasks/task_schema.json` 描述（`extraction` / `rewrite` / `qa`）。
- **候选策略**：仅实现 **direct** baseline（单轮直答；无检索、无规划、无人工确认）。代码通过 `WorkflowAdapter` 预留 `retrieve` / `planexec` / `humangate` 等扩展点，不在 v0.1 写死实现细节。
- **执行与落盘**：每条任务生成一条 **trace**（JSONL），写入 `outputs/runs/<experiment_id>/traces.jsonl`；单条调试运行写入 `outputs/runs/single_<run_id>/traces.jsonl`。
- **评分**：`src/scorers/rule_scorer.py` 做基础规则检查（输出类型、`must_include` / `must_not_do`、JSON 可解析等），结果写入 `outputs/scored_runs/<experiment_id>/scores.jsonl`。
- **汇总**：批量跑完后生成 `outputs/summaries/<experiment_id>/summary.json`。
- **刻意不做**：复杂前端、数据库、外部评测平台、通用 SaaS 化。

## 环境

- Python **3.9+**
- 依赖见 `requirements.txt`（v0.1 仅需要 `jsonschema` 用于可选的任务校验）。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 目录结构（核心）

```
data/
  tasks/
    task_schema.json    # 任务 JSON Schema
    v1_tasks.jsonl      # v0.1 样例任务（JSONL）
  samples/              # 任务引用的示例输入文件（JD、政策片段等）
src/
  adapters/             # 工作流适配器（direct baseline + 基类）
  runners/              # CLI：单条 / 批量实验
  traces/               # trace 结构与 JSONL 记录器
  scorers/              # 规则评分
  analysis/             # 汇总
  utils/                # JSONL / IO 工具
outputs/                # 运行产物（runs / scored_runs / summaries）
docs/
  methodology.md        # 方法论说明
configs/                # 预留：后续多候选配置（v0.1 可不依赖）
```

## 如何运行

在项目根目录（本仓库根目录）执行，确保当前工作目录为根目录，以便解析 `data/` 下相对路径。

### 推荐方式 vs 兼容方式

| 方式 | 示例 | 说明 |
|------|------|------|
| **推荐** | `python -m src.runners.run_single_task ...` | 以包方式运行：解释器会正确设置包上下文与 `sys.path`，`from src...` 由 Python 按包解析，行为与打包/测试一致。 |
| **兼容** | `python .\src\runners\run_single_task.py ...` | 直接跑脚本文件也可：runner 顶部在 `__package__` 为空时会把仓库根目录插入 `sys.path`，从而仍能 `import src`。 |

更推荐使用 **`python -m ...`**：不依赖脚本里的路径补丁、与 [PEP 338](https://peps.python.org/pep-0338/) 的模块执行语义一致，也避免将来移动入口文件时产生歧义。兼容方式便于在资源管理器中双击或 IDE 里「运行当前文件」调试。

### 单条任务（direct）

```bash
python -m src.runners.run_single_task --task-id v1-qa-001
```

兼容（需在仓库根目录执行，或自行保证 `data/` 相对路径可用）：

```bash
python .\src\runners\run_single_task.py --task-id v1-qa-001
```

常用参数：

- `--tasks-file`：自定义任务 JSONL（默认 `data/tasks/v1_tasks.jsonl`）
- `--validate-schema`：用 `data/tasks/task_schema.json` 校验该条任务
- `--output-dir`：自定义 trace 输出目录（默认 `outputs/runs/single_<uuid>/`）

评分结果默认写在 `outputs/scored_runs/single_<同一 run 目录名>/scores.jsonl`（与 trace 目录名对齐）。

### 批量实验（direct，全量 v1_tasks.jsonl）

```bash
python -m src.runners.run_experiment
```

兼容：

```bash
python .\src\runners\run_experiment.py
```

可选：

- `--experiment-id my_run`：指定输出子目录名（默认 UTC 时间戳 `exp_...`）
- `--tasks-file`：自定义任务集

产物：

- `outputs/runs/<experiment_id>/traces.jsonl`
- `outputs/scored_runs/<experiment_id>/scores.jsonl`
- `outputs/summaries/<experiment_id>/summary.json`

### 仅汇总已有 scores.jsonl

```bash
python -m src.analysis.summarize outputs/scored_runs/<experiment_id>/scores.jsonl --out outputs/summaries/<experiment_id>/summary.json
```

## Mock 与后续接入真实 LLM

v0.1 默认使用 **`MockTextGenerator`** 生成看起来像任务类型的文本/JSON，以便无 API Key 也能跑通闭环。将 `DirectAdapter(generator=...)` 换成实现 `TextGenerator` 协议的真实客户端即可；`token_usage`、`estimated_cost` 等字段已在 trace 中预留。

## 许可证与数据

样例任务与样例文件为演示用途；邮箱与域名多为虚构，请勿用于真实投递。
