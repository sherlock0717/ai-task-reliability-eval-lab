# AI 任务可靠性评测台
<<<<<<< HEAD

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
=======
把「会说话的 AI」，推进到「可验收的工作流」。

一个面向真实办公任务的本地评测项目。  
我把题目、执行、验收、记录和汇总串成一条可重复运行的流程，用来检查一套 AI 工作方式是否稳定、清楚、可复查。

## 在线展示

- 展示页：<https://sherlock0717.github.io/ai-task-reliability-eval-lab/>
- 仓库地址：<https://github.com/sherlock0717/ai-task-reliability-eval-lab>

---

## 项目简介

很多 AI 演示能展示“会回答”，但进入实际任务后，还需要回答另外几个更具体的问题：

- 能不能按要求完成任务
- 多跑几次以后稳不稳定
- 失败主要出在哪里
- 输出能不能留下清楚的验收记录

这个项目就是围绕这些问题搭起来的一套评测台。  
它使用固定任务集批量运行，统一收集结果，再按规则验收并生成汇总结果与图表，方便复盘和展示。
>>>>>>> cb686f5917b3f2e4aab55e3c0ffd289e642326b5

---

<<<<<<< HEAD
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
=======
## 完成内容

目前已经跑通一条从任务执行到结果汇总的基本闭环，包括：

- 固定任务集批量运行
- 输出结果统一收集
- 基于规则的验收
- 失败情况分类记录
- summary 与图表生成
- GitHub Pages 展示页

当前公开展示中，**direct 基线流程**是完成度最高的一条主线。

---

## 这个项目能看到什么

通过这套流程，可以直接看到：

- 哪类任务更容易稳定通过
- 哪类任务更容易在规则层面出错
- 同一套工作方式在多题场景下有没有明显波动
- 结果文件、日志和图表能不能支撑复查与解释

项目里的分数主要用于描述**任务完成和流程可靠性**，方便比较不同运行结果的表现。

---

## 项目结构

```text
ai-task-reliability-eval-lab/
├─ configs/                 # 配置文件
├─ data/
│  ├─ tasks/                # 任务样本
│  └─ runs/                 # 运行结果
├─ outputs/
│  ├─ summaries/            # 汇总结果
│  └─ figures/              # 图表输出
├─ scripts/                 # 执行、汇总、绘图脚本
├─ docs/                    # 展示页内容
└─ README.md
>>>>>>> cb686f5917b3f2e4aab55e3c0ffd289e642326b5
