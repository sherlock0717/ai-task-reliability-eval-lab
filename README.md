# AI 任务可靠性评测台

把 AI 输出放进可重复流程里检查，观察任务交付是否稳定、清楚、可复查。

在线展示页：https://sherlock0717.github.io/ai-task-reliability-eval-lab/

## 项目简介

这个项目用一组真实风格的办公 / 知识任务，检查 AI 工作流在基础交付层面的可靠性。当前样本覆盖信息抽取、文档改写和规则问答三类任务，并保留题目、运行记录、规则检查、结果汇总和静态展示页。

当前公开跑通的是 `direct` baseline：模型直接接收题目并输出答案，随后进入统一的记录与检查流程。`retrieve`、`planexec`、`humangate` 等工作流仍是架构预留，尚未作为完整对照实验发布。

## 当前完成内容

- `data/tasks/v1_tasks.jsonl`：12 道真实风格任务样本。
- `data/fixtures/`：任务使用的输入材料。
- `src/runners/`：单题运行与批量实验入口。
- `src/scorers/`：基础规则评分与 `quality_proxy` 辅助指标。
- `src/traces/`：运行记录结构。
- `outputs/summaries/v0_2_deepseek/summary.json`：v0.2 direct 跑批汇总。
- `site/showcase/` 与 `docs/`：公开展示页与 GitHub Pages 静态副本。

## 当前结果怎么看

v0.2 这轮共有 12 道题，在当前规则口径下基础检查全部通过。这个结果说明 direct 流程在这组样本上可以稳定生成可解析、结构合规、显性约束未失败的输出。

它不等同于最终业务质量结论。事实正确性、口径一致性、合规风险和对外发布质量仍需要人工复核或更严格的评测协议。

## 项目结构

```text
configs/                # candidate 与 experiment 配置
data/
  fixtures/             # 任务输入材料
  tasks/                # task_schema.json, v1_tasks.jsonl
docs/                   # GitHub Pages 使用的静态展示页与文档
outputs/                # 运行记录、评分结果、summary 与图表
site/showcase/          # 展示页主源
src/
  adapters/             # direct adapter
  analysis/             # summary、图表与失败归因脚本
  clients/              # OpenAI-compatible client
  runners/              # 单题与批量运行入口
  scorers/              # 规则评分与辅助指标
  traces/               # trace schema 与 recorder
scripts/                # 任务生成脚本
```

## 最简运行方式

安装依赖：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

运行单条任务：

```bash
python -m src.runners.run_single_task --task-id v1-qa-faq-005
```

运行一批任务：

```bash
python -m src.runners.run_experiment --experiment-id my_run
```

生成 summary 与图表：

```bash
python -m src.analysis.summarize outputs/scored_runs/my_run/scores.jsonl --out outputs/summaries/my_run/summary.json
python -m src.analysis.plot_summary --scores-jsonl outputs/scored_runs/my_run/scores.jsonl --out-dir outputs/charts/my_run
```

本地预览展示页：

```bash
cd site/showcase
python -m http.server 8000
```

浏览器访问 `http://localhost:8000/`。

## 下一步

- 扩充样本量与任务类型。
- 补齐多工作流对照实验。
- 引入人工评审或更严格的事实正确性检查。
- 细化失败归因，让复盘能定位到更具体的流程问题。

样例任务与素材用于演示；邮箱、域名和业务材料均按公开展示需要处理，请勿直接用于真实投递或业务决策。
