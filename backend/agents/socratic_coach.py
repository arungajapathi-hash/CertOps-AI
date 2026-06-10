from typing import Dict, List

from backend.agents.base_agent import BaseAgent


class SocraticCoach(BaseAgent):
	def __init__(self, name: str = "socratic_coach"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Generating socratic questions (stub)")
		misconceptions: List[str] = memory.get("misconceptions", []) or []
		questions = [
			"What specific concept is blocking your progress?",
			"How would you apply this topic in a real scenario?",
			"What small experiment could you run to test your understanding?",
		]
		memory["misconceptions"] = misconceptions
		memory["socratic_questions"] = questions
		memory = self._append_log(memory, "Socratic questions generated (stub)")
		return memory

