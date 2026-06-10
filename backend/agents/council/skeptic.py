from typing import Dict

from backend.agents.base_agent import BaseAgent


class Skeptic(BaseAgent):
	def __init__(self, name: str = "skeptic"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Skeptic casting vote (stub)")
		vote = {"vote": "not_ready", "confidence": 75}
		votes = memory.get("council_votes", {})
		votes[self.name] = vote
		memory["council_votes"] = votes
		memory = self._append_log(memory, f"Skeptic voted: {vote}")
		return memory
