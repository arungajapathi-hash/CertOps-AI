"""
CertOps AI — Premium SaaS Dashboard
Single-pipeline automated certification readiness platform.
Design: Linear/Vercel-inspired dark mode with glass morphism, gradients, animations.
"""

import time
import json
import html
import logging
from collections import OrderedDict
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from frontend.state import get_api_state, post_api, get_api, save_session, load_session

logger = logging.getLogger("certops.ui")

st.set_page_config(
    page_title="CertOps AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DS = {
    "primary": "#4f8ef7",
    "secondary": "#a855f7",
    "success": "#00c896",
    "danger": "#ff4757",
    "warning": "#ffa502",
    "bg_card": "rgba(255,255,255,0.04)",
    "border": "rgba(255,255,255,0.1)",
    "text_secondary": "#8b8b9e",
    "glass": "rgba(255,255,255,0.04)",
}


def render_stat_card(icon: str, label: str, value: str, trend: str = "", trend_positive: bool = True, color: str = DS["primary"]):
    trend_color = DS["success"] if trend_positive else DS["danger"]
    trend_arrow = "↑" if trend_positive else "↓"
    trend_html = f"""
    <div style='font-size: 12px; color: {trend_color}; margin-top: 8px; font-weight: 600;'>
      {trend_arrow} {trend}
    </div>""" if trend else ""
    return f"""
    <div style='
      background: {DS['glass']};
      border: 1px solid {DS['border']};
      border-radius: 16px;
      padding: 20px;
      position: relative;
      overflow: hidden;
    '>
      <div style='
        position: absolute; top: -20px; right: -20px;
        width: 80px; height: 80px;
        background: {color}15;
        border-radius: 50%;
      '></div>
      <div style='font-size: 24px; margin-bottom: 8px;'>{icon}</div>
      <div style='font-size: 28px; font-weight: 900; color: white; margin-bottom: 4px;'>{value}</div>
      <div style='font-size: 12px; color: {DS['text_secondary']}; text-transform: uppercase; letter-spacing: 1px;'>{label}</div>
      {trend_html}
    </div>"""


