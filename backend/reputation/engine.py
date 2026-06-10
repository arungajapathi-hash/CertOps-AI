"""ReputationEngine - Manages agent reputation scores and weights."""
from typing import Dict, List
import sqlite3

from backend.database import get_connection, DEFAULT_AGENTS


class ReputationEngine:
    """Tracks agent reputation (accuracy) and provides weights for Critic synthesis."""

    def get_weights(self) -> Dict[str, float]:
        """
        Get normalized reputation weights for all agents.
        Returns: {agent_name: weight (0.0-1.0)} where weight = accuracy_score / 100
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT agent_name, accuracy_score FROM agent_reputation")
            rows = cursor.fetchall()
            conn.close()
            
            weights = {}
            for row in rows:
                agent_name = row["agent_name"]
                score = float(row["accuracy_score"]) if row["accuracy_score"] else 75.0
                # Normalize to 0-1 range
                weights[agent_name] = score / 100.0
            
            # Ensure all default agents present (fallback to 0.75)
            for agent_name in DEFAULT_AGENTS:
                if agent_name not in weights:
                    weights[agent_name] = 0.75
            
            return weights
        except Exception as e:
            print(f"[ReputationEngine] Error loading weights: {e}, using defaults")
            return {agent: 0.75 for agent in DEFAULT_AGENTS}

    def get_all_scores(self) -> List[Dict]:
        """Get all agent reputation records."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT agent_name, accuracy_score, total_predictions, 
                       correct_predictions, updated_at 
                FROM agent_reputation 
                ORDER BY accuracy_score DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ReputationEngine] Error fetching scores: {e}")
            return []

    def update_reputation(self, agent_name: str, was_correct: bool) -> None:
        """Update agent reputation after prediction."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Fetch current values
            cursor.execute(
                "SELECT total_predictions, correct_predictions FROM agent_reputation WHERE agent_name = ?",
                (agent_name,)
            )
            row = cursor.fetchone()
            
            if row:
                total = int(row["total_predictions"]) + 1
                correct = int(row["correct_predictions"]) + (1 if was_correct else 0)
                accuracy = (correct / total * 100) if total > 0 else 75.0
                
                cursor.execute("""
                    UPDATE agent_reputation 
                    SET total_predictions = ?, correct_predictions = ?, accuracy_score = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE agent_name = ?
                """, (total, correct, accuracy, agent_name))
            else:
                # Insert if not exists
                total = 1
                correct = 1 if was_correct else 0
                accuracy = (correct / total * 100)
                cursor.execute("""
                    INSERT INTO agent_reputation 
                    (agent_name, accuracy_score, total_predictions, correct_predictions)
                    VALUES (?, ?, ?, ?)
                """, (agent_name, accuracy, total, correct))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ReputationEngine] Error updating reputation for {agent_name}: {e}")

    def get_reputation_summary(self) -> Dict:
        """Get formatted reputation summary for display."""
        try:
            scores = self.get_all_scores()
            summary = {}

            for score_record in scores:
                agent_name = score_record["agent_name"]
                total = int(score_record["total_predictions"])
                correct = int(score_record["correct_predictions"])
                accuracy = float(score_record["accuracy_score"])

                # Determine trend based on accuracy score
                if accuracy >= 80:
                    trend = "strong"
                elif accuracy >= 70:
                    trend = "improving"
                else:
                    trend = "needs data"

                summary[agent_name] = {
                    "accuracy": round(accuracy, 1),
                    "total": total,
                    "correct": correct,
                    "trend": trend
                }

            return summary
        except Exception as e:
            print(f"[ReputationEngine] Error generating summary: {e}")
            return {}

    def reset_to_defaults(self) -> bool:
        """Reset all agent reputations to default values (75%)."""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            for agent_name in DEFAULT_AGENTS:
                cursor.execute("""
                    UPDATE agent_reputation
                    SET accuracy_score = 75.0,
                        total_predictions = 0,
                        correct_predictions = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE agent_name = ?
                """, (agent_name,))

            conn.commit()
            conn.close()
            print("[ReputationEngine] Reset all agents to defaults (75%)")
            return True
        except Exception as e:
            print(f"[ReputationEngine] Error resetting to defaults: {e}")
            return False
