"""SocraticCoach - Diagnoses misconceptions via guided questions."""
import json
from typing import Dict, List

from backend.agents.base_agent import BaseAgent


class SocraticCoach(BaseAgent):
    def __init__(self):
        super().__init__("SocraticCoach")

    async def execute(self, memory: Dict) -> Dict:
        """Diagnose misconceptions and generate Socratic questions."""

        # Only triggered on FAIL
        if memory.get("assessment_outcome") != "FAIL":
            self._append_log(memory, "SocraticCoach: Not triggered — learner passed")
            return memory

        self._log("Diagnosing misconceptions via Socratic method...")

        wrong_questions = memory.get("wrong_questions", [])
        weak_topics = memory.get("weak_topics", [])
        breakdown = memory.get("assessment_breakdown", {})
        certification = memory.get("certification", "Unknown")
        score = memory.get("assessment_score", 0)
        last_answers = memory.get("last_answers", {})

        if not wrong_questions:
            self._log("No wrong questions to analyze")
            memory["misconceptions"] = ["No specific misconceptions identified"]
            memory["socratic_questions"] = []
            memory["remediation"] = {}
            return memory

        # Build wrong answers data
        wrong_data = []
        for q in wrong_questions[:5]:  # Analyze top 5 wrong answers
            q_id = str(q.get("id", ""))
            wrong_data.append({
                "question": q.get("question", ""),
                "their_answer": last_answers.get(q_id, "Unknown"),
                "correct_answer": q.get("correct_answer", ""),
                "explanation": q.get("explanation", ""),
                "topic": q.get("topic", "General")
            })

        system_prompt = (
            "You are a Socratic learning coach specialising in Microsoft certifications. "
            "Your method: never give answers directly. "
            "Ask guided questions that lead the learner to discover their own misconceptions. "
            "Identify the ROOT misconception behind wrong answers — not just the surface mistake. "
            "Be encouraging but rigorous. "
            "Return only valid JSON."
        )

        user_prompt = (
            f"A learner failed their {certification} assessment.\n\n"
            f"Score: {score:.1f}%\n\n"
            f"Questions they got wrong:\n"
            f"{json.dumps(wrong_data, indent=2)}\n\n"
            f"Topic breakdown (scores by topic):\n"
            f"{json.dumps({t: s.get('score', 0) for t, s in breakdown.items()}, indent=2)}\n\n"
            f"Identify the root misconception behind their failures. "
            f"Then generate 3 Socratic questions that will help them discover the correct understanding themselves.\n\n"
            f"Do NOT reveal the answer in the questions. "
            f"Make questions thought-provoking and specific.\n\n"
            f"Return JSON:\n"
            f"{{\n"
            f"  'root_misconception': 'what they fundamentally misunderstood',\n"
            f"  'affected_topics': ['topic1', 'topic2'],\n"
            f"  'socratic_questions': [\n"
            f"    {{\n"
            f"      'question': 'thought-provoking question',\n"
            f"      'hint': 'subtle hint if they are stuck',\n"
            f"      'leads_to': 'what understanding this reveals'\n"
            f"    }}\n"
            f"  ],\n"
            f"  'remediation': {{\n"
            f"    'focus_areas': ['specific area 1', 'specific area 2'],\n"
            f"    'study_approach': 'how to study this differently',\n"
            f"    'estimated_hours': 3,\n"
            f"    'confidence_message': 'encouraging message'\n"
            f"  }}\n"
            f"}}"
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.5)

        # Parse response
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)

            memory["misconceptions"] = [result.get("root_misconception", "Unknown misconception")]
            memory["socratic_questions"] = result.get("socratic_questions", [])
            memory["remediation"] = result.get("remediation", {})

            self._append_log(
                memory,
                f"SocraticCoach: Diagnosed misconception — {result.get('root_misconception', 'Unknown')[:50]}"
            )

        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")

            # Fallback content
            memory["misconceptions"] = ["Fundamental understanding gap in core concepts"]
            memory["socratic_questions"] = [
                {
                    "question": "What is the core principle that connects these topics you missed?",
                    "hint": "Think about how these services interact.",
                    "leads_to": "Understanding of system architecture"
                },
                {
                    "question": "If you were designing this system from scratch, what would be your first consideration?",
                    "hint": "Start with the requirements.",
                    "leads_to": "Requirements-driven thinking"
                },
                {
                    "question": "What assumption led you to choose the wrong answer?",
                    "hint": "Re-examine the fundamental concepts.",
                    "leads_to": "Identifying conceptual gaps"
                }
            ]
            memory["remediation"] = {
                "focus_areas": weak_topics[:2] if weak_topics else ["Core concepts"],
                "study_approach": "Review fundamentals and practice with hands-on exercises",
                "estimated_hours": 5,
                "confidence_message": "You can master this with focused practice on the fundamentals."
            }

            self._append_log(memory, "SocraticCoach: Using fallback diagnosis")

        return memory

