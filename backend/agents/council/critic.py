from typing import Dict

from backend.agents.base_agent import BaseAgent


class Critic(BaseAgent):
	def __init__(self, name: str = "critic"):
		super().__init__(name)

	def execute(self, memory: Dict) -> Dict:
		self._log("Critic casting vote (stub)")
		vote = {"vote": "not_ready", "confidence": 60}
		votes = memory.get("council_votes", {})
		votes[self.name] = vote
		memory["council_votes"] = votes
		memory = self._append_log(memory, f"Critic voted: {vote}")
		return memory
