# AI Task Reliability Eval Lab

## 简介

**AI 任务可靠性评测台** 是一个偏研究与工程演示向的本地实验项目：在贴近真实办公/知识工作的任务样本上，比较不同 **AI workflow policy**（工作流策略）的**基础可靠性**（能否稳定跑通、满足预设硬规则、可追溯），**而不是**做通用大模型排行榜，也**不是**在单轮实验里给出最终业务质量定论。

## 评测口径（对外说明）

摘要中的「通过 / 未通过」主要指 **规则检查**（结构、锚点短语、禁用短语、JSON 可解析等），**不等同于**语义质量已充分验证；**quality proxy** 仅为代理指标，**failure taxonomy** 为规则型初版映射。更完整的质量判断需要人工复核与更强评测协议（见 `docs/rubric.md`）。

## 亮点摘要

- **可复现实验闭环**：读取任务 JSONL → 执行候选策略 → 写入 trace（JSONL）→ 规则评分 + **quality proxy** + **failure taxonomy** → 导出 summary 与图表。
- **双模式可运行**：默认 **Mock** 无需密钥；配置 `.env` 后可接 **OpenAI-compatible** 真实模型（如 DeepSeek 兼容接口）。
- **任务集 v0.2**：12 条样本，覆盖 **extraction / rewrite / qa**，素材为可读 `data/fixtures/` 文本。
- **静态展示页**：`site/showcase/` 提供面向访客的 GitHub Pages 友好页面；表格与结论文案已区分**规则层 / 执行层 / 代理指标**，避免把通过率写成最终质量结论。

## 当前实验产物（示例：v0_2_deepseek）

一次真实跑批结果已保存在仓库中（若你克隆后需要复现，可重新跑 `run_experiment` 覆盖）。该批次的要点是：**规则层未出现结构性失败**（在预设硬规则意义下），属于 workflow 可靠性的**基础验证**，而非“全部成功完成”式的语义结论。

- 汇总：`outputs/summaries/v0_2_deepseek/summary.json`
- 图表：`outputs/charts/v0_2_deepseek/*.png`
- 文字解读（含口径说明）：`docs/results_v0_2_deepseek.md`

## 展示页（GitHub Pages）

- **源码目录**：`site/showcase/`（`index.html` + `style.css` + `script.js` + `assets/`）
- **托管占位**：在 GitHub 仓库 **Settings → Pages** 中，通常可将构建产物发布到 **`gh-pages` 分支根目录**，或使用 **GitHub Actions** 将 `site/showcase/` 部署到 Pages。若仅启用 “Branch /docs folder”，可将展示页内容同步到 `docs/`（根目录）再启用（按你偏好的工作流二选一即可）。
- **建议公开访问 URL 占位**：`https://<your-username>.github.io/<repo-name>/`（启用 Pages 后替换为实际地址并写回 README 与本页链接）。

### 项目截图占位

> 建议在展示页就绪后，截取浏览器全屏或 Hero 区，保存为 `docs/img/showcase-hero.png`（或同类路径），并在 README 本段下方插入：  
> `![Showcase](docs/img/showcase-hero.png)`  
> （当前仓库不强制包含图片二进制，避免体积与版权困扰。）

---

## v0.2 范围（技术）

- **任务**：`data/tasks/v1_tasks.jsonl` 共 **12** 条；结构见 `data/tasks/task_schema.json`。
- **候选策略**：当前完整跑批主要为 **direct** baseline；retrieve / planexec / humangate 在架构中预留。
- **评分**：规则评分 + `quality_proxy`（**不是**最终语义评测；见 `docs/rubric.md`）。
- **归因**：规则型 failure taxonomy（见 `docs/failure_taxonomy.md`）。
- **产出**：`outputs/runs/`、`outputs/scored_runs/`、`outputs/summaries/`、`outputs/charts/`。
- **刻意不做**：复杂 SPA 前端、数据库、通用评测 SaaS。

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
| **Mock** | `USE_REAL_LLM=false`（默认）或缺少 API 配置 | `DirectAdapter` 使用离线 Smart Mock，trace 中 `is_mock=true`。 |
| **Real LLM** | `USE_REAL_LLM=true` 且 `OPENAI_COMPAT_*` 均非空 | 调用 OpenAI-compatible `/v1/chat/completions`；trace 记录 provider / model / `is_mock=false`。 |

复制 `.env.example` 为 `.env` 并填写（**不要**提交真实密钥）：

```bash
copy .env.example .env
```

**推荐用模块方式运行**（包上下文正确）；亦支持直接运行 `.py`（runner 含 `sys.path` 兼容补丁）。

## 目录结构（核心）

```
data/
  fixtures/             # v0.2 任务素材
  tasks/                # task_schema.json, v1_tasks.jsonl
src/
  adapters/ clients/ config/
  runners/ traces/ scorers/ analysis/ utils/
outputs/                # 本地实验产物（大文件建议 .gitignore）
docs/                   # 方法论、rubric、失败归因、实验结果摘要
site/showcase/          # 静态展示页（GitHub Pages）
scripts/ gen_v1_tasks.py
```

## 如何运行

在**仓库根目录**执行。

### 推荐 vs 兼容

| 方式 | 示例 |
|------|------|
| 推荐 | `python -m src.runners.run_single_task ...` |
| 兼容 | `python .\src\runners\run_single_task.py ...` |

### 单条任务（direct）

**Mock：**

```bash
python -m src.runners.run_single_task --task-id v1-qa-faq-005
```

**Real LLM：** 配置好 `.env` 后同上。

### 批量实验

```bash
python -m src.runners.run_experiment --experiment-id my_run
```

### 生成 summary 与图表

```bash
python -m src.analysis.summarize outputs/scored_runs/my_run/scores.jsonl --out outputs/summaries/my_run/summary.json
python -m src.analysis.plot_summary --scores-jsonl outputs/scored_runs/my_run/scores.jsonl --out-dir outputs/charts/my_run
```

### 展示页本地预览

```bash
cd site/showcase
python -m http.server 8000
```

浏览器访问 `http://localhost:8000/`（直接双击打开 `index.html` 可能因浏览器安全策略无法 `fetch` JSON，故推荐本地 HTTP 服务）。

## 关于 quality proxy

`quality_proxy` 只是**启发式代理信号**，不能替代人工审核、对照答案或更严谨评测。详见 `docs/rubric.md`。

## 许可证与数据

样例任务与素材为演示用途；邮箱与域名多为虚构，请勿用于真实投递。
