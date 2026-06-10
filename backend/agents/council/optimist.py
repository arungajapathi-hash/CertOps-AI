from typing import Dict

from backend.agents.base_agent import BaseAgent


class Optimist(BaseAgent):
	def __init__(self, name: str = "optimist"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Optimist casting vote (stub)")
		vote = {"vote": "ready", "confidence": 85}
		votes = memory.get("council_votes", {})
		votes[self.name] = vote
		memory["council_votes"] = votes
		memory = self._append_log(memory, f"Optimist voted: {vote}")
		return memory

