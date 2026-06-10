from typing import Dict

from backend.agents.base_agent import BaseAgent


class AssessmentAgent(BaseAgent):
	def __init__(self, name: str = "assessment_agent"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Running assessment (stub)")
		# Simple heuristic stub: use practice_score_avg as assessment
		score = float(memory.get("practice_score_avg", 0))
		breakdown = {"overall": score}
		outcome = "Pass" if score >= 70 else "Fail"
		memory["assessment_score"] = score
		memory["assessment_breakdown"] = breakdown
		memory["assessment_outcome"] = outcome
		memory = self._append_log(memory, f"Assessment completed: {outcome} ({score})")
		return memory

