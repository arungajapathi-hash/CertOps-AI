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


class PipelineRequest(BaseModel):
    learner_id: str
    role: str
    certification: str
    target_weeks: int = 6


class AdaptiveRequest(BaseModel):
    learner_id: str
    max_iterations: int = 3


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
    print("[Startup] Orchestrator initialized — singleton instance ready")
    print("[Startup] Shared memory active — persists across all requests")
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


@app.get("/state")
async def get_state() -> Dict[str, Any]:
    """Returns current shared memory — used by all pages"""
    mem = orchestrator.memory.to_dict()
    return {
        "has_data": bool(mem.get("learner_id")),
        "learner_id": mem.get("learner_id", ""),
        "certification": mem.get("certification", ""),
        "role": mem.get("role", ""),
        "target_weeks": mem.get("target_weeks", 0),
        "skill_map": mem.get("skill_map", []),
        "study_plan": mem.get("study_plan", {}),
        "work_signals": mem.get("work_signals", {}),
        "council_votes": mem.get("council_votes", {}),
        "readiness_verdict": mem.get("readiness_verdict", ""),
        "readiness_confidence": mem.get("readiness_confidence", 0),
        "readiness_reasoning": mem.get("readiness_reasoning", ""),
        "assessment_score": mem.get("assessment_score", 0),
        "assessment_outcome": mem.get("assessment_outcome", ""),
        "assessment_questions": mem.get("assessment_questions", []),
        "misconceptions": mem.get("misconceptions", []),
        "socratic_questions": mem.get("socratic_questions", []),
        "remediation": mem.get("remediation", {}),
        "reflection": mem.get("reflection", {}),
        "session_log": mem.get("session_log", []),
        "knowledge_source": mem.get("knowledge_source", ""),
        "citations": mem.get("citations", []),
        "adaptations": mem.get("adaptations", [])
    }


@app.post("/pipeline")
async def run_pipeline(request: PipelineRequest) -> Dict[str, Any]:
    """
    Runs the complete automated pipeline.
    Returns consolidated report.
    """
    try:
        result = await orchestrator.run_full_pipeline(
            learner_id=request.learner_id,
            role=request.role,
            certification=request.certification,
            target_weeks=request.target_weeks
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/pipeline/status")
async def pipeline_status() -> Dict[str, Any]:
    """Returns current pipeline progress from memory"""
    mem = orchestrator.memory.to_dict()
    
    phases_complete = {
        "learning": bool(mem.get("skill_map")),
        "council": bool(mem.get("readiness_verdict")),
        "assessment": bool(mem.get("assessment_outcome")),
        "coaching": bool(mem.get("misconceptions")),
        "reflection": bool(mem.get("reflection"))
    }
    
    completed = sum(phases_complete.values())
    total = len(phases_complete)
    
    return {
        "phases": phases_complete,
        "progress_pct": (completed / total) * 100,
        "current_phase": next(
            (p for p, done in phases_complete.items() 
             if not done), "complete"
        ),
        "adaptations_made": len(mem.get("adaptations", [])),
        "is_complete": completed == total
    }


@app.post("/adaptive")
async def adaptive_loop(request: AdaptiveRequest) -> Dict[str, Any]:
    """
    Run adaptive learning loop that iterates assessment until
    learner passes or max iterations reached.
    
    Each iteration:
    1. Run assessment
    2. If PASS → stop, return results
    3. If FAIL → run Socratic coach, adapt learning plan, retry
    """
    try:
        result = await orchestrator.run_adaptive_loop(
            learner_id=request.learner_id,
            max_iterations=request.max_iterations
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
