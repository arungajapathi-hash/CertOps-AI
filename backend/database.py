import os
import sqlite3

DATABASE_PATH = os.getenv("DATABASE_PATH", "./certops.db")
DEFAULT_AGENTS = ["optimist", "skeptic", "advocate", "historian", "risk_analyst"]


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_reputation (
            agent_name TEXT PRIMARY KEY,
            accuracy_score REAL DEFAULT 75.0,
            total_predictions INTEGER DEFAULT 0,
            correct_predictions INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT,
            certification TEXT,
            predicted_outcome TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT,
            certification TEXT,
            score REAL,
            topic_breakdown TEXT,
            outcome TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reflections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT,
            predicted_outcome TEXT,
            actual_outcome TEXT,
            analysis TEXT,
            agents_correct TEXT,
            agents_wrong TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    for agent_name in DEFAULT_AGENTS:
        cursor.execute(
            "INSERT OR IGNORE INTO agent_reputation (agent_name) VALUES (?)",
            (agent_name,),
        )

    conn.commit()
    conn.close()


init_db()
