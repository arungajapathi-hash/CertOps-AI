"""HistorianAgent - Finds patterns from past learners."""
import json
from typing import Dict

from backend.agents.base_agent import BaseAgent
from backend.plugins.history_plugin import HistoryPlugin


class HistorianAgent(BaseAgent):
    def __init__(self):
        super().__init__("Historian")
        self.history_plugin = HistoryPlugin()

    async def execute(self, memory: Dict) -> Dict:
        """Execute historian analysis - compare to similar past learners."""
        self._log("Starting historian analysis...")

        system_prompt = (
            "You are the Historian on a certification readiness council. "
            "Your role is to find patterns from PAST LEARNERS with similar profiles. "
            "Compare this learner to historical outcomes. "
            "Be specific about what past learners' success/failure patterns suggest. "
            "Return ONLY valid JSON with no markdown:\n"
            "{"
            '"agent": "Historian", '
            '"verdict": "READY|NOT_READY|DELAY", '
            '"confidence": 0-100, '
            '"evidence": ["pattern1", "comparison1", "precedent1"], '
            '"recommendation": "action based on history"'
            "}"
        )

        certification = memory.get("certification", "Unknown")
        practice_score = memory.get("practice_score_avg", 0)
        hours_studied = memory.get("hours_studied", 0)

        # Query similar learners from history
        similar_learners = self.history_plugin.find_similar_learners(
            certification=certification,
            score=practice_score,
            hours=hours_studied
        )

        user_prompt = (
            f"Historical patterns for {certification}:\n\n"
            f"Current learner:\n"
            f"- Practice score: {practice_score}%\n"
            f"- Hours studied: {hours_studied}\n\n"
            f"Similar past learners:\n"
            f"{json.dumps(similar_learners, indent=2)}\n\n"
            f"Analyze patterns:\n"
            f"- Did learners with similar scores pass or fail?\n"
            f"- What determined success/failure (score? hours? other factors)?\n"
            f"- What is the pass rate for this score range?\n"
            f"- Any concerning patterns for this certification?\n\n"
            f"Verdict rules:\n"
            f"- READY: Historical precedent shows similar learners succeeded\n"
            f"- NOT_READY: Similar learners failed, high-risk pattern\n"
            f"- DELAY: Mixed historical results, insufficient pattern\n"
            f"Confidence 0-100 based on pattern clarity and sample size.\n"
            f"Evidence: 3 specific historical patterns or precedents."
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            result["agent"] = "Historian"
            memory["council_votes"]["historian"] = result
            
            self._append_log(
                memory,
                f"Historian: {result['verdict']} ({result['confidence']}%)"
            )
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            result = {
                "agent": "Historian",
                "verdict": "DELAY",
                "confidence": 50,
                "evidence": ["Insufficient historical data", "Parse error", "Low sample size"],
                "recommendation": "Gather more historical data"
            }
            memory["council_votes"]["historian"] = result
            self._append_log(memory, "Historian: Parse error, fallback used")

        return memory
