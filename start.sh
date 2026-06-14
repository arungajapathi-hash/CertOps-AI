#!/bin/bash

export PYTHONPATH=/app

# Start FastAPI in background
uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 8000 &

# Start Streamlit on Render assigned port
streamlit run frontend/app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true

wait