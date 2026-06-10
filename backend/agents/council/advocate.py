from typing import Dict

from backend.agents.base_agent import BaseAgent


class Advocate(BaseAgent):
	def __init__(self, name: str = "advocate"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Advocate casting vote (stub)")
		vote = {"vote": "ready", "confidence": 80}
		votes = memory.get("council_votes", {})
		votes[self.name] = vote
		memory["council_votes"] = votes
		memory = self._append_log(memory, f"Advocate voted: {vote}")
		return memory
