#!/bin/bash
# FastAPI stays internal on 8000 (frontend talks to it via localhost).
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
# Streamlit is the public entry — bind to the platform-assigned $PORT
# (Render/Railway inject this; fall back to 8501 for local Docker).
streamlit run frontend/app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true
wait
