# AI Task Reliability Eval Lab

本仓库不是通用大模型平台，而是一套用于比较 **AI 工作流策略（workflow policy）** 可靠性的本地实验工程：给定贴近办公/求职/知识工作的任务样本，用候选策略（candidate）跑任务、落盘 trace、做规则与 **quality proxy** 汇总，并导出 **summary + 图表**，便于 GitHub 展示与复盘。

## v0.2 范围（可展示实验版）

- **任务**：`data/tasks/v1_tasks.jsonl` 共 **12** 条（extraction / rewrite / qa 各 4）；结构化定义见 `data/tasks/task_schema.json`。
- **素材**：`data/fixtures/{extraction,rewrite,qa}/` 下的 `.md` / `.txt`（可读、可版本管理）。
- **候选策略**：**direct** baseline（单轮直答）。支持 **Mock（默认）** 与 **OpenAI-compatible 真实 LLM（可选）**；适配器仍通过抽象接口预留 retrieve / planexec / humangate。
- **评分**：规则评分 + `quality_proxy`（**不是**最终语义评测；见 `docs/rubric.md`）。
- **归因**：规则型 failure taxonomy（见 `docs/failure_taxonomy.md`）。
- **产出**：`outputs/runs/`、`outputs/scored_runs/`、`outputs/summaries/`、`outputs/charts/`。
- **刻意不做**：复杂前端、数据库、外部通用评测 SaaS。

## 环境

- Python **3.9+**
- 依赖见 `requirements.txt`（`jsonschema`、`python-dotenv`、`matplotlib`）。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Mock 与 Real LLM

| 模式 | 条件 | 行为 |
|------|------|------|
| **Mock** | `USE_REAL_LLM=false`（默认）或缺少 API 配置 | `DirectAdapter` 使用离线 Smart Mock，trace 中 `is_mock=true`，`model_name=mock`。 |
| **Real LLM** | `USE_REAL_LLM=true` 且 `OPENAI_COMPAT_BASE_URL`、`OPENAI_COMPAT_API_KEY`、`OPENAI_COMPAT_MODEL` 均非空 | 调用 OpenAI-compatible `/v1/chat/completions`；trace 记录 `provider=openai-compatible`、实际 `model_name`、`is_mock=false`。 |

复制 `.env.example` 为 `.env` 并填写（**不要**把真实密钥提交到 Git）：

```bash
copy .env.example .env
```

**推荐用模块方式运行**（解释器包上下文正确）；亦支持直接运行脚本文件（runner/plot 顶部含 `sys.path` 兼容补丁），见下文。

## 目录结构（核心）

```
data/
  fixtures/             # v0.2 任务素材（按类型分目录）
  tasks/
    task_schema.json
    v1_tasks.jsonl
src/
  adapters/             # direct baseline（mock / real）
  clients/              # OpenAI-compatible HTTP 客户端
  config/               # 环境配置加载
  runners/
  traces/
  scorers/              # rule + quality proxy
  analysis/             # summarize + plot + failure taxonomy
  utils/
outputs/
  runs/ scored_runs/ summaries/ charts/
docs/
  methodology.md  rubric.md  failure_taxonomy.md
scripts/
  gen_v1_tasks.py       # 可选：从脚本再生 JSONL（一般直接用仓库内已生成文件即可）
```

## 如何运行

在**仓库根目录**执行，以便 `data/` 相对路径解析正确。

### 推荐 vs 兼容

| 方式 | 示例 |
|------|------|
| 推荐 | `python -m src.runners.run_single_task ...` |
| 兼容 | `python .\src\runners\run_single_task.py ...` |

更推荐 `python -m`：包导入与 PEP 338 行为一致；兼容方式便于 IDE「运行当前文件」。

### 单条任务（direct）

**Mock：**

```bash
python -m src.runners.run_single_task --task-id v1-qa-faq-005
```

**Real LLM：** 配置好 `.env` 后同上（适配器自动切换）。

### 批量实验（`v1_tasks.jsonl` 全量）

```bash
python -m src.runners.run_experiment --experiment-id my_run
```

兼容：`python .\src\runners\run_experiment.py --experiment-id my_run`

产物：

- `outputs/runs/<id>/traces.jsonl`
- `outputs/scored_runs/<id>/scores.jsonl`（含 `quality_proxy`、`failure_taxonomy`）
- `outputs/summaries/<id>/summary.json`

### 生成 summary（可选单独跑）

```bash
python -m src.analysis.summarize outputs/scored_runs/my_run/scores.jsonl --out outputs/summaries/my_run/summary.json
```

### 生成图表（matplotlib）

在已有 `scores.jsonl` 后：

```bash
python -m src.analysis.plot_summary --scores-jsonl outputs/scored_runs/my_run/scores.jsonl --out-dir outputs/charts/my_run
```

将生成：

- `pass_rate_by_task_type.png`
- `pass_rate_by_difficulty.png`
- `quality_proxy_overview.png`
- `failure_type_distribution.png`

## 关于 “quality proxy”

`quality_proxy` 指标（如 `citation_presence`、`constraint_hit_rate`）只是 **启发式代理信号**，用于概览与排序线索；**不能**替代人工审核、对照答案或 LLM-as-judge 等更严谨评测。详见 `docs/rubric.md`。

## 许可证与数据

样例任务与素材为演示用途；邮箱与域名多为虚构，请勿用于真实投递。
