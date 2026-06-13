"""
Centralized state manager for all Streamlit pages.
Handles all API communication with the FastAPI backend.
"""

import httpx
import streamlit as st

API_BASE = "http://localhost:8000"


def get_api_state() -> dict:
    """Fetch current state from FastAPI backend"""
    try:
        response = httpx.get(f"{API_BASE}/state", timeout=10)
        return response.json()
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")
        return {}


def post_api(endpoint: str, payload: dict) -> dict:
    """POST to FastAPI with error handling"""
    try:
        response = httpx.post(
            f"{API_BASE}/{endpoint}",
            json=payload,
            timeout=120  # LLM calls take time
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API error {response.status_code}: {response.text}")
            return {}
    except httpx.TimeoutException:
        st.error("Request timed out. LLM is taking too long.")
        return {}
    except Exception as e:
        st.error(f"Connection error: {e}")
        return {}


def get_api(endpoint: str) -> dict:
    """GET from FastAPI with error handling"""
    try:
        response = httpx.get(
            f"{API_BASE}/{endpoint}",
            timeout=30
        )
        return response.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return {}


def save_session(payload: dict) -> dict:
    """Store UI session data in backend memory"""
    try:
        response = httpx.post(f"{API_BASE}/session/save", json=payload, timeout=3)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        # Avoid raising Streamlit errors on simple session saves to prevent reruns
        return {}


def load_session(learner_id: str, session_key: str) -> dict:
    try:
        response = httpx.get(f"{API_BASE}/session/load", params={"learner_id": learner_id, "session_key": session_key}, timeout=10)
        if response.status_code == 200:
            return response.json().get("data")
        return None
    except Exception as e:
        st.error(f"Cannot load session: {e}")
        return None


def has_completed_phase(phase: str) -> bool:
    """Check if a phase has been completed"""
    state = get_api_state()
    checks = {
        "learning": bool(state.get("skill_map")),
        "readiness": bool(state.get("readiness_verdict")),
        "assessment": bool(state.get("assessment_outcome")),
        "coaching": bool(state.get("misconceptions")),
        "reflection": bool(state.get("reflection"))
    }
    return checks.get(phase, False)


def show_phase_guard(required_phase: str, message: str):
    """Show warning if required phase not completed"""
    if not has_completed_phase(required_phase):
        st.warning(f"⚠️ {message}")
        st.info("Complete the previous step first.")
        return False
    return True
