from typing import Dict

from backend.agents.base_agent import BaseAgent


class ReflectionAgent(BaseAgent):
	def __init__(self, name: str = "reflection_agent"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Reflecting on outcomes (stub)")
		# Simple reflection collects predicted vs actual if available
		predicted = memory.get("predicted_outcome")
		actual = memory.get("actual_outcome")
		analysis = "No actual outcome provided." if not actual else f"Predicted: {predicted}, Actual: {actual}"
		memory["reflection"] = {"predicted": predicted, "actual": actual, "analysis": analysis}
		memory = self._append_log(memory, "Reflection recorded (stub)")
		return memory

