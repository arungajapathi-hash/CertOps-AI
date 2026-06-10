from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from backend import database
from backend.memory import SharedMemory
from backend.orchestrator import Orchestrator


class LearnRequest(BaseModel):
    learner_id: str
    role: str
    certification: str
    target_weeks: int

    @validator("certification")
    def check_cert(cls, v):
        """Allow any Microsoft certification — dynamic knowledge plugin handles all."""
        if not v or not isinstance(v, str):
            raise ValueError("certification must be a non-empty string")
        return v.strip().upper()

    @validator("target_weeks")
    def check_weeks(cls, v):
        if not (1 <= v <= 12):
            raise ValueError("target_weeks must be between 1 and 12")
        return v


class LearnerRequest(BaseModel):
    learner_id: str


class ReadinessRequest(BaseModel):
    learner_id: str


class ReflectionRequest(BaseModel):
    learner_id: str
    actual_outcome: str


sessions: Dict[str, SharedMemory] = {}
orchestrator = Orchestrator()


def get_session_memory(learner_id: str) -> SharedMemory:
    if learner_id not in sessions:
        sessions[learner_id] = SharedMemory()
        sessions[learner_id].set("learner_id", learner_id)
    return sessions[learner_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="CertOps AI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/learn")
async def learn(payload: LearnRequest) -> Dict[str, Any]:
    try:
        result = await orchestrator.run_learning_phase(
            learner_id=payload.learner_id,
            role=payload.role,
            certification=payload.certification,
            target_weeks=payload.target_weeks,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/readiness")
async def readiness(payload: ReadinessRequest) -> Dict[str, Any]:
    try:
        result = await orchestrator.run_readiness_phase(
            learner_id=payload.learner_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/assessment")
async def assessment(payload: LearnerRequest) -> Dict[str, Any]:
    memory = get_session_memory(payload.learner_id)
    orchestrator.run_assessment(memory.to_dict())
    return {
        "score": memory.get("assessment_score"),
        "topic_breakdown": memory.get("assessment_breakdown"),
        "outcome": memory.get("assessment_outcome"),
        "questions": memory.get("socratic_questions"),
    }


@app.post("/coaching")
async def coaching(payload: LearnerRequest) -> Dict[str, Any]:
    memory = get_session_memory(payload.learner_id)
    orchestrator.coach_learner(memory.to_dict())
    return {
        "misconceptions": memory.get("misconceptions"),
        "socratic_questions": memory.get("socratic_questions"),
        "remediation": memory.get("recommended_materials"),
    }


@app.post("/reflection")
async def reflection(payload: ReflectionRequest) -> Dict[str, Any]:
    memory = get_session_memory(payload.learner_id)
    memory.set("actual_outcome", payload.actual_outcome)
    orchestrator.reflect_outcome(memory.to_dict())
    return {
        "prediction_accuracy": 0.0,
        "agents_correct": [],
        "agents_wrong": [],
    }


@app.get("/manager")
async def manager() -> Dict[str, Any]:
    orchestrator.manager_overview({})
    return {
        "team_readiness": [],
        "at_risk": [],
        "pass_rate": 0,
        "weak_areas": [],
    }


@app.get("/reputation")
async def reputation() -> Dict[str, Any]:
    conn = database.get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT agent_name, accuracy_score, total_predictions, correct_predictions FROM agent_reputation"
    ).fetchall()
    conn.close()
    agents = [
        {
            "name": row["agent_name"],
            "accuracy": row["accuracy_score"],
            "total": row["total_predictions"],
            "correct": row["correct_predictions"],
        }
        for row in rows
    ]
    return {"agents": agents}


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
