"""One-off generator for data/tasks/v1_tasks.jsonl (v0.2)."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    tasks = [
        {
            "task_id": "v1-extract-jd-001",
            "task_name": "JD 关键条款抽取（投递前核对）",
            "task_type": "extraction",
            "difficulty": "easy",
            "scenario": "求职投递",
            "description": "从真实风格的 JD 中抽取候选人决策所需的关键条款（地点、年限、硬技能、投递方式等）。",
            "input_files": [
                {"path": "data/fixtures/extraction/jd_backend_senior.txt", "role": "primary_source"}
            ],
            "prompt": (
                "阅读附件 JD，仅依据正文抽取信息。用中文分行输出：岗位名称、地点与远程政策、年限与学历硬门槛、"
                "必备技术栈、加分项、薪资福利（如有）、申请方式。若某项未出现，写“未提及”。"
            ),
            "constraints": ["不得编造附件中不存在的公司或链接。", "不要输出泛泛的职业规划建议。"],
            "must_include": ["学历", "申请方式", "未提及"],
            "must_not_do": ["玩具", "hello world"],
            "expected_output_type": "text",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["远程政策是否保留“首月全周现场”等细节。"],
            "human_check_points": ["与原始 JD 核对数字与技能名称。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "recruiting",
                "dataset_version": "v0.2",
                "scene": "jd_extract",
            },
        },
        {
            "task_id": "v1-extract-match-002",
            "task_name": "简历与 JD 匹配要点（差距/风险）",
            "task_type": "extraction",
            "difficulty": "medium",
            "scenario": "招聘筛选 / 候选人自检",
            "description": "同时阅读 JD 与候选人简历片段，输出匹配点、差距点与需要澄清的风险点。",
            "input_files": [
                {"path": "data/fixtures/extraction/jd_product_manager.txt", "role": "jd"},
                {"path": "data/fixtures/extraction/resume_pm_candidate.txt", "role": "resume"},
            ],
            "prompt": (
                "基于两份材料，输出四段：匹配点、差距点、风险点、建议澄清问题（各用条目列出）。"
                "要求可审计：每条都说明依据来自哪份材料。"
            ),
            "constraints": ["不得推断候选人未写明的经历细节。", "不得输出歧视性用语。"],
            "must_include": ["匹配", "风险", "材料"],
            "must_not_do": ["请咨询律师", "包过"],
            "expected_output_type": "markdown",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["是否把“出差频率”与候选人期望城市对齐比较。"],
            "human_check_points": ["招聘负责人最终判断是否约面。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "recruiting",
                "dataset_version": "v0.2",
                "scene": "jd_resume_match",
            },
        },
        {
            "task_id": "v1-extract-meeting-003",
            "task_name": "会议纪要结构化（结论/待办/未决）",
            "task_type": "extraction",
            "difficulty": "medium",
            "scenario": "会议运营",
            "description": "把语音转写风格的会议纪要整理为可执行的结构化摘要。",
            "input_files": [
                {"path": "data/fixtures/extraction/meeting_notes_raw.txt", "role": "primary_source"}
            ],
            "prompt": "整理为三部分：结论清单、行动项（负责人/截止时间若可识别则写出）、未决事项。使用中文，条目化。",
            "constraints": ["不得把“未决”写成已经结论。", "不要添加会议中未出现的系统指标承诺。"],
            "must_include": ["负责人", "截止", "未决"],
            "must_not_do": ["免责声明", "最终解释权"],
            "expected_output_type": "markdown",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["日期是否统一为可理解格式。"],
            "human_check_points": ["与会者复核负责人与截止时间。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "meeting",
                "dataset_version": "v0.2",
                "scene": "minutes",
            },
        },
        {
            "task_id": "v1-extract-feedback-004",
            "task_name": "多客户反馈信息汇总（共性/优先级线索）",
            "task_type": "extraction",
            "difficulty": "hard",
            "scenario": "产品/CS 内部复盘",
            "description": "从多客户反馈中抽取共性主题，并给出可作为优先级讨论线索的要点。",
            "input_files": [
                {"path": "data/fixtures/extraction/customer_feedback_q1.txt", "role": "primary_source"}
            ],
            "prompt": (
                "输出：共性主题（>=2 条）、差异化诉求、与权限/审计相关的问题、"
                "建议产品团队在评审会上追问的两个问题。"
            ),
            "constraints": ["不得虚构客户行业细节。", "不要直接承诺交付日期。"],
            "must_include": ["共性", "审计", "追问"],
            "must_not_do": ["保证", "确定上线"],
            "expected_output_type": "text",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["是否区分“共性”与“单点问题”。"],
            "human_check_points": ["产品经理结合路线图判断是否立项。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "product",
                "dataset_version": "v0.2",
                "scene": "customer_feedback",
            },
        },
        {
            "task_id": "v1-rewrite-bullets-001",
            "task_name": "项目经历改写为简历要点",
            "task_type": "rewrite",
            "difficulty": "easy",
            "scenario": "求职材料",
            "description": "把口语化项目说明改写为可放入简历的要点条目。",
            "input_files": [
                {"path": "data/fixtures/rewrite/project_data_platform.txt", "role": "primary_source"}
            ],
            "prompt": (
                "改写成 3 条简历要点：每条一行；强动词开头；可量化则量化，无法量化则保守表述；"
                "不要编造输入没有的数据。"
            ),
            "constraints": ["总字数建议不超过 260 字。", "不要使用表情符号。"],
            "must_include": ["数据平台", "条"],
            "must_not_do": ["😀", "hello world"],
            "expected_output_type": "markdown",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["每条是否独立可读。"],
            "human_check_points": ["候选人与真实经历核对。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "career",
                "dataset_version": "v0.2",
                "scene": "resume_rewrite",
            },
        },
        {
            "task_id": "v1-rewrite-email-002",
            "task_name": "求职邮件润色（岗位导向）",
            "task_type": "rewrite",
            "difficulty": "medium",
            "scenario": "求职沟通",
            "description": "把粗糙邮件草稿改写成更专业、岗位导向的版本（仍基于给定信息）。",
            "input_files": [
                {"path": "data/fixtures/rewrite/email_coarse_request.txt", "role": "primary_source"}
            ],
            "prompt": (
                "输出邮件正文（中文）：包含问候、动机、与岗位相关的两条能力证据、礼貌结尾；"
                "不要虚构经历；可假设“附件已附简历”。"
            ),
            "constraints": ["不要夸大候选人未给出的数据。", "不要人身攻击或贬低前雇主。"],
            "must_include": ["岗位", "附件", "分析"],
            "must_not_do": ["亲", "包过"],
            "expected_output_type": "text",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["证据是否来自草稿中可支持的内容。"],
            "human_check_points": ["候选人最终发送前人工校对。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "career",
                "dataset_version": "v0.2",
                "scene": "email_rewrite",
            },
        },
        {
            "task_id": "v1-rewrite-jd-summary-003",
            "task_name": "岗位定向摘要（内部转发版）",
            "task_type": "rewrite",
            "difficulty": "medium",
            "scenario": "招聘协作",
            "description": "将 JD 改写为适合内部群转发的短摘要，突出岗位画像与硬约束。",
            "input_files": [
                {"path": "data/fixtures/rewrite/jd_ai_engineer.txt", "role": "primary_source"}
            ],
            "prompt": (
                "输出 120–180 字中文摘要：包含岗位目标、关键能力、现场/地点约束、"
                "你不应夸大的边界（例如不要承诺资源）。用条目或短段落均可。"
            ),
            "constraints": ["不得添加 JD 未提到的产品指标。", "不要替公司承诺薪资上限之外的内容。"],
            "must_include": ["北京", "交付", "评测"],
            "must_not_do": ["SaaS", "颠覆式"],
            "expected_output_type": "markdown",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["是否强调“可落地/评测”而非空泛大模型口号。"],
            "human_check_points": ["用人经理确认摘要是否误导。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "recruiting",
                "dataset_version": "v0.2",
                "scene": "jd_internal_summary",
            },
        },
        {
            "task_id": "v1-rewrite-announce-004",
            "task_name": "内部公告润色（清晰约束）",
            "task_type": "rewrite",
            "difficulty": "hard",
            "scenario": "对内沟通",
            "description": "把简短草稿扩写为清晰、可执行的公告：目的、适用范围、时间节点与咨询入口。",
            "input_files": [
                {"path": "data/fixtures/rewrite/internal_announcement_draft.md", "role": "primary_source"}
            ],
            "prompt": (
                "用中文输出公告正文：标题 + 背景 + 新规则要点 + 生效时间（若材料不足写“待行政确认”）"
                "+ 咨询方式（可占位）。"
            ),
            "constraints": ["不得编造具体日期数字，除非草稿已给出。", "语气正式但不官僚。"],
            "must_include": ["试点", "行政", "反馈"],
            "must_not_do": ["保密协议", "最终解释权归我"],
            "expected_output_type": "markdown",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["是否有明确行动指引。"],
            "human_check_points": ["行政与法务确认日期与条款。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "internal_comms",
                "dataset_version": "v0.2",
                "scene": "announcement",
            },
        },
        {
            "task_id": "v1-qa-leave-004",
            "task_name": "年假规则结构化问答（JSON）",
            "task_type": "qa",
            "difficulty": "easy",
            "scenario": "HR 制度",
            "description": "依据给定规则片段回答结构化问题，输出 JSON 供下游系统使用。",
            "input_files": [
                {"path": "data/fixtures/qa/leave_policy_snippet.md", "role": "primary_source"}
            ],
            "prompt": (
                "规则见附件。问题：一名员工在当年 7 月 1 日首次入职本公司，当年可享受多少天带薪年假？"
                "只输出 JSON：answer_days（数字）、rule_refs（字符串数组）、reasoning（简短中文）。"
            ),
            "constraints": ["只依据附件规则，不讨论劳动法一般知识。", "不要输出 Markdown 围栏。"],
            "must_include": ["answer_days", "rule_refs", "reasoning"],
            "must_not_do": ["仅供参考", "hello world"],
            "expected_output_type": "json",
            "expected_output_schema": {
                "type": "object",
                "required": ["answer_days", "rule_refs", "reasoning"],
            },
            "reference_answer": {
                "answer_days": 0,
                "rule_refs": ["R1"],
                "reasoning": "当年入职不满一年，不享受带薪年假。",
            },
            "evaluation_hints": ["answer_days 应为 0。"],
            "human_check_points": ["与完整员工手册核对例外条款。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "hr_policy",
                "dataset_version": "v0.2",
                "scene": "policy_json",
                "proxy_expect_citation": False,
            },
        },
        {
            "task_id": "v1-qa-faq-005",
            "task_name": "FAQ 引用式回答（标注信息来源）",
            "task_type": "qa",
            "difficulty": "medium",
            "scenario": "IT 支持",
            "description": "回答用户问题并引用 FAQ 编号，便于审计与复盘。",
            "input_files": [{"path": "data/fixtures/qa/faq_it_support.md", "role": "primary_source"}],
            "prompt": (
                "用户问题：我在外地出差，笔记本开机密码忘了，最省时的处理路径是什么？"
                "请用中文回答，并在正文中引用对应 FAQ 编号（如 [FAQ-1]）。不要编造附件之外的流程。"
            ),
            "constraints": ["不得承诺 10 分钟内完成重置，除非材料支持。", "不要引导用户绕过安全流程。"],
            "must_include": ["FAQ", "VPN", "身份"],
            "must_not_do": ["一定", "保证成功"],
            "expected_output_type": "markdown",
            "expected_output_schema": None,
            "reference_answer": None,
            "evaluation_hints": ["是否引用到身份核验/到场相关条款。"],
            "human_check_points": ["IT 服务台确认最新流程。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "it_support",
                "dataset_version": "v0.2",
                "scene": "faq_citation",
                "proxy_expect_citation": True,
            },
        },
        {
            "task_id": "v1-qa-expense-006",
            "task_name": "报销规则适用性判断（JSON）",
            "task_type": "qa",
            "difficulty": "medium",
            "scenario": "财务制度",
            "description": "判断给定行为主要命中哪条规则，并输出 JSON。",
            "input_files": [{"path": "data/fixtures/qa/expense_policy.md", "role": "primary_source"}],
            "prompt": (
                "情境：员工因紧急会议通过非指定平台预订酒店并索取报销。依据附件规则，输出 JSON："
                "rule_id（如 E1/E2/E3）、confidence（0-1 数字）、reasoning（中文）。不要输出多余字段。"
            ),
            "constraints": ["不得引用附件不存在的条款编号。", "不要给出违法避税建议。"],
            "must_include": ["rule_id", "confidence", "reasoning"],
            "must_not_do": ["避税", "找票"],
            "expected_output_type": "json",
            "expected_output_schema": {
                "type": "object",
                "required": ["rule_id", "confidence", "reasoning"],
            },
            "reference_answer": None,
            "evaluation_hints": ["更可能命中非指定平台预订相关条款。"],
            "human_check_points": ["财务复核材料与审批链。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "finance_policy",
                "dataset_version": "v0.2",
                "scene": "expense_json",
                "proxy_expect_citation": False,
            },
        },
        {
            "task_id": "v1-qa-remote-007",
            "task_name": "远程办公政策要点问答（JSON）",
            "task_type": "qa",
            "difficulty": "hard",
            "scenario": "员工手册",
            "description": "综合政策片段回答问题并输出 JSON，用于表单或工单系统。",
            "input_files": [
                {"path": "data/fixtures/qa/handbook_remote_work.md", "role": "primary_source"}
            ],
            "prompt": (
                "问题：若某岗位需要高频客户现场交付，是否默认适用“每周至少一天现场协作”的通用规则？"
                "依据附件，输出 JSON：answer_summary（字符串）、clauses（字符串数组，引用 H1/H2/H3）、"
                "caveats（字符串，说明材料未覆盖的信息）。"
            ),
            "constraints": ["不要臆测公司未给出的岗位清单。", "不要给出法律结论，仅作制度信息整理。"],
            "must_include": ["answer_summary", "clauses", "caveats", "H1"],
            "must_not_do": ["劳动仲裁", "违法"],
            "expected_output_type": "json",
            "expected_output_schema": {
                "type": "object",
                "required": ["answer_summary", "clauses", "caveats"],
            },
            "reference_answer": None,
            "evaluation_hints": ["是否提到客户现场交付岗位可能不适用的例外语境。"],
            "human_check_points": ["HR 确认岗位是否属于例外清单。"],
            "metadata": {
                "locale": "zh-CN",
                "domain": "hr_policy",
                "dataset_version": "v0.2",
                "scene": "handbook_json",
                "proxy_expect_citation": False,
            },
        },
    ]

    path = Path(__file__).resolve().parents[1] / "data" / "tasks" / "v1_tasks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("wrote", path, "tasks=", len(tasks))


if __name__ == "__main__":
    main()
