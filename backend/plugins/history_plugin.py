import sqlite3
from typing import Dict
from semantic_kernel.functions import kernel_function

from backend import database


class HistoryPlugin:
    def __init__(self):
        pass

    @kernel_function(name="find_similar_learners", description="Find past learners with similar profile from database")
    def find_similar_learners(self, certification: str, score: float, hours: float) -> str:
        conn = database.get_connection()
        cursor = conn.cursor()
        low = score - 10
        high = score + 10
        rows = cursor.execute(
            "SELECT learner_id, score, topic_breakdown, outcome FROM assessment_results WHERE certification = ? AND score BETWEEN ? AND ? LIMIT 5",
            (certification, low, high),
        ).fetchall()
        conn.close()
        if not rows:
            return "No similar historical learners found. Using synthetic baseline data."
        lines = []
        for r in rows:
            learner = r["learner_id"]
            sc = r["score"]
            outcome = r["outcome"]
            # hours are not stored in this table; put placeholder
            lines.append(f"Learner {learner}: Score {sc}%, Hours {hours}, Outcome: {outcome}")
        return "\n".join(lines)
