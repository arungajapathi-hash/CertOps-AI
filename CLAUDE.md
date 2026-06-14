# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```powershell
pip install -r requirements.txt
```

**Run the backend (FastAPI):**
```powershell
uvicorn backend.main:app --reload --port 8000
```

**Run the frontend (Streamlit):**
```powershell
streamlit run frontend/app.py
```

Both must run concurrently. The frontend calls `http://localhost:8000` (hardcoded in `frontend/state.py`).

**Authenticate for Foundry IQ (local dev):**
```powershell
az login
```

**Test Foundry IQ connection:**
```powershell
.\scripts\test_foundry.ps1
```

**Set debug logging:**
```
LOG_LEVEL=DEBUG  # in .env
```

## Architecture

CertOps AI is a multi-agent certification readiness platform. It has two processes:

- **Backend** — FastAPI app (`backend/main.py`) exposing 12 endpoints. All agent orchestration happens here.
- **Frontend** — Single Streamlit file (`frontend/app.py`) communicating with the backend via synchronous `httpx` calls through `frontend/state.py`.

### Request flow

```
Streamlit (app.py)
  → frontend/state.py (httpx GET/POST)
  → FastAPI (main.py)
  → Orchestrator (orchestrator.py)
  → Agents (execute against SharedMemory dict)
  → LLM (Azure OpenAI via BaseAgent._call_llm)
```

### Agent pattern

All 13 agents inherit `BaseAgent` (`backend/agents/base_agent.py`). Every agent:
- Implements `execute(memory: dict) -> dict`
- Makes LLM calls only through `_call_llm()` or `_call_llm_async()` — never directly
- Reads from and writes to the shared memory dict; never calls another agent directly
- Appends progress entries via `_append_log(memory, message)`

LLM calls use `asyncio.to_thread()` so they don't block the event loop during pipeline runs.

### Orchestrator

`backend/orchestrator.py` holds a singleton `Orchestrator` instance with per-learner session isolation (`_bind(learner_id)`). Agents are initialized lazily. The pipeline runs as a background `asyncio.Task` (`/pipeline` starts it; `/pipeline/status` and `/state` are polled for progress). The pipeline pauses after the council phase for the interactive assessment (`interactive_assessment=True`), then resumes via `POST /pipeline/continue`.

### Shared memory

All agent state lives in a single `SharedMemory` dict (see full schema in `PROJECT_CONTEXT.md`). The `/state` endpoint exposes it to the frontend. The schema is frozen — do not add keys without updating `PROJECT_CONTEXT.md`.

### Knowledge retrieval cascade

```
FoundryKnowledgePlugin (Azure AI Foundry RAG)
  → DynamicKnowledgePlugin (MS Learn scraping + LLM)
  → Offline hardcoded guides (AZ-204, AZ-400, DP-203)
```

Controlled by `USE_FOUNDRY_IQ=true/false` in `.env`. Use `backend/plugins/knowledge_router.py` as the single import point — never import a knowledge plugin directly.

### Council flow

Five specialist agents (Optimist, Skeptic, Advocate, Historian, RiskAnalyst) run in parallel via `asyncio.gather`. CriticAgent then synthesises their votes using reputation weights from SQLite. Each council agent must return exactly:
```python
{"agent": str, "verdict": "READY|NOT_READY|DELAY", "confidence": int, "evidence": list[str], "recommendation": str}
```

### Reputation engine

`backend/reputation/engine.py` (not `backend/agents/reputation/`) tracks per-agent accuracy in SQLite. Agents start at 75.0%. After each assessment, ReflectionAgent updates scores. CriticAgent weights council votes by these scores; if the top-verdict margin is < 15%, it outputs DELAY regardless.

### Frontend state machine

`app.py` uses `st.session_state.view` with four states: `landing → analyzing → exam → results`. Navigation is explicit; no auto-advance or backend-driven routing. The sidebar shows deep-dive views (Council Debate, Manager Insights, Agent Reputation, Reasoning Trace) that are read-only.

### Log streaming

`backend/log_buffer.py` captures stdout/stderr into a ring buffer. `/ws/logs` WebSocket streams entries in real time. `/logs` (GET) returns the last N buffered lines. The frontend console drawer uses the WebSocket.

## Key constraints

- **4 SQLite tables only** — `agent_reputation`, `predictions`, `assessment_results`, `reflections`
- **No direct agent-to-agent calls** — only shared memory
- **13 agents maximum** — do not add more without updating `PROJECT_CONTEXT.md`
- **Tech stack is frozen** — do not add new packages without updating `PROJECT_CONTEXT.md`
- **No hardcoded LLM responses** — every agent must make a real LLM call
- **Shared memory schema is frozen** — see `PROJECT_CONTEXT.md` for the full dict

## Environment variables

```env
AZURE_OPENAI_ENDPOINT=https://<resource>.services.ai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=certops-agent
DATABASE_PATH=./certops.db
USE_FOUNDRY_IQ=true
```

Copy `.env.example` to `.env`. Local dev auth for Foundry IQ uses `az login` (DefaultAzureCredential). Production uses `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID`.
