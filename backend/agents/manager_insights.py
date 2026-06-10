"""ManagerInsights - Provides team-level certification readiness analytics."""
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from backend.agents.base_agent import BaseAgent
from backend import database


class ManagerInsightsAgent(BaseAgent):
    def __init__(self):
        super().__init__("ManagerInsights")
        self.db_path = os.getenv("DATABASE_PATH", "./certops.db")

    async def execute(self, memory: Dict) -> Dict:
        """Return memory unchanged — manager reads from DB directly."""
        return memory

    def get_insights(self) -> Dict[str, Any]:
        """Generate comprehensive team insights from SQLite data."""
        try:
            conn = database.get_connection()
            cursor = conn.cursor()

            # Query 1 — Overall stats by certification
            cursor.execute("""
                SELECT 
                    certification,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN outcome='PASS' THEN 1 ELSE 0 END) as passes,
                    AVG(score) as avg_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score
                FROM assessment_results
                GROUP BY certification
            """)
            cert_stats = cursor.fetchall()

            # Query 2 — At risk learners
            cursor.execute("""
                SELECT learner_id, certification, score, outcome
                FROM assessment_results
                WHERE score < 70
                ORDER BY score ASC
                LIMIT 10
            """)
            at_risk = cursor.fetchall()

            # Query 3 — Recent activity
            cursor.execute("""
                SELECT learner_id, certification, score, outcome, created_at
                FROM assessment_results
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent = cursor.fetchall()

            # Query 4 — Get all topic breakdowns for aggregation
            cursor.execute("""
                SELECT topic_breakdown FROM assessment_results
                WHERE topic_breakdown IS NOT NULL AND topic_breakdown != ''
            """)
            topic_rows = cursor.fetchall()

            conn.close()

            # Build team readiness by certification
            team_readiness = []
            total_passes = 0
            total_attempts = 0

            for row in cert_stats:
                cert = row["certification"]
                attempts = row["total_attempts"]
                passes = row["passes"] or 0
                avg_score = row["avg_score"] or 0

                pass_rate = (passes / attempts * 100) if attempts > 0 else 0
                total_passes += passes
                total_attempts += attempts

                # Determine status
                if pass_rate >= 70:
                    status = "On Track"
                elif pass_rate >= 50:
                    status = "At Risk"
                else:
                    status = "Critical"

                team_readiness.append({
                    "certification": cert,
                    "total_attempts": attempts,
                    "passes": passes,
                    "pass_rate": round(pass_rate, 1),
                    "avg_score": round(avg_score, 1),
                    "status": status
                })

            # Sort by status severity
            status_order = {"Critical": 0, "At Risk": 1, "On Track": 2}
            team_readiness.sort(key=lambda x: status_order.get(x["status"], 3))

            # Build at risk learners list
            at_risk_learners = []
            for row in at_risk:
                at_risk_learners.append({
                    "learner_id": row["learner_id"],
                    "certification": row["certification"],
                    "score": round(row["score"], 1),
                    "outcome": row["outcome"],
                    "action": "View Details"
                })

            # Build recent activity
            recent_activity = []
            for row in recent:
                recent_activity.append({
                    "learner_id": row["learner_id"],
                    "certification": row["certification"],
                    "score": round(row["score"], 1),
                    "outcome": row["outcome"],
                    "timestamp": row["created_at"]
                })

            # Aggregate topic weaknesses
            topic_scores = {}
            topic_totals = {}

            for row in topic_rows:
                try:
                    breakdown = json.loads(row["topic_breakdown"])
                    for topic, data in breakdown.items():
                        score = data.get("score", 0)
                        if topic not in topic_scores:
                            topic_scores[topic] = []
                        topic_scores[topic].append(score)
                except (json.JSONDecodeError, TypeError):
                    continue

            # Calculate average score per topic
            topic_avg = {}
            for topic, scores in topic_scores.items():
                topic_avg[topic] = sum(scores) / len(scores) if scores else 0

            # Sort by lowest score (weakest topics first)
            sorted_topics = sorted(topic_avg.items(), key=lambda x: x[1])
            top_weak_areas = [t[0] for t in sorted_topics[:3]]

            # Calculate overall pass rate
            overall_pass_rate = (total_passes / total_attempts * 100) if total_attempts > 0 else 0

            return {
                "team_readiness": team_readiness,
                "at_risk_learners": at_risk_learners,
                "recent_activity": recent_activity,
                "top_weak_areas": top_weak_areas,
                "overall_pass_rate": round(overall_pass_rate, 1),
                "total_assessments": total_attempts,
                "insights_generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"[ManagerInsights] Error generating insights: {e}")
            return {
                "team_readiness": [],
                "at_risk_learners": [],
                "recent_activity": [],
                "top_weak_areas": [],
                "overall_pass_rate": 0,
                "total_assessments": 0,
                "insights_generated_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }

