"""OptimistAgent - Finds reasons why the learner CAN succeed."""
import json
from typing import Dict

from backend.agents.base_agent import BaseAgent


class OptimistAgent(BaseAgent):
    def __init__(self):
        super().__init__("Optimist")

    async def execute(self, memory: Dict) -> Dict:
        """Execute optimist analysis - find positive signals."""
        self._log("Starting optimist analysis...")

        system_prompt = (
            "You are the Optimist on a certification readiness council. "
            "Your role is to find every reason WHY this learner CAN pass. "
            "Look for positive trends, strengths, and encouraging signals. "
            "Be specific — cite actual numbers from their data. "
            "Return ONLY valid JSON with no markdown:\n"
            "{"
            '"agent": "Optimist", '
            '"verdict": "READY|NOT_READY|DELAY", '
            '"confidence": 0-100, '
            '"evidence": ["point1", "point2", "point3"], '
            '"recommendation": "one sentence"'
            "}"
        )

        certification = memory.get("certification", "Unknown")
        practice_score = memory.get("practice_score_avg", 0)
        hours_studied = memory.get("hours_studied", 0)
        weak_topics = memory.get("weak_topics", [])
        skill_map = memory.get("skill_map", [])
        work_signals = memory.get("work_signals", {})
        target_weeks = memory.get("target_weeks", 6)
        
        study_plan = memory.get("study_plan", {})
        weeks_completed = len([w for w in study_plan.values() if isinstance(w, dict)])

        user_prompt = (
            f"Assess positive readiness signals for {certification}:\n\n"
            f"Practice score: {practice_score}%\n"
            f"Hours studied: {hours_studied}\n"
            f"Skills identified: {len(skill_map)}\n"
            f"Weeks completed: {weeks_completed}/{target_weeks}\n"
            f"Weak topics: {len(weak_topics)}\n"
            f"Workload risk: {work_signals.get('workload_risk', 'unknown')}\n\n"
            f"Find POSITIVE signals:\n"
            f"- Is practice score 60%+?\n"
            f"- Has learner invested hours?\n"
            f"- Is skills coverage 70%+?\n"
            f"- Is workload manageable?\n\n"
            f"Verdict rules:\n"
            f"- READY: score ≥70% AND hours adequate\n"
            f"- NOT_READY: score <70% OR major gaps\n"
            f"- DELAY: insufficient data\n"
            f"Confidence 0-100 based on signal strength.\n"
            f"Evidence: 3 specific positive points with numbers."
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
            result["agent"] = "Optimist"
            memory["council_votes"]["optimist"] = result
            
            self._append_log(
                memory,
                f"Optimist: {result['verdict']} ({result['confidence']}%)"
            )
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            result = {
                "agent": "Optimist",
                "verdict": "DELAY",
                "confidence": 50,
                "evidence": ["Parse error", "Recommend manual review", "Check logs"],
                "recommendation": "Continue studying"
            }
            memory["council_votes"]["optimist"] = result
            self._append_log(memory, "Optimist: Parse error, fallback used")

        return memory

