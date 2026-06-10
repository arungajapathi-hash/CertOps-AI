"""SkepticAgent - Finds reasons why the learner will FAIL."""
import json
from typing import Dict

from backend.agents.base_agent import BaseAgent


class SkepticAgent(BaseAgent):
    def __init__(self):
        super().__init__("Skeptic")

    async def execute(self, memory: Dict) -> Dict:
        """Execute skeptic analysis - identify gaps and risks."""
        self._log("Starting skeptic analysis...")

        system_prompt = (
            "You are the Skeptic on a certification readiness council. "
            "Your role is to find every reason WHY this learner WILL FAIL. "
            "Look for gaps, risks, insufficient preparation, weak areas. "
            "You protect the learner from premature exam failure. "
            "Be specific — cite actual numbers and gaps. "
            "Return ONLY valid JSON with no markdown:\n"
            "{"
            '"agent": "Skeptic", '
            '"verdict": "READY|NOT_READY|DELAY", '
            '"confidence": 0-100, '
            '"evidence": ["gap1", "risk1", "weakness1"], '
            '"recommendation": "actionable improvement"'
            "}"
        )

        certification = memory.get("certification", "Unknown")
        practice_score = memory.get("practice_score_avg", 0)
        hours_studied = memory.get("hours_studied", 0)
        weak_topics = memory.get("weak_topics", [])
        skill_map = memory.get("skill_map", [])
        exam_domains = memory.get("exam_domains", [])
        target_weeks = memory.get("target_weeks", 6)

        user_prompt = (
            f"Assess risk factors for {certification}:\n\n"
            f"Practice score: {practice_score}%\n"
            f"Hours studied: {hours_studied}\n"
            f"Weak topics: {weak_topics}\n"
            f"Skills: {len(skill_map)}\n"
            f"Exam domains: {len(exam_domains)}\n"
            f"Target weeks: {target_weeks}\n\n"
            f"Identify GAPS and RISKS:\n"
            f"- Pass threshold is 70%. Is score near this?\n"
            f"- Any weak topics that are high-weight domains?\n"
            f"- Is hours studied below recommended?\n"
            f"- Are there untouched domains?\n"
            f"- Is time running out (weeks << target)?\n\n"
            f"Verdict rules:\n"
            f"- NOT_READY: Multiple high-risk factors\n"
            f"- DELAY: Some risks but fixable\n"
            f"- READY: Only minor risks\n"
            f"Confidence 0-100 based on risk severity.\n"
            f"Evidence: 3 specific risk points with numbers."
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
            result["agent"] = "Skeptic"
            memory["council_votes"]["skeptic"] = result
            
            self._append_log(
                memory,
                f"Skeptic: {result['verdict']} ({result['confidence']}%)"
            )
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            result = {
                "agent": "Skeptic",
                "verdict": "DELAY",
                "confidence": 50,
                "evidence": ["Parse error", "Unable to assess", "Manual review needed"],
                "recommendation": "Address identified gaps"
            }
            memory["council_votes"]["skeptic"] = result
            self._append_log(memory, "Skeptic: Parse error, fallback used")

        return memory
