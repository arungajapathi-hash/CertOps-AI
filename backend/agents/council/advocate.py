"""AdvocateAgent - Assesses practical constraints and workload."""
import json
from typing import Dict

from backend.agents.base_agent import BaseAgent


class AdvocateAgent(BaseAgent):
    def __init__(self):
        super().__init__("Advocate")

    async def execute(self, memory: Dict) -> Dict:
        """Execute advocate analysis - focus on practical constraints."""
        self._log("Starting advocate analysis...")

        system_prompt = (
            "You are the Advocate on a certification readiness council. "
            "Your role is to assess PRACTICAL CONSTRAINTS affecting readiness. "
            "Focus on: workload, stress, meeting load, time availability, personal capacity. "
            "A learner might know the material but fail due to exhaustion. "
            "Be specific — cite actual workload numbers. "
            "Return ONLY valid JSON with no markdown:\n"
            "{"
            '"agent": "Advocate", '
            '"verdict": "READY|NOT_READY|DELAY", '
            '"confidence": 0-100, '
            '"evidence": ["constraint1", "availability1", "capacity1"], '
            '"recommendation": "practical adjustment"'
            "}"
        )

        work_signals = memory.get("work_signals", {})
        meeting_hours = work_signals.get("meeting_hours_per_week", 0)
        focus_hours = work_signals.get("focus_hours_per_week", 0)
        workload_risk = work_signals.get("workload_risk", "unknown")
        certification = memory.get("certification", "Unknown")
        target_weeks = memory.get("target_weeks", 6)

        user_prompt = (
            f"Assess practical constraints for {certification} (target: {target_weeks} weeks):\n\n"
            f"Work signals:\n"
            f"- Meeting hours/week: {meeting_hours}\n"
            f"- Focus hours/week: {focus_hours}\n"
            f"- Workload risk: {workload_risk}\n\n"
            f"Assess PRACTICAL READINESS:\n"
            f"- Is learner in high-meeting period? (>20 hrs/week = RED FLAG)\n"
            f"- Available focus time for studying? (<10 hrs/week = INSUFFICIENT)\n"
            f"- Can learner maintain study pace through exam?\n"
            f"- Is there risk of burnout or stress failure?\n\n"
            f"Verdict rules:\n"
            f"- NOT_READY: Excessive workload conflicts with exam prep\n"
            f"- DELAY: Should wait for lower workload period\n"
            f"- READY: Workload is manageable with focus time\n"
            f"Confidence 0-100 based on workload feasibility.\n"
            f"Evidence: 3 specific practical constraints."
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
            result["agent"] = "Advocate"
            memory["council_votes"]["advocate"] = result
            
            self._append_log(
                memory,
                f"Advocate: {result['verdict']} ({result['confidence']}%)"
            )
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            result = {
                "agent": "Advocate",
                "verdict": "DELAY",
                "confidence": 50,
                "evidence": ["Parse error", "Unable to assess workload", "Manual review"],
                "recommendation": "Reassess workload context"
            }
            memory["council_votes"]["advocate"] = result
            self._append_log(memory, "Advocate: Parse error, fallback used")

        return memory
