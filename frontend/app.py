"""
CertOps AI — Premium SaaS Dashboard
Single-pipeline automated certification readiness platform.
Design: Linear/Vercel-inspired dark mode with glass morphism, gradients, animations.
"""

import time
import json
import random
import streamlit as st
import httpx
import plotly.graph_objects as go
from frontend.state import get_api_state, post_api, get_api, has_completed_phase, show_phase_guard

st.set_page_config(
    page_title="CertOps AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# PREDEFINED DESIGN SYSTEM — Color Tokens & Utility Functions
# ============================================================================
DS = {
    "primary": "#4f8ef7",
    "secondary": "#a855f7",
    "success": "#00c896",
    "danger": "#ff4757",
    "warning": "#ffa502",
    "bg_card": "rgba(255,255,255,0.04)",
    "bg_card_hover": "rgba(255,255,255,0.08)",
    "border": "rgba(255,255,255,0.1)",
    "border_hover": "rgba(79,142,247,0.4)",
    "text_primary": "#f0f0f0",
    "text_secondary": "#8b8b9e",
    "text_muted": "#555566",
    "glass": "rgba(255,255,255,0.04)",
    "glass_border": "rgba(255,255,255,0.1)",
    "shadow": "0 8px 32px rgba(0,0,0,0.3)",
    "gradient_btn": "linear-gradient(135deg, #4f8ef7, #a855f7)",
    "gradient_bg": "radial-gradient(circle at 50% 0%, rgba(79,142,247,0.15) 0%, transparent 60%)",
}


def render_stat_card(icon: str, label: str, value: str, trend: str = "", trend_positive: bool = True, color: str = DS["primary"]):
    """Modern stat card with icon, trend indicator, decorative blob."""
    trend_color = DS["success"] if trend_positive else DS["danger"]
    trend_arrow = "↑" if trend_positive else "↓"
    trend_html = f"""
    <div style='font-size: 12px; color: {trend_color}; margin-top: 8px; font-weight: 600;'>
      {trend_arrow} {trend}
    </div>""" if trend else ""
    return f"""
    <div style='
      background: {DS["glass"]};
      border: 1px solid {DS["border"]};
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
      <div style='font-size: 12px; color: {DS["text_secondary"]}; text-transform: uppercase; letter-spacing: 1px;'>{label}</div>
      {trend_html}
    </div>"""


def show_skeleton(rows: int = 3):
    """Skeleton loading shimmer animation."""
    for _ in range(rows):
        st.markdown(f"""
        <div style='
          background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.03) 75%);
          background-size: 200% 100%;
          animation: shimmer 1.5s infinite;
          border-radius: 12px;
          height: 60px;
          margin-bottom: 12px;
        '></div>
        <style>
          @keyframes shimmer {{ 0% {{ background-position: 200% 0; }} 100% {{ background-position: -200% 0; }} }}
        </style>
        """, unsafe_allow_html=True)


def render_sidebar_progress(state: dict):
    """Circular SVG progress ring for pipeline completion."""
    phases_done = sum([
        bool(state.get("skill_map")),
        bool(state.get("readiness_verdict")),
        bool(state.get("assessment_outcome")),
        bool(state.get("misconceptions")) or state.get("assessment_outcome") == "PASS",
        bool(state.get("reflection"))
    ])
    total = 5
    pct = int((phases_done / total) * 100)
    r = 42
    circ = 2 * 3.14159 * r
    offset = circ * (1 - pct / 100)
    st.markdown(f"""
    <div style='text-align: center; padding: 16px 0;'>
      <div style='position: relative; width: 100px; height: 100px; margin: 0 auto;'>
        <svg width="100" height="100" style="transform: rotate(-90deg);">
          <circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
          <circle cx="50" cy="50" r="{r}" fill="none" stroke="#4f8ef7" stroke-width="8"
                  stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round"/>
        </svg>
        <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 20px; font-weight: 800;'>{pct}%</div>
      </div>
      <div style='color: #8b8b9e; font-size: 11px; margin-top: 8px; text-transform: uppercase; letter-spacing: 1px;'>Pipeline Progress</div>
    </div>""", unsafe_allow_html=True)


# ============================================================================
# GLOBAL DESIGN SYSTEM CSS
# ============================================================================
st.markdown(f"""
<style>
  /* ---------- Root ---------- */
  #root > div:first-child {{ background: #0a0a11; }}
  .stApp {{ background: #0a0a11; }}
  .main > div {{ background: #0a0a11; }}

  /* ---------- Glass input card ---------- */
  .input-card {{
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 32px;
    max-width: 700px;
    margin: 0 auto 40px auto;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  }}
  .input-card:hover {{ border-color: rgba(79,142,247,0.4); transition: border-color 0.3s ease; }}

  /* ---------- Streamlit overrides ---------- */
  .stTextInput input, .stSelectbox > div > div {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #f0f0f0 !important;
    padding: 12px !important;
  }}
  .stTextInput input:focus {{
    border-color: #4f8ef7 !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.15) !important;
  }}
  .stSlider > div > div > div > div {{
    background: linear-gradient(90deg, #4f8ef7, #a855f7) !important;
  }}
  .stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #4f8ef7, #a855f7) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 0 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 20px rgba(79,142,247,0.4) !important;
    transition: all 0.2s ease !important;
  }}
  .stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 28px rgba(79,142,247,0.5) !important;
  }}
  .stButton > button:not([kind="primary"]) {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #f0f0f0 !important;
    transition: all 0.2s ease !important;
  }}
  .stButton > button:not([kind="primary"]):hover {{
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.3) !important;
  }}
  .stProgress > div > div > div {{
    background: linear-gradient(90deg, #4f8ef7, #a855f7) !important;
    border-radius: 10px !important;
  }}
  .stProgress > div > div {{
    background: rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    height: 8px !important;
  }}
  .streamlit-expanderHeader {{
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
  }}
  .streamlit-expanderHeader:hover {{
    background: rgba(255,255,255,0.06) !important;
  }}
  [data-testid="stMetricValue"] {{
    font-size: 32px !important;
    font-weight: 800 !important;
  }}
  [data-testid="stMetricLabel"] {{
    color: #8b8b9e !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
  }}
  .stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
  }}
  .stTabs [aria-selected="true"] {{
    background: rgba(79,142,247,0.15) !important;
    color: #4f8ef7 !important;
  }}

  /* ---------- Skill tags ---------- */
  .skill-tag {{
    display: inline-block;
    background: rgba(79,142,247,0.1);
    border: 1px solid rgba(79,142,247,0.3);
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 13px;
    color: #4f8ef7;
    margin: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }}
  .skill-tag:hover {{
    background: rgba(79,142,247,0.25);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(79,142,247,0.3);
  }}
  .skill-tag.weak {{
    background: rgba(255,71,87,0.1);
    border-color: rgba(255,71,87,0.3);
    color: #ff4757;
  }}
  .skill-tag.weak:hover {{
    background: rgba(255,71,87,0.25);
    box-shadow: 0 4px 12px rgba(255,71,87,0.3);
  }}

  /* ---------- Typing animation ---------- */
  .typing-dots span {{
    animation: blink 1.4s infinite;
    animation-fill-mode: both;
  }}
  .typing-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
  .typing-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
  @keyframes blink {{ 0%,80%,100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
  @keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} }}

  /* ---------- Answer option letter badge ---------- */
  .opt-letter {{
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700;
    font-size: 14px;
  }}

  /* ---------- Resource card ---------- */
  .resource-card {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    transition: all 0.2s ease;
  }}
  .resource-card:hover {{
    background: rgba(255,255,255,0.06);
    border-color: rgba(79,142,247,0.3);
    transform: translateX(4px);
  }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.title("🎓 CertOps AI")
st.sidebar.markdown("*Self-Learning Certification Readiness Intelligence Platform*")

# Circular progress ring
state = get_api_state()
render_sidebar_progress(state)

# Phase status badges
st.sidebar.divider()
st.sidebar.markdown("### Session Status")
state_side = get_api_state()

def status_badge(condition, label, detail=""):
    icon = "✅" if condition else "⭕"
    line = f"{icon} {label}"
    if condition and detail:
        line += f": {detail}"
    st.sidebar.write(line)

status_badge(bool(state_side.get("skill_map")), "Learning Plan", f"{len(state_side.get('skill_map', []))} skills")
status_badge(bool(state_side.get("readiness_verdict")), "Council Verdict", state_side.get("readiness_verdict", ""))
status_badge(bool(state_side.get("assessment_outcome")), "Assessment", f"{state_side.get('assessment_score', 0):.0f}%")
status_badge(bool(state_side.get("misconceptions")), "Coaching", "Diagnosed" if state_side.get("misconceptions") else "")
status_badge(bool(state_side.get("reflection")), "Reflection", "Complete" if state_side.get("reflection") else "")

# Deep-dive navigation
st.sidebar.divider()
st.sidebar.markdown("### Deep Dive")
page = st.sidebar.selectbox("View Details", [
    "🏠 Pipeline (Main)",
    "⚖️ Council Debate",
    "📊 Manager Insights",
    "🏆 Agent Reputation",
    "🔍 Reasoning Trace"
])

# System health
st.sidebar.divider()
with st.sidebar.expander("🔧 System Status"):
    try:
        health = httpx.get("http://localhost:8000/health", timeout=3).json()
        st.write(f"✅ API: {health.get('status')}")
    except:
        st.write("❌ API: Offline")
    sc = get_api_state()
    st.write(f"💾 Memory: {'Active' if sc.get('learner_id') else 'Empty'}")

st.sidebar.divider()
if st.sidebar.button("🔄 Reset Demo", use_container_width=True):
    get_api("reset-demo")
    st.sidebar.success("✅ Reset!")
    st.rerun()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_week_data(week_data: dict) -> dict:
    return {
        "focus": week_data.get("focus") or week_data.get("theme") or week_data.get("title") or "Study session",
        "topics": week_data.get("topics") or week_data.get("activities") or week_data.get("skills") or [],
        "hours": week_data.get("hours") or week_data.get("duration") or week_data.get("study_hours") or 5,
        "milestone": week_data.get("milestone") or week_data.get("goal") or week_data.get("outcome") or "",
        "resources": week_data.get("resources") or week_data.get("materials") or []
    }


def render_agent_activity_feed():
    """Animated agent activity feed showing agents 'thinking' in real-time."""
    placeholder = st.empty()
    activities = [
        {"agent": "🔍 LearningAgent", "action": "Analyzing certification requirements", "color": "#4f8ef7"},
        {"agent": "📅 StudyPlanAgent", "action": "Building week-by-week schedule", "color": "#4f8ef7"},
        {"agent": "⏰ EngagementAgent", "action": "Calculating optimal study windows", "color": "#4f8ef7"},
    ]
    for activity in activities:
        with placeholder.container():
            st.markdown(f"""
            <div style='
              display: flex; align-items: center; gap: 12px;
              padding: 16px;
              background: rgba(255,255,255,0.03);
              border-radius: 12px;
              border-left: 3px solid {activity["color"]};
              margin-bottom: 8px;
              animation: pulse 1.5s ease-in-out infinite;
            '>
              <div style='font-size: 20px;'>{activity["agent"].split()[0]}</div>
              <div>
                <div style='font-weight: 600; font-size: 14px;'>{activity["agent"].split()[1]}</div>
                <div style='color: #8b8b9e; font-size: 13px;'>
                  {activity["action"]}
                  <span class='typing-dots'><span>.</span><span>.</span><span>.</span></span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
        time.sleep(0.3)


def render_council_debate_chat(votes: dict):
    """Council debate as live chat bubbles — left/right alternating."""
    agent_config = {
        "optimist": {"icon": "😊", "color": "#00c896", "side": "left"},
        "skeptic": {"icon": "🔍", "color": "#ff4757", "side": "right"},
        "advocate": {"icon": "🛡️", "color": "#ffa502", "side": "left"},
        "historian": {"icon": "📚", "color": "#a855f7", "side": "right"},
        "risk_analyst": {"icon": "⚠️", "color": "#4f8ef7", "side": "left"},
    }
    st.markdown("""
    <div style='background: rgba(255,255,255,0.02); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.06);'>
      <div style='text-align: center; color: #8b8b9e; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px;'>
        ⚖️ Council Debate Room
      </div>
    """, unsafe_allow_html=True)

    for agent, vote in votes.items():
        cfg = agent_config.get(agent, {"icon": "🤖", "color": "#fff", "side": "left"})
        verdict = vote.get("verdict", "")
        confidence = vote.get("confidence", 0)
        evidence = vote.get("evidence", [])
        align = "flex-start" if cfg["side"] == "left" else "flex-end"
        bubble_r = "4px 18px 18px 18px" if cfg["side"] == "left" else "18px 4px 18px 18px"
        v_emoji = "✅" if verdict == "READY" else "❌" if verdict == "NOT_READY" else "⏳"
        flex_end = "justify-content: flex-end;" if cfg["side"] == "right" else ""

        st.markdown(f"""
        <div style='display: flex; justify-content: {align}; margin: 12px 0;'>
          <div style='max-width: 75%;'>
            <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 4px; {flex_end}'>
              <span style='font-size: 18px;'>{cfg["icon"]}</span>
              <span style='font-size: 11px; color: {cfg["color"]}; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;'>{agent.replace("_"," ")}</span>
            </div>
            <div style='background: {cfg["color"]}15; border: 1px solid {cfg["color"]}40; border-radius: {bubble_r}; padding: 12px 16px;'>
              <div style='font-weight: 700; color: {cfg["color"]}; font-size: 14px; margin-bottom: 6px;'>
                {v_emoji} {verdict.replace("_"," ")} <span style='color: #8b8b9e; font-weight: 400; font-size: 12px;'>· {confidence}% confident</span>
              </div>
              <div style='font-size: 13px; color: #d0d0d0; line-height: 1.5;'>"{evidence[0] if evidence else ''}"</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        time.sleep(0.4)

    st.markdown("</div>", unsafe_allow_html=True)


def render_verdict_reveal(verdict: str, confidence: int, reasoning: str):
    """Dramatic verdict reveal with animated SVG confidence ring."""
    color = "#00c896" if verdict == "READY" else "#ff4757" if verdict == "NOT_READY" else "#ffa502"
    icon_s = "🎉" if verdict == "READY" else "⚠️" if verdict == "NOT_READY" else "⏳"
    r = 60
    circ = 2 * 3.14159 * r
    offset = circ * (1 - confidence / 100)
    st.markdown(f"""
    <div style='
      text-align: center; padding: 40px 20px;
      background: radial-gradient(circle at 50% 0%, {color}22 0%, transparent 70%);
      border-radius: 20px; border: 2px solid {color}40;
      margin: 20px 0;
    '>
      <div style='font-size: 56px; margin-bottom: 8px;'>{icon_s}</div>
      <div style='position: relative; width: 140px; height: 140px; margin: 0 auto 20px auto;'>
        <svg width="140" height="140" style="transform: rotate(-90deg);">
          <circle cx="70" cy="70" r="{r}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="10"/>
          <circle cx="70" cy="70" r="{r}" fill="none" stroke="{color}" stroke-width="10"
                  stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round"
                  style="transition: stroke-dashoffset 1.5s ease-out;"/>
        </svg>
        <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 32px; font-weight: 900; color: white;'>{confidence}%</div>
      </div>
      <div style='font-size: 32px; font-weight: 900; color: {color}; letter-spacing: 2px; margin-bottom: 12px;'>{verdict.replace("_"," ")}</div>
      <div style='font-size: 14px; color: #c0c0d0; max-width: 500px; margin: 0 auto; line-height: 1.6;'>{reasoning}</div>
    </div>""", unsafe_allow_html=True)


# ============================================================================
# INTERACTIVE MOCK EXAM — Premium Redesign
# ============================================================================
def render_interactive_exam(state: dict):
    questions = st.session_state.get("questions", [])
    if not questions:
        st.warning("No questions available. Run assessment first.")
        return

    total = len(questions)
    if "exam_state" not in st.session_state:
        st.session_state.exam_state = {
            "current_q": 0, "answers": {}, "time_per_q": {},
            "start_time": time.time(), "q_start_time": time.time(),
            "submitted": False, "show_feedback": False, "last_answer": None
        }

    exam = st.session_state.exam_state
    current_idx = exam["current_q"]

    if exam["submitted"]:
        render_exam_results(questions, exam, state)
        return

    # Header
    progress_pct = current_idx / total
    elapsed = int(time.time() - exam["start_time"])
    mins, secs = elapsed // 60, elapsed % 60
    answered = len(exam["answers"])

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress_pct)
        st.caption(f"Question {current_idx + 1} of {total}")
    with col2:
        st.markdown(f"""<div style='text-align: center; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 8px;'>
          <div style='font-size: 20px; font-weight: 700;'>{mins:02d}:{secs:02d}</div>
          <div style='font-size: 11px; color: #8b8b9e;'>TIME</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div style='text-align: center; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 8px;'>
          <div style='font-size: 20px; font-weight: 700;'>{answered}/{total}</div>
          <div style='font-size: 11px; color: #8b8b9e;'>ANSWERED</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    if current_idx >= total:
        st.success(f"✅ All {total} questions answered!")
        if st.button("📤 Submit Exam & See Results", type="primary", use_container_width=True):
            exam["submitted"] = True
            st.rerun()
        return

    q = questions[current_idx]
    topic = q.get("topic", "")
    question_text = q.get("question", "")
    options = q.get("options", {})
    source = q.get("source", "")

    # Feedback from previous question
    if exam.get("show_feedback") and current_idx > 0:
        prev_q = questions[current_idx - 1]
        prev_answer = exam["last_answer"]
        correct = prev_q.get("correct_answer", "")
        is_correct = prev_answer == correct
        if is_correct:
            st.success(f"✅ Correct! {prev_q.get('explanation', '')}")
        else:
            st.error(f"❌ Incorrect. Correct answer: **{correct}** — {prev_q.get('explanation', '')}")
        exam["show_feedback"] = False
        st.markdown("---")

    # Premium question card
    st.markdown(f"""
    <div style='
      background: linear-gradient(135deg, rgba(79,142,247,0.08), rgba(168,85,247,0.04));
      border: 1px solid rgba(79,142,247,0.2);
      border-radius: 20px; padding: 28px; margin-bottom: 20px;
    '>
      <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;'>
        <div style='background: rgba(79,142,247,0.15); border-radius: 20px; padding: 4px 14px; font-size: 12px; color: #4f8ef7; font-weight: 600;'>
          📚 {topic}
        </div>
        <div style='color: #8b8b9e; font-size: 12px; font-weight: 600;'>
          QUESTION {current_idx + 1} OF {total}
        </div>
      </div>
      <div style='font-size: 19px; font-weight: 600; line-height: 1.6; color: #f5f5f5;'>
        {question_text}
      </div>
    </div>""", unsafe_allow_html=True)

    # Answer options with letter badges
    selected = exam["answers"].get(str(q["id"]), None)

    for opt_key, opt_text in options.items():
        is_selected = selected == opt_key
        col_a, col_b = st.columns([1, 11])
        with col_a:
            bg = "#4f8ef7" if is_selected else "rgba(255,255,255,0.05)"
            txt = "white" if is_selected else "#8b8b9e"
            bdr = "#4f8ef7" if is_selected else "rgba(255,255,255,0.1)"
            st.markdown(f"""<div class='opt-letter' style='background:{bg}; color:{txt}; border:1px solid {bdr};'>{opt_key}</div>""", unsafe_allow_html=True)
        with col_b:
            if st.button(opt_text, key=f"opt_{current_idx}_{opt_key}", use_container_width=True):
                q_time = time.time() - exam["q_start_time"]
                exam["answers"][str(q["id"])] = opt_key
                exam["time_per_q"][str(q["id"])] = q_time
                exam["last_answer"] = opt_key
                exam["show_feedback"] = True
                exam["q_start_time"] = time.time()
                exam["current_q"] = current_idx + 1
                st.rerun()

    if source:
        st.markdown(f"""<div style='color: #555566; font-size: 12px; margin-top: 16px;'>📖 Source: {source}</div>""", unsafe_allow_html=True)

    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if current_idx > 0 and st.button("← Previous", use_container_width=True):
            exam["current_q"] = current_idx - 1
            exam["show_feedback"] = False
            st.rerun()
    with col2:
        nav_html = ""
        for i in range(total):
            q_id = str(questions[i]["id"])
            is_ans = q_id in exam["answers"]
            is_curr = i == current_idx
            c = "#4f8ef7" if is_curr else "#00c896" if is_ans else "#333"
            nav_html += f"<span style='display:inline-block; width:24px; height:24px; background:{c}; border-radius:4px; margin:2px; text-align:center; font-size:11px; line-height:24px;'>{i+1}</span>"
        st.markdown(nav_html, unsafe_allow_html=True)
    with col3:
        if current_idx < total - 1:
            if st.button("Next →", type="primary", use_container_width=True):
                exam["current_q"] = current_idx + 1
                exam["show_feedback"] = False
                st.rerun()
        else:
            if st.button("Finish ✓", type="primary", use_container_width=True):
                exam["submitted"] = True
                st.rerun()


def render_exam_results(questions: list, exam: dict, state: dict):
    """Exam results with premium styling."""
    if "results_loaded" not in st.session_state:
        with st.spinner("Calculating results..."):
            result = post_api("submit", {"learner_id": state.get("learner_id", "L-1001"), "answers": exam["answers"]})
        st.session_state.exam_results = result
        st.session_state.results_loaded = True

    result = st.session_state.get("exam_results", {})
    score = result.get("score", 0)
    outcome = result.get("outcome", "FAIL")
    breakdown = result.get("topic_breakdown", {})
    color = "#00c896" if outcome == "PASS" else "#ff4757"
    icon_s = "🎉" if outcome == "PASS" else "❌"

    # Results header
    st.markdown(f"""
    <div style='background:{color}11; border:2px solid {color}; border-radius:20px; padding:32px; text-align:center; margin-bottom:24px;'>
      <div style='font-size:48px;'>{icon_s}</div>
      <div style='font-size:48px; font-weight:900; color:{color};'>{outcome}</div>
      <div style='font-size:64px; font-weight:900; color:white; margin:8px 0;'>{score:.1f}%</div>
      <div style='font-size:14px; color:#8b8b9e;'>{len(exam["answers"])} questions · Passing score: 70% · Time: {int((time.time()-exam["start_time"])//60)}m</div>
    </div>""", unsafe_allow_html=True)

    try:
        from frontend.components.verdict_explainer import render_verdict_explainer
        render_verdict_explainer(get_api_state())
    except:
        pass

    # Topic breakdown chart
    if breakdown and isinstance(breakdown, dict):
        topics = list(breakdown.keys())
        scores_vals = [breakdown[t].get("score", 0) if isinstance(breakdown[t], dict) else 0 for t in topics]
        colors = ["#00c896" if s >= 70 else "#ffa502" if s >= 50 else "#ff4757" for s in scores_vals]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=topics, x=scores_vals, orientation="h", marker_color=colors, text=[f"{s:.0f}%" for s in scores_vals], textposition="auto"))
        fig.add_vline(x=70, line_dash="dash", line_color="#ffa502", annotation_text="Pass threshold")
        fig.update_layout(title="Performance by Topic", xaxis_title="Score %", xaxis_range=[0, 100], height=max(200, len(topics) * 45),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#f0f0f0"), margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # Question review
    st.markdown("### 📋 Question Review")
    st.caption("See exactly what went wrong and why")
    for q in questions:
        qid = str(q["id"])
        user_answer = exam["answers"].get(qid, "?")
        correct = q.get("correct_answer", "")
        is_correct = user_answer == correct
        with st.expander(f"{'✅' if is_correct else '❌'} Q{q['id']}: {q['question'][:80]}...", expanded=not is_correct):
            st.write(q["question"])
            options_exp = q.get("options", {})
            for opt_k, opt_v in options_exp.items():
                if opt_k == correct:
                    st.success(f"✅ **{opt_k}.** {opt_v}")
                elif opt_k == user_answer and opt_k != correct:
                    st.error(f"❌ **{opt_k}.** {opt_v} (Your answer)")
                else:
                    st.write(f"⚪ **{opt_k}.** {opt_v}")
            st.info(f"💡 {q.get('explanation', '')}")

    # Adaptive path if failed
    if outcome == "FAIL":
        st.markdown("---")
        st.markdown("### 🔄 Adapt Your Learning Path")
        if st.button("🔄 Regenerate Learning Path for Weak Topics", type="primary", use_container_width=True):
            with st.spinner("Adapting your learning path..."):
                result = post_api("adaptive", {"learner_id": state.get("learner_id", "L-1001"), "max_iterations": 1})
            if result:
                st.success("✅ Learning path updated!")
                st.rerun()

        # Learning resources for weak topics
        st.markdown("---")
        st.markdown("### 📚 Learning Resources for Weak Topics")
        weak_topics = state.get("weak_topics", [])
        if weak_topics:
            from backend.plugins.resource_finder import find_resources
            cert = state.get("certification", "")
            for topic in weak_topics[:3]:
                with st.expander(f"📖 {topic} — Study Materials"):
                    try:
                        resources = find_resources(cert, topic)
                        official = resources.get("official", [])
                        if official:
                            st.markdown("**📘 Microsoft Learn (Official)**")
                            for r in official:
                                st.markdown(f"→ [{r.get('title', 'Learn more')}]({r.get('url', '#')}) *{r.get('duration', '')}*")

                        mvp = resources.get("mvp", [])
                        if mvp:
                            st.markdown("**⭐ Microsoft MVP Content**")
                            for r in mvp:
                                st.markdown(f"""<div class='resource-card'><div style='font-size:20px;'>⭐</div><div>
                                  <a href='{r.get("url","#")}' target='_blank' style='color:#ffa502; font-weight:600; text-decoration:none;'>{r.get("title","Learn more")}</a>
                                  <div style='color:#8b8b9e; font-size:12px;'>{r.get("source","")} · {r.get("type","")}</div></div></div>""", unsafe_allow_html=True)

                        videos = resources.get("videos", [])
                        if videos:
                            st.markdown("**🎬 Video Tutorials**")
                            for r in videos:
                                st.markdown(f"→ [{r.get('title', 'Watch')}]({r.get('url', '#')})")

                        practice = resources.get("practice", [])
                        if practice:
                            st.markdown("**💻 Hands-On Practice**")
                            for r in practice:
                                st.markdown(f"→ [{r.get('title', 'Try')}]({r.get('url', '#')})")
                    except:
                        st.write(f"Resources for {topic}...")

    # Retake / view report
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if outcome == "FAIL" and st.button("🔁 Retake Exam", use_container_width=True):
            for key in ["exam_state", "questions", "results_loaded", "exam_results"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("📊 View Full Report", type="primary", use_container_width=True):
            st.session_state.page = "⚖️ Council Debate"
            st.rerun()


# ============================================================================
# MAIN PIPELINE VIEW (Primary)
# ============================================================================
def render_pipeline():
    """Main page with hero section, glass input card, and consolidated results."""

    # HERO SECTION
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px 40px 20px;
         background: radial-gradient(circle at 50% 0%, rgba(79,142,247,0.15) 0%, transparent 60%);'>
      <div style='display: inline-block; background: rgba(79,142,247,0.1);
           border: 1px solid rgba(79,142,247,0.3); border-radius: 30px;
           padding: 6px 18px; font-size: 12px; color: #4f8ef7;
           margin-bottom: 20px; letter-spacing: 1px;'>
        ⚡ POWERED BY AZURE AI FOUNDRY · 13 AGENTS
      </div>
      <div style='font-size: 42px; font-weight: 900;
           background: linear-gradient(135deg, #ffffff, #a855f7);
           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
           line-height: 1.2; margin-bottom: 12px;'>
        Will You Pass Your<br/>Certification Exam?
      </div>
      <div style='color: #8b8b9e; font-size: 16px; max-width: 600px; margin: 0 auto;'>
        5 AI agents debate your readiness. A coach diagnoses your gaps. The system learns from every outcome.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Input card
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    with st.form("pipeline_form"):
        col1, col2 = st.columns(2)
        state = get_api_state()
        with col1:
            learner_id = st.text_input("Learner ID", value=state.get("learner_id") or "L-1001")
            certification = st.text_input("Certification", value=state.get("certification") or "AZ-204",
                                          help="Any Microsoft cert: AZ-204, AZ-400, SC-900...")
        with col2:
            role = st.text_input("Role", value=state.get("role") or "Cloud Engineer")
            target_weeks = st.slider("Target weeks", 1, 12, value=state.get("target_weeks") or 6)
        submitted = st.form_submit_button("🚀 Run Full Analysis", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        run_automated_pipeline(learner_id, role, certification, target_weeks)
    elif state.get("skill_map"):
        show_consolidated_results()


# ============================================================================
# PIPELINE EXECUTION — Premium Animated
# ============================================================================
def run_automated_pipeline(learner_id, role, certification, target_weeks):
    st.markdown("---")
    st.subheader("🔄 Running Analysis Pipeline")

    overall_progress = st.progress(0)
    current_phase_text = st.empty()

    phase_containers = {
        "learning": st.container(),
        "council": st.container(),
        "assessment": st.container(),
        "coaching": st.container(),
        "reflection": st.container(),
    }
    consolidated_container = st.container()

    # PHASE 1: Learning
    current_phase_text.write("📚 Building learning plan...")
    overall_progress.progress(0.1)

    with phase_containers["learning"]:
        render_agent_activity_feed()

        with st.status("📚 Phase 1: Building Learning Plan", expanded=True) as status:
            st.write("🔍 Querying knowledge base...")
            st.write("🗺️ Building skill map...")
            st.write("📅 Generating study schedule...")
            st.write("⏰ Calculating study windows...")

            learning_result = post_api("learn", {"learner_id": learner_id, "role": role, "certification": certification, "target_weeks": target_weeks})
            if not learning_result:
                status.update(label="❌ Learning phase failed", state="error")
                return
            status.update(label="✅ Phase 1 Complete — Learning Plan Ready", state="complete")

        state = get_api_state()
        skill_map = state.get("skill_map", [])
        skill_count = len(skill_map)
        weak_topics = state.get("weak_topics", [])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(render_stat_card("📚", "Skills Identified", str(skill_count), color="#4f8ef7"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_stat_card("📅", "Study Weeks", str(target_weeks), color="#a855f7"), unsafe_allow_html=True)
        with col3:
            risk = state.get("work_signals", {}).get("workload_risk", "Unknown")
            st.markdown(render_stat_card("⚡", "Workload Risk", risk, color="#ffa502"), unsafe_allow_html=True)

        # Skill tags with weak topic highlighting
        if skill_map:
            with st.expander(f"📚 View Skill Map ({skill_count} skills)"):
                html = ""
                for skill in skill_map:
                    is_weak = skill in weak_topics
                    cls = "skill-tag weak" if is_weak else "skill-tag"
                    icon_s = "⚠️ " if is_weak else ""
                    html += f'<span class="{cls}">{icon_s}{skill}</span>'
                st.markdown(html, unsafe_allow_html=True)

    overall_progress.progress(0.2)

    # PHASE 2: Council — with live chat
    current_phase_text.write("⚖️ Convening readiness council...")

    with phase_containers["council"]:
        with st.status("⚖️ Phase 2: Readiness Council Debate", expanded=True) as status:
            st.write("😊 Optimist analyzing strengths...")
            st.write("🔍 Skeptic finding weaknesses...")
            st.write("🛡️ Advocate checking workload...")
            st.write("📚 Historian searching past patterns...")
            st.write("⚠️ Risk Analyst calculating gaps...")

            council_result = post_api("readiness", {"learner_id": learner_id})
            st.write("⚖️ Critic synthesising weighted votes...")

            if not council_result:
                status.update(label="❌ Council phase failed", state="error")
                return

            votes = council_result.get("council_votes", {})
            verdicts_set = [v.get("verdict") for v in votes.values()]
            has_discrepancy = len(set(verdicts_set)) > 2
            if has_discrepancy:
                st.write("⚡ Discrepancy detected — adapting learning plan...")
            status.update(label="✅ Phase 2 Complete — Verdict Ready", state="complete")

        # Show chat-style debate
        state = get_api_state()
        votes = state.get("council_votes", {})
        if votes:
            render_council_debate_chat(votes)

        # Verdict reveal
        verdict = state.get("readiness_verdict", "")
        confidence = state.get("readiness_confidence", 0)
        reasoning = state.get("readiness_reasoning", "")
        if verdict:
            render_verdict_reveal(verdict, confidence, reasoning)

        # Show adaptations
        adaptations = state.get("adaptations", [])
        if adaptations:
            for a in adaptations:
                st.warning(f"⚡ Plan adapted: {a.get('reason')}  \nAction: {a.get('action')}")

    overall_progress.progress(0.4)

    # PHASE 3: Assessment
    current_phase_text.write("📝 Running mock assessment...")

    with phase_containers["assessment"]:
        with st.status("📝 Phase 3: Mock Assessment", expanded=True) as status:
            st.write("📋 Generating exam questions from Foundry IQ...")
            assessment_result = post_api("assessment", {"learner_id": learner_id})
            if not assessment_result:
                status.update(label="❌ Assessment phase failed", state="error")
                return
            questions = assessment_result.get("questions", [])
            st.write(f"✅ {len(questions)} questions generated")
            st.write("📤 Auto-evaluating based on practice score...")

            state = get_api_state()
            practice_score = 65
            simulated = {}
            for q in questions:
                qid = str(q["id"])
                correct = q.get("correct_answer", "A")
                opts = list(q.get("options", {}).keys())
                if random.random() < (practice_score / 100):
                    simulated[qid] = correct
                else:
                    wrong = [o for o in opts if o != correct]
                    simulated[qid] = random.choice(wrong) if wrong else correct

            submit_result = post_api("submit", {"learner_id": learner_id, "answers": simulated})
            if not submit_result:
                status.update(label="❌ Assessment submission failed", state="error")
                return
            score = submit_result.get("score", 0)
            outcome = submit_result.get("outcome", "")
            status.update(label=f"✅ Phase 3 Complete — Score: {score:.1f}% ({outcome})", state="complete")

        state = get_api_state()
        score = state.get("assessment_score", 0)
        outcome = state.get("assessment_outcome", "")
        breakdown = state.get("assessment_breakdown", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(render_stat_card("📝", "Assessment Score", f"{score:.1f}%", "Above threshold" if score >= 70 else "Below threshold",
                                          trend_positive=score >= 70, color="#00c896" if score >= 70 else "#ff4757"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_stat_card("📋", "Questions", f"{len(simulated)}/{len(questions)}", color="#4f8ef7"), unsafe_allow_html=True)
        with col3:
            st.markdown(render_stat_card("🎯", "Outcome", outcome, color="#00c896" if outcome == "PASS" else "#ff4757"), unsafe_allow_html=True)
        with col4:
            weak_count = len(state.get("weak_topics", []))
            st.markdown(render_stat_card("⚠️", "Weak Topics", str(weak_count), color="#ffa502"), unsafe_allow_html=True)

        if breakdown:
            topics = list(breakdown.keys())
            scores_vals = [breakdown[t]["score"] for t in topics]
            colors = ["green" if s >= 70 else "red" for s in scores_vals]
            fig = go.Figure(go.Bar(x=scores_vals, y=topics, orientation='h', marker_color=colors))
            fig.add_vline(x=70, line_dash="dash", line_color="yellow", annotation_text="70% threshold")
            fig.update_layout(title="Topic Performance", height=250, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

        if outcome == "FAIL":
            weak = state.get("weak_topics", [])
            st.warning(f"⚡ Study plan adapted: Added reinforcement for {', '.join(weak[:3])}")

    overall_progress.progress(0.6)

    # PHASE 4: Coaching
    current_phase_text.write("🧠 Running Socratic coaching...")

    with phase_containers["coaching"]:
        state = get_api_state()
        outcome = state.get("assessment_outcome", "")

        if outcome == "FAIL":
            with st.status("🧠 Phase 4: Socratic Coaching", expanded=True) as status:
                st.write("🔍 Identifying root misconceptions...")
                st.write("❓ Generating Socratic questions...")
                st.write("📋 Building remediation plan...")
                coaching_result = post_api("coaching", {"learner_id": learner_id})
                status.update(label="✅ Phase 4 Complete — Diagnosis Ready", state="complete")

            state = get_api_state()
            misconceptions = state.get("misconceptions", [])
            socratic_qs = state.get("socratic_questions", [])
            remediation = state.get("remediation", {})

            if misconceptions:
                st.error(f"🔍 Root misconception: {misconceptions[0]}")
            if socratic_qs:
                with st.expander(f"❓ {len(socratic_qs)} Socratic Questions"):
                    for i, q in enumerate(socratic_qs):
                        st.markdown(f"**Q{i+1}:** {q.get('question', '')}")
                        st.caption(f"💡 Leads to: {q.get('leads_to', '')}")
            if remediation:
                st.info(f"📋 Remediation: {remediation.get('study_approach', '')}  \n⏱️ Estimated: {remediation.get('estimated_hours', 0)} hours")
        else:
            with st.status("🧠 Phase 4: Coaching", expanded=False) as status:
                status.update(label="✅ Phase 4 Skipped — Assessment Passed", state="complete")
            st.success("🎉 No coaching needed — learner is ready!")

    overall_progress.progress(0.8)

    # PHASE 5: Reflection
    current_phase_text.write("🔄 Running reflection...")

    with phase_containers["reflection"]:
        with st.status("🔄 Phase 5: Reflection & Agent Learning", expanded=True) as status:
            st.write("📊 Comparing prediction vs actual outcome...")
            st.write("🏆 Updating agent reputation scores...")
            st.write("🧠 Generating system learning insights...")
            state = get_api_state()
            actual_outcome = state.get("assessment_outcome", "FAIL")
            reflection_result = post_api("reflection", {"learner_id": learner_id, "actual_outcome": actual_outcome})
            status.update(label="✅ Phase 5 Complete — Agents Updated", state="complete")

        reflection = reflection_result.get("reflection", {})
        rep_scores = reflection_result.get("updated_reputation", [])

        if reflection.get("analysis"):
            st.info(f"💡 {reflection.get('analysis', '')}")

        if rep_scores:
            cols = st.columns(len(rep_scores))
            for i, agent in enumerate(sorted(rep_scores, key=lambda x: x.get("accuracy_score", 0), reverse=True)):
                with cols[i]:
                    score = agent.get("accuracy_score", 75)
                    name = agent.get("agent_name", "")
                    c = "green" if score >= 80 else "orange" if score >= 70 else "red"
                    st.markdown(f"**{name.title()}**  \n:{c}[{score:.1f}%]")

    overall_progress.progress(1.0)
    current_phase_text.write("✅ Pipeline complete!")

    # COMPLETION BANNER
    state = get_api_state()
    verdict = state.get("readiness_verdict", "")
    score = state.get("assessment_score", 0)
    adaptations_count = len(state.get("adaptations", []))

    if verdict:
        if verdict == "READY":
            b_color, b_emoji, b_text = "#00aa00", "✅", "READY FOR EXAM"
        elif verdict == "NOT_READY":
            b_color, b_emoji, b_text = "#ff4444", "❌", "MORE STUDY NEEDED"
        else:
            b_color, b_emoji, b_text = "#ffaa00", "⏳", "EXAM DELAYED"
        st.markdown(f"""<div style='background: linear-gradient(90deg, {b_color}22 0%, {b_color}11 100%); border-left: 5px solid {b_color}; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;'>
          <div style='font-size: 36px; margin-bottom: 10px;'>{b_emoji}</div>
          <div style='font-size: 28px; font-weight: bold; color:{b_color}; margin-bottom: 10px;'>{b_text}</div>
          <div style='font-size: 16px; color: white; margin: 10px 0;'><strong>Assessment Score:</strong> {score:.1f}% | <strong>Plan Adaptations:</strong> {adaptations_count}</div>
        </div>""", unsafe_allow_html=True)

    # CONSOLIDATED REPORT
    with consolidated_container:
        st.markdown("---")
        st.subheader("📋 Consolidated Analysis Report")
        state = get_api_state()
        verdict = state.get("readiness_verdict", "")
        score = state.get("assessment_score", 0)
        adaptations = state.get("adaptations", [])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(render_stat_card("⚖️", "Readiness Verdict", verdict, f"{state.get('readiness_confidence', 0)}% confidence", color="#00c896" if verdict=="READY" else "#ff4757"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_stat_card("📝", "Assessment Score", f"{score:.1f}%", "Above threshold" if score>=70 else "Below threshold", trend_positive=score>=70, color="#00c896" if score>=70 else "#ff4757"), unsafe_allow_html=True)
        with col3:
            st.markdown(render_stat_card("⚡", "Plan Adaptations", str(len(adaptations)), "Auto-applied" if adaptations else "None needed", color="#ffa502"), unsafe_allow_html=True)
        with col4:
            st.markdown(render_stat_card("🎯", "Weak Topics", str(len(state.get("weak_topics", []))), color="#4f8ef7"), unsafe_allow_html=True)

        if adaptations:
            st.subheader("⚡ Adaptations Made to Your Plan")
            for i, a in enumerate(adaptations):
                with st.expander(f"Adaptation {i+1}: {a.get('reason', '')}"):
                    st.write(f"**Action taken:** {a.get('action', '')}")
                    if a.get("signals"):
                        st.write("**Signals detected:**")
                        for s in a.get("signals", []):
                            st.write(f"  • {s}")

        # Final study plan
        st.subheader("📅 Final Study Plan")
        study_plan = state.get("study_plan", {})
        for week, data in study_plan.items():
            if not isinstance(data, dict):
                continue
            week_data = get_week_data(data)
            adapted = data.get("adapted", False)
            label = f"{week}: {week_data['focus']}"
            if adapted:
                label += " ⚡ (adapted)"
            with st.expander(label):
                st.write(f"**Topics:** {', '.join(week_data['topics'])}")
                st.write(f"**Hours:** {week_data['hours']}")
                st.write(f"**Milestone:** {week_data['milestone']}")
                if week_data['resources']:
                    st.write(f"**Resources:** {', '.join(week_data['resources'])}")
                if adapted:
                    st.info("✨ This week was adapted based on findings")

        # Next action
        st.subheader("🎯 Recommended Next Action")
        if verdict == "READY":
            st.success("✅ You are ready to book your exam. Schedule within the next 5-7 days while knowledge is fresh.")
        elif verdict == "DELAY":
            st.warning("⏳ Delay your exam by 1-2 weeks. Follow the adapted study plan focusing on weak topics.")
        else:
            weak = state.get("weak_topics", [])
            if not weak:
                breakdown = state.get("assessment_breakdown", {})
                if breakdown:
                    weak = [t for t, d in breakdown.items() if d.get("score", 100) < 70]
            if not weak:
                weak = ["Review all exam domains"]
            st.error(f"❌ Not ready yet. Focus on: {', '.join(weak[:3])}. Re-run analysis after 2 weeks of focused study.")

        # Export
        report_data = {
            "learner_id": state.get("learner_id"),
            "certification": state.get("certification"),
            "verdict": verdict,
            "score": score,
            "study_plan": study_plan,
            "weak_topics": state.get("weak_topics", []),
            "adaptations": adaptations,
            "session_log": state.get("session_log", [])
        }
        st.download_button("📥 Export Full Report", data=json.dumps(report_data, indent=2),
                           file_name=f"certops_{state.get('learner_id','')}_{state.get('certification','')}.json", mime="application/json")


def show_consolidated_results():
    """Show results if pipeline has been run before."""
    st.markdown("---")
    st.subheader("📋 Last Analysis Results")
    state = get_api_state()
    verdict = state.get("readiness_verdict", "")
    score = state.get("assessment_score", 0)
    adaptations = state.get("adaptations", [])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_stat_card("⚖️", "Readiness Verdict", verdict, f"{state.get('readiness_confidence', 0)}% confidence", color="#00c896" if verdict=="READY" else "#ff4757"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_stat_card("📝", "Assessment Score", f"{score:.1f}%", "Above threshold" if score>=70 else "Below threshold", trend_positive=score>=70, color="#00c896" if score>=70 else "#ff4757"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_stat_card("⚡", "Plan Adaptations", str(len(adaptations)), "Auto-applied" if adaptations else "None needed", color="#ffa502"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_stat_card("🎯", "Weak Topics", str(len(state.get("weak_topics", []))), color="#4f8ef7"), unsafe_allow_html=True)

    if adaptations:
        st.subheader("⚡ Adaptations Made to Your Plan")
        for i, a in enumerate(adaptations):
            with st.expander(f"Adaptation {i+1}: {a.get('reason', '')}"):
                st.write(f"**Action taken:** {a.get('action', '')}")
                if a.get("signals"):
                    st.write("**Signals detected:**")
                    for s in a.get("signals", []):
                        st.write(f"  • {s}")

    st.subheader("📅 Final Study Plan")
    study_plan = state.get("study_plan", {})
    for week, data in study_plan.items():
        adapted = data.get("adapted", False)
        label = f"{week}: {data.get('focus', '')}"
        if adapted:
            label += " ⚡ (adapted)"
        with st.expander(label):
            st.write(f"**Topics:** {', '.join(data.get('topics', []))}")
            st.write(f"**Hours:** {data.get('hours', 0)}")
            st.write(f"**Milestone:** {data.get('milestone', '')}")
            if adapted:
                st.info("✨ This week was adapted based on findings")

    st.divider()
    st.info("→ Use sidebar to explore deep-dive views")


# ============================================================================
# DEEP-DIVE PAGES (Read-Only)
# ============================================================================
def render_council_deepdive():
    st.title("⚖️ Council Debate — Deep Dive")
    st.markdown("Review the detailed council voting breakdown from the pipeline")
    state = get_api_state()
    votes = state.get("council_votes", {})

    if not votes:
        st.warning("Run the pipeline first to see council votes")
        return

    # Use chat-style debate instead of cards
    render_council_debate_chat(votes)

    # Critic verdict
    st.divider()
    verdict = state.get("readiness_verdict", "")
    confidence = state.get("readiness_confidence", 0)
    reasoning = state.get("readiness_reasoning", "")
    if verdict:
        render_verdict_reveal(verdict, confidence, reasoning)


def render_manager_insights():
    st.title("📊 Manager Insights")
    st.markdown("Team-level analytics from pipeline executions")
    try:
        insights = get_api("manager")
        if not insights or not insights.get("learners"):
            st.info("No team data available yet. Run pipeline to see insights.")
            return
        learners = insights.get("learners", [])
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ready = sum(1 for l in learners if l.get("readiness_verdict") == "READY")
            st.markdown(render_stat_card("✅", "Ready", f"{ready}/{len(learners)}", color="#00c896"), unsafe_allow_html=True)
        with col2:
            avg_score = sum(l.get("assessment_score", 0) for l in learners) / len(learners) if learners else 0
            st.markdown(render_stat_card("📊", "Avg Score", f"{avg_score:.0f}%", color="#4f8ef7"), unsafe_allow_html=True)
        with col3:
            failed = sum(1 for l in learners if l.get("assessment_outcome") == "FAIL")
            st.markdown(render_stat_card("⚠️", "At Risk", str(failed), color="#ff4757"), unsafe_allow_html=True)
        with col4:
            completed = sum(1 for l in learners if l.get("reflection"))
            st.markdown(render_stat_card("🔄", "Completed", str(completed), color="#a855f7"), unsafe_allow_html=True)

        st.divider()
        st.subheader("👥 Learner Status")
        learner_data = []
        for l in learners:
            learner_data.append({
                "ID": l.get("learner_id", ""),
                "Cert": l.get("certification", ""),
                "Plan": "✅" if l.get("skill_map") else "⭕",
                "Council": "✅" if l.get("readiness_verdict") else "⭕",
                "Assessment": f"{l.get('assessment_score', 0):.0f}%" if l.get('assessment_score') else "⭕",
                "Outcome": l.get("assessment_outcome", "⭕"),
            })
        st.dataframe(learner_data, use_container_width=True, hide_index=True)

        weak_topics = insights.get("weak_topics", {})
        if weak_topics:
            st.subheader("📉 Topic Weakness Patterns")
            for topic, count in sorted(weak_topics.items(), key=lambda x: x[1], reverse=True)[:5]:
                st.write(f"• **{topic}** — {count} learners struggling")
    except Exception as e:
        st.error(f"Error loading manager insights: {e}")


def render_agent_reputation():
    st.title("🏆 Agent Reputation")
    st.markdown("Agent prediction accuracy from all pipeline runs")
    try:
        rep_data = get_api("reputation")
        agents = rep_data.get("agents", [])
        if not agents:
            st.info("No reputation data yet. Run pipeline to see agent performance.")
            return

        agent_names = [a.get("agent_name", "").upper() for a in agents]
        accuracies = [a.get("accuracy_score", 0) for a in agents]
        fig = go.Figure(go.Bar(x=agent_names, y=accuracies,
                               marker_color=["green" if x >= 80 else "orange" if x >= 70 else "red" for x in accuracies],
                               text=[f"{x:.0f}%" for x in accuracies], textposition="auto"))
        fig.update_layout(title="Agent Accuracy Comparison", xaxis_title="Agent", yaxis_title="Accuracy %", height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Detailed Scores")
        agent_table = []
        for a in agents:
            total = a.get("total_predictions", 0)
            correct = a.get("correct_predictions", 0)
            wrong = total - correct
            agent_table.append({
                "Agent": a.get("agent_name", "").upper(),
                "Accuracy": f"{a.get('accuracy_score', 0):.1f}%",
                "Total": total, "Correct": correct, "Wrong": wrong,
            })
        st.dataframe(agent_table, use_container_width=True, hide_index=True)
        st.info("💡 Higher accuracy agents have more influence on readiness verdicts.")
    except Exception as e:
        st.error(f"Error loading reputation data: {e}")


def render_reasoning_trace():
    st.title("🔍 Reasoning Trace")
    st.markdown("Complete execution log from pipeline")
    state = get_api_state()
    session_log = state.get("session_log", [])
    if not session_log:
        st.info("No reasoning log available. Run pipeline to generate logs.")
        return
    with st.expander("📜 Full Execution Log", expanded=True):
        for i, log in enumerate(session_log):
            st.text(f"[{i+1}] {log}")
    st.divider()
    st.caption(f"Total log entries: {len(session_log)}")


# ============================================================================
# MAIN ROUTER
# ============================================================================
if page == "🏠 Pipeline (Main)":
    render_pipeline()
elif page == "⚖️ Council Debate":
    render_council_deepdive()
elif page == "📊 Manager Insights":
    render_manager_insights()
elif page == "🏆 Agent Reputation":
    render_agent_reputation()
elif page == "🔍 Reasoning Trace":
    render_reasoning_trace()