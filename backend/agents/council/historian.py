from typing import Dict

from backend.agents.base_agent import BaseAgent


class Historian(BaseAgent):
	def __init__(self, name: str = "historian"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Historian casting vote (stub)")
		vote = {"vote": "ready", "confidence": 70}
		votes = memory.get("council_votes", {})
		votes[self.name] = vote
		memory["council_votes"] = votes
		memory = self._append_log(memory, f"Historian voted: {vote}")
		return memory
