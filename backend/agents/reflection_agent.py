"""ReflectionAgent - Self-learning heart of CertOps AI.
Compares predictions vs actual outcomes and updates agent reputation.
"""
import json
import os
from typing import Dict, List

from backend.agents.base_agent import BaseAgent
from backend.reputation.engine import ReputationEngine
from backend import database


class ReflectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReflectionAgent")
        self.reputation = ReputationEngine()

    async def execute(self, memory: Dict) -> Dict:
        """Compare prediction vs actual outcome and update agent reputations."""
        self._log("Running reflection analysis...")

        predicted = memory.get("readiness_verdict", "")
        actual = memory.get("assessment_outcome", "")
        council_votes = memory.get("council_votes", {})
        learner_id = memory.get("learner_id", "unknown")
        certification = memory.get("certification", "unknown")

        if not predicted or not actual:
            self._append_log(memory, "ReflectionAgent: Missing prediction or outcome — skipping")
            return memory

        # Step 1: Map outcomes to comparable values
        prediction_was_correct = (
            (predicted == "READY" and actual == "PASS") or
            (predicted in ["NOT_READY", "DELAY"] and actual == "FAIL")
        )

        # Step 2: Determine which council agents were right
        agents_correct = []
        agents_wrong = []

        for agent_name, vote in council_votes.items():
            if not isinstance(vote, dict):
                continue

            agent_verdict = vote.get("verdict", "DELAY")
            agent_was_correct = (
                (agent_verdict == "READY" and actual == "PASS") or
                (agent_verdict in ["NOT_READY", "DELAY"] and actual == "FAIL")
            )

            if agent_was_correct:
                agents_correct.append(agent_name)
            else:
                agents_wrong.append(agent_name)

            # Update reputation
            self.reputation.update_reputation(agent_name, agent_was_correct)

        # Step 3: Generate reflection analysis via LLM
        system_prompt = (
            "You are a learning system analyst. "
            "Your job is to understand WHY the council prediction "
            "matched or failed to match the actual exam outcome. "
            "Be specific and analytical. "
            "Your insights will improve future predictions. "
            "Return only valid JSON."
        )

        council_summary = {}
        for agent, vote in council_votes.items():
            if isinstance(vote, dict):
                council_summary[agent] = {
                    "verdict": vote.get("verdict", "UNKNOWN"),
                    "confidence": vote.get("confidence", 0),
                    "key_evidence": vote.get("evidence", [""])[0] if vote.get("evidence") else ""
                }

        user_prompt = (
            f"Certification: {certification}\n"
            f"Learner: {learner_id}\n\n"
            f"Council predicted: {predicted}\n"
            f"Actual outcome: {actual}\n"
            f"Prediction correct: {prediction_was_correct}\n\n"
            f"Agents who were RIGHT: {agents_correct}\n"
            f"Agents who were WRONG: {agents_wrong}\n\n"
            f"Council votes summary:\n"
            f"{json.dumps(council_summary, indent=2)}\n\n"
            f"Assessment score: {memory.get('assessment_score', 0):.1f}%\n"
            f"Weak topics identified: {memory.get('weak_topics', [])}\n\n"
            f"Analyse:\n"
            f"1. Why did the prediction succeed or fail?\n"
            f"2. Which agent signals were most valuable?\n"
            f"3. What pattern should the system learn from this?\n"
            f"4. What should change in future evaluations for similar learners?\n\n"
            f"Return JSON:\n"
            f"{{\n"
            f"  'prediction_correct': true/false,\n"
            f"  'analysis': '2-3 sentence analysis',\n"
            f"  'key_learning': 'one specific thing the system learned',\n"
            f"  'most_accurate_agent': 'agent name',\n"
            f"  'least_accurate_agent': 'agent name',\n"
            f"  'pattern_identified': 'pattern for future reference',\n"
            f"  'recommendation_for_system': 'how to improve next time'\n"
            f"}}"
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.4)

        # Step 4: Parse response
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)

            memory["reflection"] = {
                "predicted": predicted,
                "actual": actual,
                "prediction_correct": prediction_was_correct,
                "agents_correct": agents_correct,
                "agents_wrong": agents_wrong,
                "analysis": result.get("analysis", ""),
                "key_learning": result.get("key_learning", ""),
                "pattern": result.get("pattern_identified", "")
            }

        except json.JSONDecodeError:
            self._log("LLM returned non-JSON, using fallback analysis")
            memory["reflection"] = {
                "predicted": predicted,
                "actual": actual,
                "prediction_correct": prediction_was_correct,
                "agents_correct": agents_correct,
                "agents_wrong": agents_wrong,
                "analysis": f"Prediction was {'correct' if prediction_was_correct else 'incorrect'}. "
                           f"{len(agents_correct)} agents were right, {len(agents_wrong)} were wrong.",
                "key_learning": "System needs more data on similar learner profiles.",
                "pattern": "Correlation between weak topics and exam performance."
            }

        # Step 5: Save to SQLite reflections table
        try:
            conn = database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO reflections 
                (learner_id, predicted_outcome, actual_outcome, analysis, 
                 agents_correct, agents_wrong)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                learner_id,
                predicted,
                actual,
                memory["reflection"].get("analysis", ""),
                json.dumps(agents_correct),
                json.dumps(agents_wrong)
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            self._log(f"Error saving reflection: {e}")

        # Step 6: Log updated reputation scores
        new_scores = self.reputation.get_all_scores()
        if new_scores:
            top_agent = max(new_scores, key=lambda x: x.get("accuracy", 0))
            self._append_log(
                memory,
                f"ReflectionAgent: Prediction was {'CORRECT' if prediction_was_correct else 'WRONG'}. "
                f"Agents updated. Top agent: {top_agent.get('agent_name', 'unknown')} "
                f"({top_agent.get('accuracy', 0):.1f}%)"
            )

        return memory

