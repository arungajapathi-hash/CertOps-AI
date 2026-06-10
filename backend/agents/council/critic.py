"""CriticAgent - Synthesizes council votes using reputation weights."""
import json
from typing import Dict

from backend.agents.base_agent import BaseAgent
from backend.database import get_connection
from backend.reputation.engine import ReputationEngine


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__("Critic")
        self.reputation_engine = ReputationEngine()

    async def execute(self, memory: Dict) -> Dict:
        """Execute critic synthesis - weighted vote resolution."""
        self._log("Synthesizing council votes...")

        # Step 1: Collect all council votes
        votes = memory.get("council_votes", {})
        
        if len(votes) < 3:
            self._log("WARNING: Fewer than 3 votes present")
            memory["readiness_verdict"] = "DELAY"
            memory["readiness_confidence"] = 30
            memory["readiness_reasoning"] = "Insufficient council participation for decision"
            self._append_log(memory, "Critic: Insufficient votes for decision")
            return memory

        # Step 2: Load reputation weights
        weights = self.reputation_engine.get_weights()
        
        # Step 3: Calculate weighted confidence per verdict
        verdict_scores = {"READY": 0.0, "NOT_READY": 0.0, "DELAY": 0.0}
        
        for agent_name, vote in votes.items():
            if not isinstance(vote, dict):
                continue
            
            agent_name_lower = agent_name.lower()
            weight = weights.get(agent_name_lower, 0.75)
            confidence = float(vote.get("confidence", 50))
            verdict = vote.get("verdict", "DELAY")
            
            weighted_conf = confidence * weight
            if verdict in verdict_scores:
                verdict_scores[verdict] += weighted_conf

        # Step 4: Apply safety rule - if READY and NOT_READY are close, default to DELAY
        ready_score = verdict_scores["READY"]
        not_ready_score = verdict_scores["NOT_READY"]
        delay_score = verdict_scores["DELAY"]

        calculated_verdict = "DELAY"
        if abs(ready_score - not_ready_score) > 15:
            if ready_score > not_ready_score:
                calculated_verdict = "READY"
            else:
                calculated_verdict = "NOT_READY"
        
        calculated_confidence = max(ready_score, not_ready_score, delay_score) / (sum(weights.values()) * 100 + 0.001) * 100

        # Step 5: Build system prompt
        system_prompt = (
            "You are the Critic — the final decision maker on a certification readiness council. "
            "You have received weighted votes from 5 specialist agents. "
            "Your job is to synthesise their arguments, resolve conflicts, and deliver the final verdict. "
            "Be decisive. Be fair. Protect the learner from premature failure. "
            "Return ONLY valid JSON with no markdown:\n"
            "{"
            '"verdict": "READY|NOT_READY|DELAY", '
            '"confidence": 0-100, '
            '"reasoning": "2-3 sentences", '
            '"key_blocker": "reason if NOT_READY or DELAY, else null", '
            '"recommendation": "actionable next step", '
            '"weighted_votes": {"READY": number, "NOT_READY": number, "DELAY": number}'
            "}"
        )

        # Step 6: Build user prompt with all votes and calculations
        user_prompt = (
            "Council votes received:\n"
            f"{json.dumps(votes, indent=2)}\n\n"
            "Weighted verdict scores:\n"
            f"READY: {ready_score:.1f}\n"
            f"NOT_READY: {not_ready_score:.1f}\n"
            f"DELAY: {delay_score:.1f}\n\n"
            f"Calculated verdict: {calculated_verdict}\n\n"
            "Agent reputation weights:\n"
            f"{json.dumps({k: f'{v:.2f}' for k, v in weights.items()}, indent=2)}\n\n"
            "Safety rule applied: If READY and NOT_READY scores differ by <15 points, verdict defaults to DELAY.\n\n"
            "Now synthesise the council arguments and explain your final decision. "
            "Address any major disagreements between agents. "
            "Provide clear reasoning for the verdict."
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.4)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            
            # Step 7: Store in memory
            memory["readiness_verdict"] = result.get("verdict", calculated_verdict)
            memory["readiness_confidence"] = int(result.get("confidence", 50))
            memory["readiness_reasoning"] = result.get("reasoning", "Council decision synthesized")
            memory["critic_output"] = result
            
            # Step 8: Save prediction to SQLite
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                learner_id = memory.get("learner_id", "unknown")
                certification = memory.get("certification", "unknown")
                verdict = memory["readiness_verdict"]
                confidence = memory["readiness_confidence"]
                
                cursor.execute("""
                    INSERT INTO predictions (learner_id, certification, predicted_outcome, confidence)
                    VALUES (?, ?, ?, ?)
                """, (learner_id, certification, verdict, confidence))
                
                conn.commit()
                conn.close()
            except Exception as e:
                self._log(f"Error saving prediction: {e}")
            
            self._append_log(
                memory,
                f"Critic: FINAL VERDICT {memory['readiness_verdict']} "
                f"({memory['readiness_confidence']}% confidence) — {memory['readiness_reasoning']}"
            )
            
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            memory["readiness_verdict"] = calculated_verdict
            memory["readiness_confidence"] = int(calculated_confidence)
            memory["readiness_reasoning"] = f"Weighted vote synthesis: {calculated_verdict}"
            memory["critic_output"] = {
                "verdict": calculated_verdict,
                "confidence": int(calculated_confidence),
                "reasoning": "Council decision based on weighted voting",
                "key_blocker": None,
                "recommendation": "Review council votes for details",
                "weighted_votes": verdict_scores
            }
            self._append_log(memory, f"Critic: Fallback verdict {calculated_verdict}")

        return memory