def render_progress_strip(current_step: int):
    steps = [
        ("1", "Learning Plan", "📚"),
        ("2", "Council Verdict", "⚖️"),
        ("3", "Mock Exam", "📝"),
        ("4", "Results", "🎯")
    ]
    cols = st.columns(len(steps))
    for i, (num, label, icon) in enumerate(steps):
        with cols[i]:
            is_done = i < current_step
            is_active = i == current_step
            color = "#00c896" if is_done else "#4f8ef7" if is_active else "#555566"
            bg = color if is_done or is_active else "transparent"
            text_color = "white" if is_done or is_active else color
            st.markdown(f"""
            <div style='text-align:center; opacity: {1 if is_done or is_active else 0.55};'>
              <div style='
                width:40px; height:40px;
                border-radius:50%;
                background:{bg};
                border:2px solid {color};
                display:flex; align-items:center; justify-content:center;
                margin:0 auto 6px auto;
                font-size:16px;
                color:{text_color};
              '>{'✓' if is_done else icon}</div>
              <div style='font-size:11px; color:{color}; font-weight:600;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown(f"""
    <div style='
      height:2px;
      background: linear-gradient(90deg, #00c896 0%, #00c896 {(current_step/3)*100}%, #333 {(current_step/3)*100}%, #333 100%);
      margin: -28px 5% 20px 5%;
      z-index: -1;
    '></div>
    """, unsafe_allow_html=True)


def get_url_params() -> dict:
    params = getattr(st, "query_params", {}) or {}
    return {k: v[0] for k, v in params.items() if v}


def update_url_params(learner_id: str = None, view: str = None):
    desired = {}
    if learner_id:
        desired["learner_id"] = learner_id
    if view:
        desired["view"] = view
    current = get_url_params()
    if current != desired:
        try:
            st.experimental_set_query_params(**desired)
        except AttributeError:
            # Fallback for Streamlit versions using query_params only
            if hasattr(st, "query_params"):
                st.query_params.update(desired)


def get_ui_session_payload() -> dict:
    return {
        "view": st.session_state.get("view", "landing"),
        "form_learner_id": st.session_state.get("form_learner_id", ""),
        "form_certification": st.session_state.get("form_certification", ""),
        "form_role": st.session_state.get("form_role", ""),
        "form_weeks": st.session_state.get("form_weeks", 6),
        "pipeline_result": st.session_state.get("pipeline_result"),
        "questions": st.session_state.get("questions"),
        "exam": st.session_state.get("exam"),
        "final_result": st.session_state.get("final_result")
    }


def save_ui_session():
    learner_id = st.session_state.get("form_learner_id") or get_url_params().get("learner_id")
    if not learner_id:
        return
    save_session({
        "learner_id": learner_id,
        "session_key": "ui_state",
        "data": get_ui_session_payload()
    })


def restore_ui_session():
    params = get_url_params()
    learner_id = params.get("learner_id")
    if not learner_id:
        return
    saved = load_session(learner_id, "ui_state")
    if not saved or not isinstance(saved, dict):
        return
    for key, value in saved.items():
        st.session_state[key] = value
    st.session_state.view = saved.get("view", st.session_state.get("view", "landing"))
    update_url_params(learner_id, st.session_state.view)


def navigate_to(view: str):
    st.session_state.view = view
    save_ui_session()
    update_url_params(st.session_state.get("form_learner_id", get_url_params().get("learner_id", "")), view)
    st.rerun()


def render_global_css():
    st.markdown(f"""
    <style>
      .main {{ background: #0a0a11; }}
      .stApp {{ background: #0a0a11; }}
      .input-card {{
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 32px;
        max-width: 720px;
        margin: 0 auto 40px auto;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
      }}
      .input-card:hover {{ border-color: rgba(79,142,247,0.4); }}
      .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #4f8ef7, #a855f7) !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 20px rgba(79,142,247,0.35) !important;
      }}
      .exam-topic {{
        background: rgba(79,142,247,0.12);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 12px;
        color: #4f8ef7;
      }}
      /* --- Agent intelligence showcase (landing) --- */
      .ai-badge {{
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(79,142,247,0.12);
        border: 1px solid rgba(79,142,247,0.3);
        color: #9cc2ff; font-size: 13px; font-weight: 600;
        padding: 6px 14px; border-radius: 999px; margin-bottom: 18px;
      }}
      .ai-badge .dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: #00c896; box-shadow: 0 0 0 0 rgba(0,200,150,0.6);
        animation: aipulse 1.8s infinite;
      }}
      @keyframes aipulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(0,200,150,0.6); }}
        70% {{ box-shadow: 0 0 0 8px rgba(0,200,150,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(0,200,150,0); }}
      }}
      .agent-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px; margin: 8px 0 28px 0;
      }}
      .agent-card {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-top: 2px solid var(--accent, #4f8ef7);
        border-radius: 14px; padding: 14px 16px;
        transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
      }}
      .agent-card:hover {{
        transform: translateY(-3px);
        border-color: var(--accent, #4f8ef7);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
      }}
      .agent-card .ac-icon {{ font-size: 22px; }}
      .agent-card .ac-name {{ font-size: 14px; font-weight: 700; color: #f0f0f0; margin-top: 6px; }}
      .agent-card .ac-role {{ font-size: 12px; color: #8b8b9e; margin-top: 3px; line-height: 1.4; }}
      .principle-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px; margin: 4px 0 30px 0;
      }}
      .principle-card {{
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 18px 20px;
      }}
      .principle-card .pc-title {{ font-size: 15px; font-weight: 700; color: #f0f0f0; }}
      .principle-card .pc-desc {{ font-size: 13px; color: #9a9aae; margin-top: 6px; line-height: 1.5; }}
      .section-eyebrow {{
        font-size: 12px; font-weight: 700; letter-spacing: 1.5px;
        text-transform: uppercase; color: #6f7290; margin: 8px 0 12px 0;
      }}
      /* --- Unified sidebar --- */
      [data-testid="stSidebar"] {{
        background: #07070d;
        border-right: 1px solid rgba(255,255,255,0.06);
      }}
      .sb-brand {{ padding: 6px 0 2px 0; }}
      .sb-brand .sb-logo {{
        font-size: 22px; font-weight: 900;
        background: linear-gradient(135deg, #4f8ef7, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
      }}
      .sb-brand .sb-sub {{ font-size: 11px; color: #8b8b9e; margin-top: 2px; letter-spacing:.3px; }}
      .sb-label {{
        font-size: 11px; font-weight: 700; letter-spacing: 1.4px;
        text-transform: uppercase; color: #6f7290; margin: 18px 0 10px 0;
      }}
      .sb-step {{
        display: flex; align-items: flex-start; gap: 10px;
        padding: 7px 0; position: relative;
      }}
      .sb-step .sb-rail {{
        width: 20px; display:flex; flex-direction:column; align-items:center;
      }}
      .sb-step .sb-dot {{
        width: 18px; height: 18px; border-radius: 50%;
        display:flex; align-items:center; justify-content:center;
        font-size: 10px; font-weight: 700; flex-shrink: 0;
        border: 2px solid rgba(255,255,255,0.15); color: #6f7290;
      }}
      .sb-step .sb-line {{ width: 2px; flex: 1; min-height: 14px; background: rgba(255,255,255,0.08); margin: 2px 0; }}
      .sb-step.done .sb-dot {{ background: #00c896; border-color:#00c896; color:#07070d; }}
      .sb-step.done .sb-line {{ background: #00c896; }}
      .sb-step.active .sb-dot {{
        background: #4f8ef7; border-color:#4f8ef7; color:white;
        box-shadow: 0 0 0 4px rgba(79,142,247,0.2);
      }}
      .sb-step .sb-text {{ padding-top: 0px; }}
      .sb-step .sb-name {{ font-size: 13px; font-weight: 600; color: #6f7290; }}
      .sb-step.done .sb-name {{ color: #c7c7d4; }}
      .sb-step.active .sb-name {{ color: #f0f0f0; }}
      .sb-step .sb-hint {{ font-size: 11px; color: #56586f; margin-top: 1px; }}
      .sb-meta {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 12px 14px; margin: 4px 0;
      }}
      .sb-meta .sb-row {{ display:flex; justify-content:space-between; font-size:12px; padding:3px 0; }}
      .sb-meta .sb-k {{ color:#8b8b9e; }}
      .sb-meta .sb-v {{ color:#e8e8f0; font-weight:600; }}
      .sb-health {{
        display:flex; align-items:center; gap:8px; font-size:12px;
        padding: 8px 12px; border-radius: 10px; font-weight:600;
      }}
      .sb-health .hdot {{ width:8px; height:8px; border-radius:50%; }}
      .sb-health.ok {{ background: rgba(0,200,150,0.1); color:#00c896; }}
      .sb-health.ok .hdot {{ background:#00c896; }}
      .sb-health.down {{ background: rgba(255,71,87,0.1); color:#ff4757; }}
      .sb-health.down .hdot {{ background:#ff4757; }}
    </style>
    """, unsafe_allow_html=True)


def render_logo():
    st.sidebar.markdown("""
    <div class="sb-brand">
      <div class="sb-logo">🎓 CertOps AI</div>
      <div class="sb-sub">Self-learning certification intelligence</div>
    </div>
    """, unsafe_allow_html=True)


def render_loading_header(text: str):
    return f"""
    <div style='padding: 18px; background: rgba(255,255,255,0.05); border-radius: 18px; margin-bottom: 20px;'>
      <div style='font-size: 26px; font-weight: 900; color: white;'>{text}</div>
    </div>
    """


def render_error_state(message: str, reset_fn):
    st.error(message)
    if st.button("Retry", type="primary", use_container_width=True):
        reset_fn()
        st.rerun()


def render_phase1_2_summary(result: dict):
    assessment = result.get("phases", {}).get("assessment", {})
    verdict = result.get("phases", {}).get("readiness", {}).get("verdict") or result.get("readiness_verdict") or "Pending"
    confidence = result.get("phases", {}).get("readiness", {}).get("confidence") or result.get("readiness_confidence") or 0
    score = assessment.get("score", 0)
    st.markdown(f"## 📚 Learning Plan & Council Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(render_stat_card("📚", "Questions", str(len(result.get('phases', {}).get('assessment', {}).get('questions', []))), color="#4f8ef7"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_stat_card("⚖️", "Council Verdict", verdict, f"{confidence:.0f}%", color="#a855f7"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_stat_card("📝", "Assessment Prep", f"{score:.0f}%", color="#00c896"), unsafe_allow_html=True)
    if result.get("summary"):
        st.info(result.get("summary"))


def render_question_card(topic: str, question_text: str, idx: int, total: int):
    return f"""
    <div style='background: rgba(79,142,247,0.08); border: 1px solid rgba(79,142,247,0.2); border-radius: 20px; padding: 24px; margin-bottom: 20px;'>
      <div style='display:flex; justify-content:space-between; flex-wrap:wrap; gap:12px;'>
        <div class='exam-topic'>📚 {html.escape(topic)}</div>
        <div style='color:#8b8b9e; font-size:12px;'>QUESTION {idx + 1} OF {total}</div>
      </div>
      <div style='font-size: 18px; font-weight: 700; margin-top: 14px; color: #f5f5f5;'>{html.escape(question_text)}</div>
    </div>
    """


EXAM_PROFILES = {
    "AZ-900": {"count": 40, "duration": 45},
    "AZ-204": {"count": 50, "duration": 60},
    "AZ-400": {"count": 60, "duration": 90},
}

def get_exam_profile(certification: str) -> dict:
    return EXAM_PROFILES.get(certification.upper(), {"count": 40, "duration": 45})


def format_time(seconds: int) -> str:
    minutes, seconds = divmod(max(0, seconds), 60)
    return f"{minutes}:{seconds:02d}"


def _group_questions_into_pages(questions: list, page_size: int = 10) -> list:
    """Group questions by topic, then split into pages of ~page_size questions.
    Keeps questions from the same topic together on the same page."""
    if not questions:
        return []
    topic_groups = OrderedDict()
    for i, q in enumerate(questions):
        topic = q.get("topic", "General")
        if topic not in topic_groups:
            topic_groups[topic] = []
        topic_groups[topic].append(i)
    pages = []
    current_page = []
    for topic, indices in topic_groups.items():
        if current_page and len(current_page) + len(indices) > page_size:
            pages.append(current_page)
            current_page = []
        current_page.extend(indices)
    if current_page:
        pages.append(current_page)
    return pages


def render_page_dots(current_page: int, pages: list, answers: dict, review_flags: dict, questions: list):
    """Show page-level progress with colored pill-shaped indicators."""
    dots_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;justify-content:center;'>"
    for pi, page_indices in enumerate(pages):
        page_answered = all(str(questions[i].get("id", i)) in answers for i in page_indices)
        page_has_review = any(str(questions[i].get("id", i)) in review_flags for i in page_indices)
        is_current = pi == current_page
        if is_current:
            bg = "#4f8ef7"
            border = "2px solid #7bb3ff"
            txt = "white"
        elif page_answered:
            bg = "#00c896"
            border = "2px solid #33d9a8"
            txt = "white"
        elif page_has_review:
            bg = "#ffa502"
            border = "2px solid #ffc107"
            txt = "black"
        else:
            bg = "rgba(255,255,255,0.08)"
            border = "2px solid rgba(255,255,255,0.15)"
            txt = "#8b8b9e"
        count = len(page_indices)
        label = f"P{pi+1} ({count})"
        dots_html += f"<span style='display:inline-flex;align-items:center;justify-content:center;min-width:40px;height:30px;padding:0 10px;border-radius:15px;background:{bg};border:{border};font-size:11px;font-weight:700;color:{txt};cursor:default;'>{label}</span>"
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)


def render_results_headline(state: dict, final_result: dict):
    verdict = final_result.get("phases", {}).get("assessment", {}).get("outcome", "Unknown")
    score = final_result.get("phases", {}).get("assessment", {}).get("score", 0)
    color = "#00c896" if verdict == "PASS" else "#ff4757"
    icon = "🎉" if verdict == "PASS" else "❌"
    st.markdown(f"""
    <div style='background: rgba(0,0,0,0.25); border: 1px solid {color}; border-radius: 24px; padding: 28px; margin-bottom: 24px;'>
      <div style='font-size: 48px;'>{icon}</div>
      <div style='font-size: 40px; color: {color}; font-weight: 800;'>{verdict}</div>
      <div style='font-size: 32px; color: white; margin-top: 8px;'>{score:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)


def render_results_stat_cards(state: dict, final_result: dict):
    assessment = final_result.get("phases", {}).get("assessment", {})
    outcome = assessment.get("outcome", "N/A")
    score = assessment.get("score", 0)
    weak_topics = state.get("weak_topics", [])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_stat_card("📝", "Score", f"{score:.1f}%", color="#00c896"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_stat_card("⚖️", "Outcome", outcome, color="#4f8ef7"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_stat_card("📚", "Topics", str(len(state.get("skill_map", []))), color="#a855f7"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_stat_card("⚡", "Weak Topics", str(len(weak_topics)), color="#ffa502"), unsafe_allow_html=True)


def render_study_plan_with_adaptations(state: dict):
    plan = state.get("study_plan", {})
    if not plan:
        st.info("Study plan not available.")
        return
    for week, entry in plan.items():
        # study_plan values are usually {focus, topics, hours, milestone} dicts,
        # but adapted plans can carry lists/strings/flags — render defensively
        # so a stray non-dict entry never crashes the whole results page.
        week_label = str(week).replace("_", " ").title()
        if isinstance(entry, dict):
            with st.expander(f"📅 {week_label}: {entry.get('focus', 'Study focus')}", expanded=False):
                topics = entry.get("topics", [])
                if isinstance(topics, (list, tuple)) and topics:
                    st.markdown("**Topics to cover**")
                    st.markdown("\n".join(f"- {html.escape(str(t))}" for t in topics))
                elif topics:
                    st.markdown(f"**Topics to cover:** {html.escape(str(topics))}")
                hours = entry.get("hours")
                if hours:
                    st.markdown(f"**⏱️ Estimated hours:** {hours}")
                if entry.get("milestone"):
                    st.markdown(f"**🎯 Milestone:** {html.escape(str(entry.get('milestone')))}")
        elif isinstance(entry, (list, tuple)):
            with st.expander(f"📅 {week_label}", expanded=False):
                st.markdown("\n".join(f"- {html.escape(str(t))}" for t in entry))
        else:
            with st.expander(f"📅 {week_label}", expanded=False):
                st.markdown(html.escape(str(entry)))


def render_skill_tags(state: dict):
    weak_topics = state.get("weak_topics", [])
    skill_map = state.get("skill_map", [])
    if skill_map:
        st.markdown("### 🔖 Skills Covered")
        chips = "".join([
            f"<span style='display:inline-block;margin:3px 6px 3px 0;padding:8px 12px;border-radius:999px;background:rgba(79,142,247,0.14);color:#b3d1ff;font-size:13px;'>{html.escape(str(topic))}</span>"
            for topic in skill_map[:12]
        ])
        st.markdown(f"<div style='display:flex;flex-wrap:wrap;'>{chips}</div>", unsafe_allow_html=True)
    if weak_topics:
        st.markdown("### ⚠️ Weak Topics")
        chips = "".join([
            f"<span style='display:inline-block;margin:3px 6px 3px 0;padding:8px 12px;border-radius:999px;background:rgba(255,69,87,0.14);color:#ffb3ba;font-size:13px;'>{html.escape(str(topic))}</span>"
            for topic in weak_topics[:12]
        ])
        st.markdown(f"<div style='display:flex;flex-wrap:wrap;'>{chips}</div>", unsafe_allow_html=True)


def render_council_debate_chat(votes: dict):
    if not votes:
        st.info("Council votes are not available yet.")
        return
    st.markdown("### 🗣️ Readiness Council Debate")
    for agent_name, vote in votes.items():
        if not isinstance(vote, dict):
            continue
        verdict = vote.get("verdict", "UNKNOWN")
        confidence = vote.get("confidence", 0)
        evidence = vote.get("evidence", [])
        agent_label = agent_name.replace("_", " ").title()
        st.markdown(f"<div style='border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);border-radius:18px;padding:18px;margin-bottom:12px;'>"
                    f"<div style='font-weight:700;color:#ffffff;'>{agent_label} — {verdict}</div>"
                    f"<div style='color:#8b8b9e;font-size:13px;margin-top:6px;'>Confidence: {confidence:.0f}%</div>", unsafe_allow_html=True)
        if evidence:
            for item in evidence[:2]:
                st.markdown(f"<div style='color:#c0c0d0;font-size:13px;margin-top:6px;'>• {html.escape(str(item))}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_council_exam_explanation(state: dict, final_result: dict):
    votes = state.get("council_votes", {}) or {}
    outcome = final_result.get("phases", {}).get("assessment", {}).get("outcome", "UNKNOWN")
    score = final_result.get("phases", {}).get("assessment", {}).get("score", 0)
    matched = 0
    total_agents = 0

    if not votes:
        st.info("No council prediction data is available for this exam.")
        return

    st.markdown(f"<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(79,142,247,0.2);border-radius:20px;padding:18px;margin-bottom:18px;'>"
                f"<div style='font-size:18px;font-weight:700;color:#ffffff;'>Council pass/fail analysis</div>"
                f"<div style='color:#8b8b9e;margin-top:8px;'>Actual exam outcome: <strong>{outcome}</strong> ({score:.1f}%)</div>"
                f"</div>", unsafe_allow_html=True)

    for agent_name, vote in votes.items():
        if not isinstance(vote, dict):
            continue
        verdict = vote.get("verdict", "UNKNOWN")
        confidence = vote.get("confidence", 0)
        evidence = vote.get("evidence", [])
        agent_label = agent_name.replace("_", " ").title()
        predicted_pass = verdict == "READY"
        actual_pass = outcome == "PASS"
        is_match = predicted_pass == actual_pass
        badge_color = "#00c896" if is_match else "#ff4757"
        matched += 1 if is_match else 0
        total_agents += 1

        st.markdown(f"<div style='border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);border-radius:18px;padding:18px;margin-bottom:12px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div style='font-weight:700;color:#ffffff;'>{agent_label}</div>"
                    f"<div style='color:{badge_color};font-weight:700;'>{'✅ Matched' if is_match else '❌ Missed'}</div>"
                    f"</div>"
                    f"<div style='color:#8b8b9e;font-size:13px;margin-top:6px;'>Prediction: {verdict} ({confidence:.0f}% confidence)</div>", unsafe_allow_html=True)
        if evidence:
            st.markdown(f"<div style='color:#c0c0c0;font-size:13px;margin-top:8px;font-weight:600;'>Key evidence:</div>", unsafe_allow_html=True)
            for item in evidence[:3]:
                st.markdown(f"<div style='color:#c0c0c0;font-size:13px;margin-top:4px;'>• {html.escape(str(item))}</div>", unsafe_allow_html=True)
        explanation = vote.get("reason", vote.get("explanation", ""))
        if explanation:
            st.markdown(f"<div style='color:#b3b3c7;font-size:13px;margin-top:8px;'>Explanation: {html.escape(str(explanation))}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if total_agents:
        st.markdown(f"<div style='background:rgba(79,142,247,0.08);border:1px solid rgba(79,142,247,0.2);border-radius:18px;padding:16px;margin-top:12px;'>"
                    f"<div style='font-weight:700;color:#ffffff;'>Prediction accuracy</div>"
                    f"<div style='color:#8b8b9e;font-size:13px;margin-top:6px;'>{matched}/{total_agents} council agents matched the actual outcome.</div>"
                    f"</div>", unsafe_allow_html=True)


def render_verdict_reveal(verdict: str, confidence: float, reasoning: str):
    color = "#00c896" if verdict == "READY" else "#ff4757" if verdict == "NOT_READY" else "#ffa502"
    icon = "✅" if verdict == "READY" else "❌" if verdict == "NOT_READY" else "⏳"
    st.markdown(f"<div style='background:rgba(255,255,255,0.05);border:1px solid {color};border-radius:22px;padding:24px;margin-bottom:20px;'>"
                f"<div style='font-size:32px;font-weight:800;color:{color};'>{icon} {verdict.replace('_',' ')}</div>"
                f"<div style='font-size:18px;color:white;margin-top:8px;'>Confidence: {confidence:.0f}%</div>"
                f"<div style='margin-top:12px;color:#b3b3c7;font-size:14px;'>{html.escape(str(reasoning))}</div>"
                f"</div>", unsafe_allow_html=True)


def render_resource_section(topic: str, items: list):
    if topic:
        st.markdown(f"### {html.escape(str(topic))}")
    if not items:
        st.info("No resources available for this topic.")
        return
    for index, item in enumerate(items):
        if isinstance(item, str):
            item = {"title": item}
        if not isinstance(item, dict):
            item = {"title": str(item)}
        title = item.get("title", item.get("name", "Resource"))
        source = item.get("source", item.get("provider", ""))
        url = item.get("url") or item.get("link") or item.get("source_url") or item.get("homepage") or ""
        tags = []
        if item.get("type"):
            tags.append(item.get("type"))
        if item.get("price"):
            tags.append(str(item.get("price")))
        badge_html = " ".join([f"<span style='color:#8b8b9e;font-size:12px;background:rgba(255,255,255,0.06);border-radius:10px;padding:4px 8px;margin-right:6px;'>{html.escape(str(tag))}</span>" for tag in tags])
        link_html = f"<a href='{html.escape(url)}' target='_blank' style='color:#4f8ef7;text-decoration:none;font-weight:700;'>Open resource</a>" if url else ""
        item_container = st.container()
        with item_container:
            st.markdown(
                f"<div style='border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);border-radius:20px;padding:18px;margin-bottom:16px;'>"
                f"<div style='font-size:16px;font-weight:700;color:white;margin-bottom:6px;'>{html.escape(str(title))}</div>"
                f"<div style='font-size:13px;color:#8b8b9e;margin-bottom:8px;'>{html.escape(str(source))}</div>"
                f"<div style='margin-bottom:8px;'>{badge_html}</div>"
                f"<div>{link_html}</div>"
                f"</div>", unsafe_allow_html=True)


def normalize_resource_categories(resources_all: dict) -> dict:
    categories = ["Official", "MVP", "Videos", "Practice"]
    normalized = {cat: [] for cat in categories}
    for topic, topic_resources in resources_all.items():
        if isinstance(topic_resources, dict):
            lower_resources = {str(k).lower(): v for k, v in topic_resources.items()}
            for cat in categories:
                cat_items = lower_resources.get(cat.lower()) or lower_resources.get(cat.lower() + "s")
                if cat_items:
                    if not isinstance(cat_items, list):
                        cat_items = [cat_items]
                    normalized[cat].append((topic, cat_items))
        elif isinstance(topic_resources, list):
            normalized["Official"].append((topic, topic_resources))
        elif topic_resources is not None:
            normalized["Official"].append((topic, [topic_resources]))
    return normalized


@st.fragment
def _render_resource_tab_fragment(resources_all: dict):
    """Fragment for resource tab switching.
    When user clicks a tab, ONLY this fragment reruns —
    not the sidebar, plan review, or results view."""
    if not resources_all:
        st.warning("No resources loaded.")
        return
    if "active_resource_tab" not in st.session_state:
        st.session_state.active_resource_tab = "Official"
    categories = ["Official", "MVP", "Videos", "Practice"]
    selected_tab = st.radio(
        "Resource type",
        categories,
        index=categories.index(st.session_state.active_resource_tab) if st.session_state.active_resource_tab in categories else 0,
        horizontal=True,
        key="active_resource_tab"
    )
    resources_by_category = normalize_resource_categories(resources_all)
    entries = resources_by_category.get(selected_tab, [])
    if not entries:
        st.info(f"No {selected_tab} resources available.")
        return
    for topic, items in entries:
        if topic:
            st.markdown(f"#### {html.escape(str(topic))}")
        render_resource_section("", items)


def render_learning_resources(state: dict):
    resources_all = state.get("learning_resources", {})
    if not resources_all:
        st.warning("No resources loaded.")
        return
    _render_resource_tab_fragment(resources_all)


def render_coaching_section(state: dict):
    misconceptions = state.get("misconceptions", []) or []
    socratic_questions = state.get("socratic_questions", []) or []
    remediation = state.get("remediation", {}) or {}
    if not misconceptions and not socratic_questions and not remediation:
        st.info("No coaching details available.")
        return
    st.markdown("### 🧠 Coaching Guidance")
    if misconceptions:
        st.markdown("**Root misconceptions**")
        for m in misconceptions:
            st.write(f"- {m}")
    if socratic_questions:
        st.markdown("**Socratic questions**")
        for q in socratic_questions:
            st.markdown(f"- {q.get('question','')}")
    if remediation:
        st.markdown("**Remediation plan**")
        st.write(remediation)


def render_manager_insights_tab(state: dict):
    # Cache manager insights in session state, refresh every 60 seconds
    now = time.time()
    last_check = st.session_state.get("_manager_last_check", 0)
    if now - last_check > 60:
        insights = get_api("manager")
        st.session_state._manager_cache = insights if insights else {}
        st.session_state._manager_last_check = now
    insights = st.session_state.get("_manager_cache", {})
    if not insights or insights.get("error"):
        st.info("Manager insights are not available yet.")
        return
    team = insights.get("team_readiness", [])
    recent = insights.get("recent_activity", [])
    if team:
        st.markdown("### 📈 Team Readiness")
        st.table(team)
    if recent:
        st.markdown("### 🕒 Recent Assessment Activity")
        st.table(recent[:10])
    if not team and not recent:
        st.info("Manager insights are not available yet.")


def render_reputation_chart(state: dict):
    # Cache reputation data in session state, refresh every 60 seconds
    now = time.time()
    last_check = st.session_state.get("_reputation_last_check", 0)
    if now - last_check > 60:
        payload = get_api("reputation")
        st.session_state._reputation_cache = payload if payload else {}
        st.session_state._reputation_last_check = now
    reputation_payload = st.session_state.get("_reputation_cache", {})
    agents = reputation_payload.get("agents", []) if isinstance(reputation_payload, dict) else []
    if not agents:
        st.info("Reputation data is not available yet.")
        return
    names = [a.get("agent_name", "") for a in agents]
    scores = [a.get("accuracy_score", 0) for a in agents]
    fig = go.Figure(go.Bar(x=names, y=scores, marker_color=["#4f8ef7" if x >= 70 else "#ffa502" if x >= 50 else "#ff4757" for x in scores]))
    fig.update_layout(yaxis_range=[0, 100], template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)


def build_export_report(state: dict):
    return {
        "state": state,
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def render_next_actions(state: dict):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🆕 New Analysis", use_container_width=True):
            reset_all_session_state()
            st.session_state.view = "landing"
            st.rerun()
    with col2:
        if st.button("📄 Export Report", use_container_width=True):
            st.download_button(
                "Download JSON",
                data=json.dumps(build_export_report(state), indent=2, default=str),
                file_name="certops_report.json",
                mime="application/json",
                key="export_report"
            )
    with col3:
        st.write("")


def render_api_health():
    # Cache health check in session state, refresh every 30 seconds
    now = time.time()
    last_check = st.session_state.get("_health_last_check", 0)
    if now - last_check > 30:
        try:
            health = get_api("health")
            status = health.get("status")
            st.session_state._health_ok = bool(status)
            st.session_state._health_status = status or "Unreachable"
        except Exception:
            st.session_state._health_ok = False
            st.session_state._health_status = "Unreachable"
        st.session_state._health_last_check = now
    if st.session_state.get("_health_ok"):
        st.markdown(
            f'<div class="sb-health ok"><span class="hdot"></span>System online · {st.session_state["_health_status"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="sb-health down"><span class="hdot"></span>Backend unreachable</div>',
            unsafe_allow_html=True,
        )


# Journey steps shown in the sidebar. Each maps the linear flow into 4 phases
# so the sidebar mirrors the agent-driven story on the home page.
JOURNEY_STEPS = [
    ("Setup", "Pick your certification", {"landing"}),
    ("Council debate", "Agents assess readiness", {"analyzing", "plan_review"}),
    ("Mock exam", "Prove it with questions", {"exam"}),
    ("Results", "Verdict vs. reality", {"results"}),
]

_VIEW_ORDER = ["landing", "analyzing", "plan_review", "exam", "results"]


def render_journey_steps(view: str):
    """Vertical stepper that matches the home-page aesthetic."""
    try:
        cur_idx = _VIEW_ORDER.index(view)
    except ValueError:
        cur_idx = 0
    rows = []
    for i, (name, hint, views) in enumerate(JOURNEY_STEPS):
        # max position among this step's views determines done/active ordering
        step_pos = max(_VIEW_ORDER.index(v) for v in views)
        min_pos = min(_VIEW_ORDER.index(v) for v in views)
        if view in views:
            state, mark = "active", str(i + 1)
        elif cur_idx > step_pos:
            state, mark = "done", "✓"
        else:
            state, mark = "", str(i + 1)
        line = '<div class="sb-line"></div>' if i < len(JOURNEY_STEPS) - 1 else ''
        rows.append(
            f"""<div class="sb-step {state}">
                  <div class="sb-rail"><div class="sb-dot">{mark}</div>{line}</div>
                  <div class="sb-text"><div class="sb-name">{name}</div>
                  <div class="sb-hint">{hint}</div></div>
                </div>"""
        )
    st.markdown('<div class="sb-label">Your journey</div>' + "".join(rows), unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        render_logo()
        view = st.session_state.view

        # Journey stepper (replaces the plain progress bar)
        render_journey_steps(view)

        # Session details as a styled glass mini-card
        if view != "landing":
            st.markdown(
                f"""<div class="sb-label">Session</div>
                <div class="sb-meta">
                  <div class="sb-row"><span class="sb-k">Learner</span><span class="sb-v">{st.session_state.get('form_learner_id','—')}</span></div>
                  <div class="sb-row"><span class="sb-k">Certification</span><span class="sb-v">{st.session_state.get('form_certification','—')}</span></div>
                  <div class="sb-row"><span class="sb-k">Role</span><span class="sb-v">{st.session_state.get('form_role','—')}</span></div>
                </div>""",
                unsafe_allow_html=True,
            )

        # "Jump to" only appears once analysis has started — and each target is
        # disabled until its data exists, so users can't jump into an empty
        # exam/results view before running the pipeline.
        if view not in ("landing", "analyzing"):
            has_plan = bool(st.session_state.get("pipeline_result"))
            has_exam = bool(st.session_state.get("questions"))
            has_results = bool(st.session_state.get("final_result"))
            if has_plan or has_exam or has_results:
                st.markdown('<div class="sb-label">Jump to</div>', unsafe_allow_html=True)
                if st.button("📚 Learning Plan", use_container_width=True,
                             disabled=not has_plan):
                    navigate_to("plan_review")
                if st.button("📝 Mock Exam", use_container_width=True,
                             disabled=not has_exam):
                    navigate_to("exam")
                if st.button("🎯 Results", use_container_width=True,
                             disabled=not has_results):
                    navigate_to("results")

        st.markdown('<div class="sb-label">Status</div>', unsafe_allow_html=True)
        render_api_health()
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("↺ Start Over", use_container_width=True):
            reset_all_session_state()
            st.session_state.view = "landing"
            st.rerun()


COUNCIL_AGENTS = [
    ("⚖️", "Critic", "Synthesises every vote into the final verdict", "#a855f7"),
    ("🌅", "Optimist", "Argues why you're ready to pass", "#00c896"),
    ("🔍", "Skeptic", "Challenges with why you might fail", "#ff4757"),
    ("🤝", "Advocate", "Weighs workload, stress & real constraints", "#4f8ef7"),
    ("📜", "Historian", "Compares you to similar past learners", "#ffa502"),
    ("⚠️", "Risk Analyst", "Calculates topic gaps & schedule risk", "#ff6b9d"),
]

PIPELINE_AGENTS = [
    ("📚", "Learning", "Builds your grounded skill map", "#4f8ef7"),
    ("🗓️", "Study Plan", "Turns gaps into a week-by-week plan", "#4f8ef7"),
    ("📝", "Assessment", "Generates & scores a real mock exam", "#00c896"),
    ("💡", "Socratic Coach", "Diagnoses why you got things wrong", "#ffa502"),
    ("🔄", "Reflection", "Learns from each outcome to improve", "#a855f7"),
    ("📊", "Manager Insights", "Rolls up team-level readiness", "#8b8b9e"),
]


def _agent_cards(agents: list) -> str:
    cards = "".join(
        f"""<div class="agent-card" style="--accent:{color};">
              <div class="ac-icon">{icon}</div>
              <div class="ac-name">{name}</div>
              <div class="ac-role">{role}</div>
            </div>"""
        for icon, name, role, color in agents
    )
    return f'<div class="agent-grid">{cards}</div>'


def render_agent_showcase():
    """Landing hero that foregrounds the multi-agent intelligence —
    the adversarial Readiness Council and the surrounding pipeline."""
    st.markdown(f"""
    <div style='margin-bottom:18px;'>
      <div class="ai-badge"><span class="dot"></span> 13 reasoning agents · powered by Azure AI Foundry</div>
      <div style='font-size:38px; font-weight:900; color:white; line-height:1.1;'>
        A council of AI agents decides if you're<br>ready to pass.
      </div>
      <div style='color:#c0c0d0; font-size:16px; margin-top:12px; max-width:640px;'>
        Specialist agents <b>debate</b> your certification readiness, a mock exam
        <b>tests</b> it, and the system <b>learns</b> from every outcome — in one flow.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-eyebrow">⚖️ The Readiness Council — they argue, not agree</div>', unsafe_allow_html=True)
    st.markdown(_agent_cards(COUNCIL_AGENTS), unsafe_allow_html=True)

    st.markdown("""
    <div class="principle-grid">
      <div class="principle-card">
        <div class="pc-title">🗣️ Agents debate, not report</div>
        <div class="pc-desc">Five specialists argue for and against your readiness. The verdict comes from conflict, not consensus.</div>
      </div>
      <div class="principle-card">
        <div class="pc-title">📎 Grounded, not guessed</div>
        <div class="pc-desc">Every recommendation cites a real source from the Foundry IQ knowledge base — no hallucinated advice.</div>
      </div>
      <div class="principle-card">
        <div class="pc-title">🧠 Learns from failure</div>
        <div class="pc-desc">Each wrong prediction re-weights agent reputation, so future verdicts get sharper over time.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-eyebrow">🔗 The full pipeline behind every verdict</div>', unsafe_allow_html=True)
    st.markdown(_agent_cards(PIPELINE_AGENTS), unsafe_allow_html=True)


def render_landing_view():
    render_agent_showcase()
    st.markdown('<div class="section-eyebrow">🚀 Start your assessment</div>', unsafe_allow_html=True)
    # A real bordered container that actually wraps the widgets. (Emitting a
    # raw <div> via st.markdown can't contain Streamlit widgets — it renders as
    # an empty styled box, so we use st.container(border=True) instead.)
    with st.container(border=True):
        col1, col2 = st.columns(2, gap='large')
        with col1:
            st.session_state.form_learner_id = st.text_input(
                "Learner ID",
                value=st.session_state.get("form_learner_id", "L-1001")
            )
            cert_choice = st.selectbox(
                "Certification",
                ["AZ-900", "AZ-204", "AZ-400", "Other"],
                index=["AZ-900", "AZ-204", "AZ-400", "Other"].index(
                    st.session_state.get("form_certification", "AZ-204")
                    if st.session_state.get("form_certification", "AZ-204") in ["AZ-900", "AZ-204", "AZ-400"]
                    else "Other"
                )
            )
            if cert_choice == "Other":
                st.session_state.form_certification = st.text_input(
                    "Enter certification",
                    value=st.session_state.get("form_certification", "")
                ).strip().upper() or "AZ-204"
            else:
                st.session_state.form_certification = cert_choice
        with col2:
            st.session_state.form_role = st.text_input(
                "Role",
                value=st.session_state.get("form_role", "Cloud Engineer")
            )
            st.session_state.form_weeks = st.slider(
                "Target weeks", 1, 12,
                value=st.session_state.get("form_weeks", 6)
            )
        if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
            learner_id = st.session_state.get("form_learner_id", "L-1001")
            certification = st.session_state.get("form_certification", "AZ-204")
            role = st.session_state.get("form_role", "Cloud Engineer")
            weeks = st.session_state.get("form_weeks", 6)
            reset_all_session_state()
            st.session_state.form_learner_id = learner_id
            st.session_state.form_certification = certification
            st.session_state.form_role = role
            st.session_state.form_weeks = weeks
            st.session_state.view = "analyzing"
            update_url_params(learner_id, "analyzing")
            st.rerun()


def render_analyzing_view():
    render_progress_strip(0)
    if "pipeline_result" not in st.session_state:
        st.markdown(render_loading_header("Building your learning plan & convening the council"), unsafe_allow_html=True)
        progress = st.progress(0)
        status = st.empty()
        status.markdown("📚 Analyzing certification requirements...")
        progress.progress(20)
        result = post_api("pipeline", {
            "learner_id": st.session_state.get("form_learner_id", "L-1001"),
            "role": st.session_state.get("form_role", "Cloud Engineer"),
            "certification": st.session_state.get("form_certification", "AZ-204"),
            "target_weeks": st.session_state.get("form_weeks", 6)
        })
        progress.progress(60)
        status.markdown("⚖️ Council debating readiness...")
        if not result:
            render_error_state(
                "Failed to start analysis. Check backend connection.",
                lambda: st.session_state.pop("pipeline_result", None)
            )
            return
        progress.progress(100)
        st.session_state.pipeline_result = result
        # Questions are NOT generated here anymore — they're created lazily when
        # the learner starts the mock exam, keeping this analysis fast.
        st.session_state.questions = result.get("phases", {}).get("assessment", {}).get("questions", []) or []
    # Pipeline reached the council/plan stage — move on to plan review.
    if st.session_state.get("pipeline_result"):
        learner_id = st.session_state.get("form_learner_id", "")
        st.session_state.view = "plan_review"
        save_ui_session()
        update_url_params(learner_id, "plan_review")
        st.rerun()
    else:
        render_error_state(
            "Analysis failed. Retry?",
            lambda: st.session_state.pop("pipeline_result", None)
        )


def render_plan_review_view():
    render_progress_strip(1)
    state = get_api_state()
    # Backend memory is in-process; a restart (or stale URL/session) leaves us
    # here with no data. Detect it and route back instead of rendering empty
    # "not available" shells.
    if not state.get("has_data"):
        render_error_state(
            "Your session data is no longer available — the backend may have "
            "restarted. Please start a new analysis.",
            lambda: reset_all_session_state()
        )
        return
    st.markdown("## 📚 Your Learning Plan & Readiness Verdict")
    st.caption("Review your personalized plan, council debate, and study resources before starting the mock exam.")
    render_skill_tags(state)
    st.markdown("---")
    st.markdown("### ⚖️ Readiness Council")
    render_council_debate_chat(state.get("council_votes", {}))
    render_verdict_reveal(
        state.get("readiness_verdict", ""),
        state.get("readiness_confidence", 0),
        state.get("readiness_reasoning", "")
    )
    st.markdown("---")
    st.markdown("### 📅 Study Plan")
    render_study_plan_with_adaptations(state)
    st.markdown("---")
    st.markdown("### 📚 Learning Resources")
    st.info("Study these resources before taking your mock exam.")
    render_learning_resources(state)
    st.markdown("---")
    profile = get_exam_profile(st.session_state.get("form_certification", "AZ-204"))
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"**Mock exam profile:** {st.session_state.get('form_certification', 'AZ-204')} — {profile['count']} questions, {profile['duration']} minutes")
        # Questions are generated lazily here (not during the analysis), so the
        # earlier "Analyzing..." step stays fast.
        questions_ready = bool(st.session_state.get("questions"))
        btn_label = "✅ I'm Ready — Start Mock Exam" if questions_ready \
                    else "📝 Generate & Start Mock Exam"
        if st.button(btn_label, type="primary", use_container_width=True):
            if not questions_ready:
                with st.spinner("Generating your exam questions from Foundry IQ — this takes a moment..."):
                    result = post_api("assessment", {
                        "learner_id": st.session_state.get("form_learner_id", "L-1001")
                    }, timeout=240)
                new_questions = (result or {}).get("questions", []) or []
                if not new_questions:
                    st.error("Couldn't generate exam questions. Please try again.")
                    st.stop()
                st.session_state.questions = new_questions
            navigate_to("exam")


def _submit_exam(spinner_text: str = "Evaluating your performance...") -> bool:
    """Submit the current exam answers and route to results.

    Single source of truth for exam submission — used by both the manual
    Finish button and the auto-submit-on-timeout path, so behaviour can
    never drift between them. Returns True on success.
    """
    exam = st.session_state.get("exam", {})
    answers = exam.get("answers", {})
    pipeline_result = st.session_state.get("pipeline_result", {})
    learner_id = (pipeline_result or {}).get("learner_id", "") or st.session_state.get("form_learner_id", "L-1001")
    with st.spinner(spinner_text):
        result = post_api("pipeline/continue", {
            "learner_id": learner_id,
            "answers": answers,
        })
    if result:
        st.session_state.final_result = result
        navigate_to("results")
        return True
    st.error("Submission failed. Please retry.")
    return False


@st.fragment
def _render_finish_fragment():
    """Fragment for the finish button in the exam header.
    When clicked, ONLY this fragment reruns — the sticky header JS
    and question list stay intact."""
    exam = st.session_state.get("exam", {})
    questions = st.session_state.get("questions", [])
    total = len(questions)
    answers = exam.get("answers", {})
    unanswered = total - len(answers)
    finish_label = f"📤 Finish{' (' + str(unanswered) + ' unanswered)' if unanswered else ''}"
    if st.button(finish_label, type="primary", use_container_width=True, key="finish_header_btn"):
        _submit_exam()


@st.fragment
def _render_answer_fragment(qid: str, options: dict):
    """Fragment for answer selection via radio button.
    When user selects an answer, ONLY this small fragment reruns —
    the sidebar, timer header, and navigation buttons stay intact."""
    option_items = list(options.items())
    option_labels = ["Select an answer"] + [f"{key}. {value}" for key, value in option_items]
    option_key_map = {label: key for label, key in zip(option_labels[1:], [key for key, _ in option_items])}

    exam = st.session_state.exam
    current_answer = exam["answers"].get(qid)
    default_index = 0
    if current_answer:
        for i, (key, _) in enumerate(option_items, start=1):
            if key == current_answer:
                default_index = i
                break

    selected_label = st.radio(
        "Select your answer:",
        option_labels,
        index=default_index,
        key=f"radio_q_{qid}",
        label_visibility="collapsed"
    )
    if selected_label != "Select an answer":
        exam["answers"][qid] = option_key_map[selected_label]


def _scroll_to_top(nonce):
    """Reliably scroll the page to the top.

    st.markdown('<script>') does NOT execute in Streamlit, so we use a real
    components iframe and reach into the parent document. The nonce changes
    (e.g. on page navigation) to force the iframe to re-run the script.
    """
    components.html(
        f"""
        <script>
          // nonce={nonce}
          const doc = window.parent.document;
          const main = doc.querySelector('section.main')
                     || doc.querySelector('[data-testid="stAppViewContainer"]');
          if (main) main.scrollTo({{top: 0, behavior: 'instant'}});
          doc.documentElement.scrollTop = 0;
          doc.body.scrollTop = 0;
        </script>
        """,
        height=0,
    )


def render_exam_view():
    # Land at the top on entry and on every page change (re-fires via the nonce).
    _scroll_to_top(st.session_state.get("exam", {}).get("current_page", 0))

    render_progress_strip(2)

    pipeline_result = st.session_state.get("pipeline_result", {})
    if not pipeline_result:
        render_error_state(
            "Exam state lost. Start over.",
            lambda: reset_all_session_state()
        )
        return

    # Extract verdict data from pipeline_result — avoids an HTTP call on every rerun
    phases = pipeline_result.get("phases", {})
    council = phases.get("council", {})
    verdict = council.get("verdict") or pipeline_result.get("final_verdict", "")
    confidence = council.get("confidence") or pipeline_result.get("final_confidence", 0)
    reasoning = council.get("reasoning") or ""

    # Initialize exam state with topic-grouped pages
    questions = st.session_state.questions or []
    total = len(questions)
    if "exam" not in st.session_state or "pages" not in st.session_state.exam:
        pages = _group_questions_into_pages(questions)
        st.session_state.exam = {
            "current_page": 0,
            "answers": {},
            "review_flags": {},
            "start_time": time.time(),
            "pages": pages,
        }
        st.session_state._exam_auto_submitted = False

    exam = st.session_state.exam
    pages = exam["pages"]
    total_pages = len(pages)
    current_page = exam["current_page"]
    profile = get_exam_profile(st.session_state.get("form_certification", "AZ-204"))
    duration = profile["duration"]
    start_time = exam.get("start_time", time.time())
    elapsed = int(time.time() - start_time)
    remaining = duration * 60 - elapsed

    # Time-up: auto-submit so the timer is real, not decorative. Fires on the
    # first rerun after expiry (answering a question or page nav triggers it).
    if remaining <= 0 and not st.session_state.get("_exam_auto_submitted"):
        st.session_state._exam_auto_submitted = True
        st.warning("⏰ Time's up — submitting your exam automatically.")
        _submit_exam("Time's up — submitting your exam...")
        return

    # Urgency colour: amber under 5 min, red under 1 min.
    if remaining <= 60:
        time_color = "#ff4757"
    elif remaining <= 300:
        time_color = "#ffa502"
    else:
        time_color = "#f0f0f0"

    header_cols = st.columns([2, 1, 1])
    with header_cols[0]:
        st.markdown("## 📝 Mock Exam — Your Turn")
    with header_cols[1]:
        st.markdown(
            f"**Time left:** <span style='color:{time_color};font-weight:700;'>"
            f"{format_time(remaining)}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**{len(exam['answers'])}/{total} answered**")
    with header_cols[2]:
        _render_finish_fragment()

    if total == 0 or not pages:
        render_error_state(
            "No exam questions available.",
            lambda: reset_all_session_state()
        )
        return

    page_indices = pages[current_page]
    page_start = page_indices[0] + 1 if page_indices else 1
    page_end = page_indices[-1] + 1 if page_indices else 0

    # Per-page progress — shows how many questions on THIS page are answered
    page_answered_count = sum(1 for i in page_indices if str(questions[i].get("id", i)) in exam["answers"])
    page_q_count = len(page_indices)
    page_pct = int(page_answered_count / page_q_count * 100) if page_q_count else 0
    st.progress((current_page + 1) / total_pages, text=f"Overall: Page {current_page + 1} of {total_pages}")
    st.progress(page_pct / 100, text=f"This page: {page_answered_count}/{page_q_count} answered")
    st.caption(f"Questions {page_start}–{page_end} · Page: {page_answered_count}/{page_q_count} · Total: {len(exam['answers'])}/{total}")

    st.markdown("---")
    # Recap expander
    with st.expander("📋 Recap: Your plan & council verdict", expanded=False):
        render_verdict_reveal(verdict, confidence, reasoning)
        st.markdown(f"**Questions prepared:** {len(questions)}")

    # Render each question on this page
    for qi in page_indices:
        q = questions[qi]
        qid = str(q.get("id", qi))
        st.markdown(render_question_card(q.get("topic", ""), q.get("question", ""), qi, total), unsafe_allow_html=True)
        # Radio fragment — selecting an answer only reruns this small section
        _render_answer_fragment(qid, q.get("options", {}))
        if q.get("source"):
            st.caption(f"📖 Source: {q.get('source')}")
        st.markdown("---")

    # Page-level progress dots
    render_page_dots(current_page, pages, exam["answers"], exam["review_flags"], questions)

    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if current_page > 0:
            if st.button("← Previous Page", use_container_width=True):
                exam["current_page"] -= 1
                st.rerun()
        else:
            st.write("")
    with col_info:
        st.markdown(f"<div style='text-align:center;color:#8b8b9e;font-size:14px;'>Page {current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
    with col_next:
        if current_page < total_pages - 1:
            if st.button("Next Page →", type="primary", use_container_width=True):
                exam["current_page"] += 1
                st.rerun()
        else:
            # On last page, show "Last Page" info instead of a second Finish button
            # (the header already provides the persistent Finish button)
            st.markdown("<div style='text-align:center;color:#8b8b9e;font-size:13px;'>📄 Last Page</div>", unsafe_allow_html=True)


_REVIEW_PAGE_SIZE = 8


def render_answer_review(questions: list, exam_answers: dict):
    """Collapsible, paginated answer review — keeps the results page short.

    The whole review lives under one header (collapsed by default). When opened
    it shows one page of questions at a time with Prev/Next controls, so the
    page never grows to 40-60 stacked cards.
    """
    total = len(questions)
    if not total:
        return
    correct_count = sum(
        1 for q in questions
        if exam_answers.get(str(q.get("id")), "—") == q.get("correct_answer", "")
    )
    wrong_count = total - correct_count

    open_key = "review_open"
    page_key = "review_page"
    is_open = st.session_state.get(open_key, False)

    header = (f"📋 Answer Review — {total} questions  "
              f"(✅ {correct_count} · ❌ {wrong_count})")
    label = f"▼ {header}" if is_open else f"▶ {header}"
    if st.button(label, use_container_width=True, key="review_toggle"):
        st.session_state[open_key] = not is_open
        st.session_state[page_key] = 0
        st.rerun()

    if not is_open:
        return

    total_pages = (total + _REVIEW_PAGE_SIZE - 1) // _REVIEW_PAGE_SIZE
    page = max(0, min(st.session_state.get(page_key, 0), total_pages - 1))

    # Page navigation (top)
    nav_prev, nav_info, nav_next = st.columns([1, 2, 1])
    with nav_prev:
        if st.button("◀ Prev", use_container_width=True, disabled=(page == 0), key="rev_prev"):
            st.session_state[page_key] = page - 1
            st.rerun()
    with nav_info:
        start = page * _REVIEW_PAGE_SIZE + 1
        end = min((page + 1) * _REVIEW_PAGE_SIZE, total)
        st.markdown(
            f"<div style='text-align:center;color:#8b8b9e;padding-top:6px;'>"
            f"Questions {start}–{end} · Page {page + 1} of {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with nav_next:
        if st.button("Next ▶", use_container_width=True, disabled=(page >= total_pages - 1), key="rev_next"):
            st.session_state[page_key] = page + 1
            st.rerun()

    # Questions for this page only
    for q in questions[page * _REVIEW_PAGE_SIZE:(page + 1) * _REVIEW_PAGE_SIZE]:
        qid = str(q.get("id"))
        user_ans = exam_answers.get(qid, "—")
        correct = q.get("correct_answer", "")
        is_correct = user_ans == correct
        summary = "✅" if is_correct else "❌"
        title = q.get("question", "").strip()
        with st.expander(f"{summary} Q{qid}: {title[:70]}{'...' if len(title) > 70 else ''}", expanded=False):
            st.write(q.get("question", ""))
            for k, v in q.get("options", {}).items():
                tag = ""
                if k == correct:
                    tag = " ✅ (Correct)"
                if k == user_ans and k != correct:
                    tag = " ❌ (Your answer)"
                if k == user_ans and k == correct:
                    tag = " ✅ (Your answer)"
                st.write(f"{k}. {v}{tag}")
            if q.get("explanation"):
                st.caption(f"💡 {q.get('explanation')}")
            if q.get("source"):
                st.caption(f"📖 {q.get('source')}")


def render_results_view():
    render_progress_strip(3)
    final_result = st.session_state.get("final_result", {})
    if not final_result:
        render_error_state(
            "Results not available.",
            lambda: reset_all_session_state()
        )
        return
    # Cache API state in session state, refresh every 120 seconds
    # The backend state is stable during results viewing (no new pipeline runs)
    now = time.time()
    last_check = st.session_state.get("_state_last_check", 0)
    if now - last_check > 120:
        st.session_state._state_cache = get_api_state()
        st.session_state._state_last_check = now
    state = st.session_state.get("_state_cache", {})
    logger.debug(f"council_votes keys: {list(state.get('council_votes', {}).keys())}")
    logger.debug(f"readiness_verdict: {state.get('readiness_verdict')}")
    logger.debug(f"assessment_score: {state.get('assessment_score')}")
    logger.debug(f"assessment_breakdown: {state.get('assessment_breakdown')}")
    logger.debug(f"misconceptions: {state.get('misconceptions')}")
    logger.debug(f"learning_resources keys: {list(state.get('learning_resources', {}).keys())}")
    st.markdown("## 📊 Exam Summary")
    score = state.get("assessment_score", 0)
    breakdown_total = sum(d.get("total", 0) for d in state.get("assessment_breakdown", {}).values())
    breakdown_correct = sum(d.get("correct", 0) for d in state.get("assessment_breakdown", {}).values())
    st.markdown(f"""
    <div style='text-align:center; padding:24px;'>
      <div style='font-size:48px; font-weight:900;'>{breakdown_correct} / {breakdown_total}</div>
      <div style='color:#8b8b9e;'>Questions Correct ({score:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📋 Answer Review")
    questions = st.session_state.get("questions", [])
    exam_answers = st.session_state.get("exam", {}).get("answers", {})
    review_flags = st.session_state.get("exam", {}).get("review_flags", {})
    weak_topics = state.get("weak_topics", [])
    strong_topics = [topic for topic, data in state.get("assessment_breakdown", {}).items() if data.get("score", 0) >= 80]
    st.markdown(f"**Weak topics:** {', '.join(weak_topics) if weak_topics else 'None'}")
    st.markdown(f"**Strong topics:** {', '.join(strong_topics) if strong_topics else 'None'}")
    st.markdown("---")
    st.markdown("### ⚖️ Council Pass/Fail Analysis")
    render_council_exam_explanation(state, final_result)
    st.markdown("---")
    render_answer_review(questions, exam_answers)
    st.markdown("---")
    tabs = st.tabs(["📅 Adapted Study Plan", "📚 Learning Resources", "🧠 Coaching", "📊 Manager View", "🏆 Reputation"])
    with tabs[0]:
        render_study_plan_with_adaptations(state)
    with tabs[1]:
        render_learning_resources(state)
    with tabs[2]:
        render_coaching_section(state)
    with tabs[3]:
        render_manager_insights_tab(state)
    with tabs[4]:
        render_reputation_chart(state)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔁 Retake Exam (New Questions)", type="primary", use_container_width=True):
            with st.spinner("Generating new questions based on your adapted plan..."):
                result = post_api("assessment", {
                    "learner_id": st.session_state.get("form_learner_id", "L-1001")
                })
            new_questions = result.get("questions", [])
            if not new_questions:
                st.error("Failed to generate new questions.")
            else:
                st.session_state.questions = new_questions
                st.session_state.exam = {
                    "current_q": 0,
                    "answers": {},
                    "review_flags": {},
                    "start_time": time.time()
                }
                st.session_state.pop("final_result", None)
                # Clear cached API state so results view fetches fresh data
                for key in ["_state_cache", "_state_last_check", "_manager_cache", "_manager_last_check", "_reputation_cache", "_reputation_last_check"]:
                    st.session_state.pop(key, None)
                navigate_to("exam")
    st.markdown("---")
    render_next_actions(state)


def reset_all_session_state():
    for key in [
        "pipeline_result",
        "questions",
        "exam",
        "final_result",
        "form_learner_id",
        "form_certification",
        "form_role",
        "form_weeks",
        "_state_cache",
        "_state_last_check",
        "_manager_cache",
        "_manager_last_check",
        "_reputation_cache",
        "_reputation_last_check",
    ]:
        st.session_state.pop(key, None)
    # Clear URL query params so stale learner_id doesn't trigger session restore
    try:
        st.experimental_set_query_params()
    except AttributeError:
        if hasattr(st, "query_params"):
            st.query_params.clear()


def initialize_session():
    params = get_url_params()
    selected_view = params.get("view")
    learner_id = params.get("learner_id")
    allowed_views = {"landing", "analyzing", "plan_review", "exam", "results"}
    if selected_view in allowed_views:
        st.session_state.view = selected_view
    elif "view" not in st.session_state:
        st.session_state.view = "landing"
    if learner_id and "form_learner_id" not in st.session_state:
        st.session_state.form_learner_id = learner_id
    # Don't restore from backend if user explicitly reset to landing
    if st.session_state.view != "landing" and learner_id and ("pipeline_result" not in st.session_state or "questions" not in st.session_state):
        restore_ui_session()
    if "view" not in st.session_state:
        st.session_state.view = "landing"
    if learner_id:
        update_url_params(learner_id, st.session_state.view)


def main():
    render_global_css()
    initialize_session()
    render_sidebar()
    view = st.session_state.view
    if view == "landing":
        render_landing_view()
    elif view == "analyzing":
        render_analyzing_view()
    elif view == "plan_review":
        render_plan_review_view()
    elif view == "exam":
        render_exam_view()
    elif view == "results":
        render_results_view()
    else:
        st.error(f"Unknown view: {view}")


main()
