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


class AssessmentRequest(BaseModel):
    learner_id: str


class SubmitRequest(BaseModel):
    learner_id: str
    answers: Dict[str, str]  # {"1": "A", "2": "C", ...}


class CoachingRequest(BaseModel):
    learner_id: str


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
async def assessment(payload: AssessmentRequest) -> Dict[str, Any]:
    try:
        result = await orchestrator.run_assessment_phase(
            learner_id=payload.learner_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/submit")
async def submit(payload: SubmitRequest) -> Dict[str, Any]:
    try:
        result = await orchestrator.submit_assessment(
            learner_id=payload.learner_id,
            answers=payload.answers
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/coaching")
async def coaching(payload: CoachingRequest) -> Dict[str, Any]:
    mem = orchestrator.memory.to_dict()
    return {
        "misconceptions": mem.get("misconceptions", []),
        "socratic_questions": mem.get("socratic_questions", []),
        "remediation": mem.get("remediation", {}),
    }


@app.post("/reflection")
async def reflection(payload: ReflectionRequest) -> Dict[str, Any]:
    try:
        result = await orchestrator.run_reflection_phase(
            learner_id=payload.learner_id,
            actual_outcome=payload.actual_outcome
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/manager")
async def manager() -> Dict[str, Any]:
    return orchestrator.get_manager_insights()


@app.get("/reputation")
async def reputation() -> Dict[str, Any]:
    return {
        "agents": orchestrator.reputation.get_all_scores(),
        "summary": orchestrator.reputation.get_reputation_summary()
    }


@app.get("/reset-demo")
async def reset_demo() -> Dict[str, str]:
    orchestrator.memory.reset()
    success = orchestrator.reputation.reset_to_defaults()
    return {
        "status": "Demo reset complete" if success else "Reset failed",
        "memory": "cleared",
        "reputation": "reset to defaults"
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
