from dataclasses import dataclass

@dataclass(frozen=True)
class TrainingHypothesis:
    failure_type: str
    candidate_methods: tuple[str,...]
    required_evidence: tuple[str,...]
    risks: tuple[str,...]

HYPOTHESES={
"low_diversity":TrainingHypothesis("low_diversity",("diversity-conditioned SFT/RFT","multi-objective preference optimization"),("cross-loop replication","human-validated alternatives","holdout replication"),("irrelevant novelty","appropriateness regression")),
"novel_but_infeasible":TrainingHypothesis("novel_but_infeasible",("tool-grounded trajectory SFT","DPO","process/trajectory reward model","RLVR"),("verified failure","repaired trajectory","harness variants"),("over-conservatism","tool overuse")),
"constraint_omission":TrainingHypothesis("constraint_omission",("constraint-trace SFT","DPO on omission pairs","verifiable-reward RL"),("criterion labels","audited tasks","parallel-item replication"),("constraint parroting","verbosity")),
"tool_use_error":TrainingHypothesis("tool_use_error",("function-call SFT","repaired trajectory SFT","agent RL"),("clear schema","stable environment","correct trajectory"),("unnecessary calls","format overfitting")),
"negative_revision":TrainingHypothesis("negative_revision",("revision preference optimization","reward-model rejection sampling","paired draft-revision SFT"),("draft/revision pairs","criterion regressions","style controls"),("style bias","reward hacking")),
"dynamic_replanning":TrainingHypothesis("dynamic_replanning",("multi-turn trajectory SFT","curriculum learning","agent RL"),("state-change events","valid replans","multiple perturbations"),("cost","limited transfer")),
"memory_misuse":TrainingHypothesis("memory_misuse",("retrieval-routing SFT","memory relevance preference optimization"),("relevance labels","negative transfer","no-memory baseline"),("over-ignoring memory","retrieval overfitting")),
"judge_style_bias":TrainingHypothesis("judge_style_bias",("reward-model recalibration","blinded preference optimization","multi-judge distillation"),("identity-blinded pairs","length controls","order reversal"),("preference instability","new gaming"))}
