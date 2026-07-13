from __future__ import annotations

DIAGNOSTIC_MAP = {
    "category_collapse": {"data": "跨类别高质量候选与同质负例", "methods": ["conditional SFT", "multi-objective DPO"]},
    "novel_but_infeasible": {"data": "不可行轨迹、工具证据和修正轨迹", "methods": ["trajectory SFT", "DPO", "process/outcome reward modeling"]},
    "constraint_omission": {"data": "约束解析和漏项对照轨迹", "methods": ["SFT", "DPO", "verifiable-reward RL"]},
    "tool_evidence_ignored": {"data": "证据进入／未进入决策的成对轨迹", "methods": ["trajectory SFT", "process reward model", "agent RL"]},
    "critic_overtrust": {"data": "正确拒绝错误反馈的轨迹", "methods": ["critic SFT", "preference optimization", "separate reward model"]},
    "memory_misuse": {"data": "相关与无关记忆对、负迁移案例", "methods": ["retrieval-router SFT", "memory preference optimization"]},
    "over_iteration": {"data": "已达标继续改写与正确停止的偏好对", "methods": ["DPO", "terminal reward modeling"]},
}


def suggest(failure_tag: str) -> dict[str, object] | None:
    """Return a candidate training hypothesis; this does not validate training effects."""
    return DIAGNOSTIC_MAP.get(failure_tag)
