# CertOps AI Architecture

CertOps AI is organized as a lightweight Python service layer with a Streamlit frontend.

- backend/
  - database.py: SQLite initialization and reputation storage.
  - memory.py: Shared memory structure for learner sessions.
  - orchestrator.py: Multi-agent orchestration and stubbed endpoint flow.
  - agents/: Agent abstractions and council roles.
  - main.py: FastAPI application with REST endpoints and startup lifecycle.

- frontend/
  - app.py: Streamlit navigation pages for learners, readiness council, coaching, manager insights, reputation, and trace.

- data/
  - synthetic/: Pre-built certification, learner, and work signal datasets.
  - knowledge/: Synthetic study guides for each certification path.

The project is designed for rapid testing, with a pluggable backend that can evolve into a real multi-agent certification readiness platform.
