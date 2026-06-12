"""
CertOps AI - Single-Pipeline Automated Certification Readiness Platform
Runs complete orchestration with single button. Multi-page deep-dive views remain for inspection.
"""

import streamlit as st
import httpx
import json
import plotly.graph_objects as go
from frontend.state import get_api_state, post_api, get_api, has_completed_phase, show_phase_guard

st.set_page_config(
    page_title="CertOps AI",
    page_icon="🎓",
    layout="wide"
)

# ============================================================================
# SIDEBAR: Status + Deep-Dive Navigation
# ============================================================================
st.sidebar.title("🎓 CertOps AI")
st.sidebar.markdown("*Self-Learning Certification Readiness Intelligence Platform*")

# Status indicators
st.sidebar.divider()
st.sidebar.markdown("### Session Status")
state = get_api_state()

def status_badge(condition, label, detail=""):
    icon = "✅" if condition else "⭕"
    if condition and detail:
        st.sidebar.write(f"{icon} {label}: {detail}")
    else:
        st.sidebar.write(f"{icon} {label}")

status_badge(
    bool(state.get("skill_map")),
    "Learning Plan",
    f"{len(state.get('skill_map', []))} skills"
)
status_badge(
    bool(state.get("readiness_verdict")),
    "Council Verdict",
    state.get("readiness_verdict", "")
)
status_badge(
    bool(state.get("assessment_outcome")),
    "Assessment",
    f"{state.get('assessment_score', 0):.0f}%"
)
status_badge(
    bool(state.get("misconceptions")),
    "Coaching",
    "Diagnosed" if state.get("misconceptions") else ""
)
status_badge(
    bool(state.get("reflection")),
    "Reflection",
    "Complete" if state.get("reflection") else ""
)

# Deep-dive navigation (secondary)
st.sidebar.divider()
st.sidebar.markdown("### Deep Dive")
page = st.sidebar.selectbox(
    "View Details",
    [
        "🏠 Pipeline (Main)",
        "⚖️ Council Debate",
        "📊 Manager Insights",
        "🏆 Agent Reputation",
        "🔍 Reasoning Trace"
    ]
)

# System health
st.sidebar.divider()
with st.sidebar.expander("🔧 System Status"):
    try:
        health = httpx.get(
            "http://localhost:8000/health", 
            timeout=3
        ).json()
        st.write(f"✅ API: {health.get('status')}")
    except:
        st.write("❌ API: Offline")
    
    state_check = get_api_state()
    st.write(
        f"💾 Memory: {'Active' if state_check.get('learner_id') else 'Empty'}"
    )

st.sidebar.divider()
if st.sidebar.button("🔄 Reset Demo", use_container_width=True):
    get_api("reset-demo")
    st.sidebar.success("✅ Demo reset!")
    st.rerun()

def get_week_data(week_data: dict) -> dict:
    """Extract week data handling multiple key format variations"""
    return {
        "focus": (
            week_data.get("focus") or 
            week_data.get("theme") or 
            week_data.get("title") or 
            "Study session"
        ),
        "topics": (
            week_data.get("topics") or 
            week_data.get("activities") or 
            week_data.get("skills") or 
            []
        ),
        "hours": (
            week_data.get("hours") or 
            week_data.get("duration") or 
            week_data.get("study_hours") or 
            5
        ),
        "milestone": (
            week_data.get("milestone") or 
            week_data.get("goal") or 
            week_data.get("outcome") or 
            ""
        ),
        "resources": (
            week_data.get("resources") or 
            week_data.get("materials") or 
            []
        )
    }


# ============================================================================
# MAIN PIPELINE VIEW (Primary)
# ============================================================================
def render_pipeline():
    """Main automated pipeline view — single page, all phases"""
    st.title("🎓 CertOps AI")
    st.caption("Self-Learning Certification Readiness Platform")
    
    # Input section
    with st.form("pipeline_form"):
        col1, col2 = st.columns(2)
        state = get_api_state()
        
        with col1:
            learner_id = st.text_input(
                "Learner ID", 
                value=state.get("learner_id") or "L-1001"
            )
            certification = st.text_input(
                "Certification",
                value=state.get("certification") or "AZ-204",
                help="Any Microsoft cert: AZ-204, AZ-400, SC-900..."
            )
        with col2:
            role = st.text_input(
                "Role",
                value=state.get("role") or "Cloud Engineer"
            )
            target_weeks = st.slider("Target weeks", 1, 12, value=state.get("target_weeks") or 6)
        
        submitted = st.form_submit_button(
            "🚀 Run Full Analysis",
            type="primary",
            use_container_width=True
        )
    
    if submitted:
        run_automated_pipeline(learner_id, role, certification, target_weeks)
    
    # Show results if pipeline has completed any phase
    elif state.get("skill_map"):
        show_consolidated_results()


# ============================================================================
# PIPELINE EXECUTION
# ============================================================================
def run_automated_pipeline(learner_id, role, certification, target_weeks):
    """
    Shows live progress as pipeline executes.
    Results appear as each phase completes.
    """
    st.markdown("---")
    st.subheader("🔄 Running Analysis Pipeline")
    
    # Overall progress bar
    overall_progress = st.progress(0)
    current_phase_text = st.empty()
    
    # Phase result containers — pre-create so they fill in order
    phase_containers = {}
    phase_containers["learning"] = st.container()
    phase_containers["council"] = st.container()
    phase_containers["assessment"] = st.container()
    phase_containers["coaching"] = st.container()
    phase_containers["reflection"] = st.container()
    consolidated_container = st.container()

    # PHASE 1: Learning
    current_phase_text.write("📚 Building learning plan...")
    overall_progress.progress(0.1)
    
    with phase_containers["learning"]:
        with st.status(
            "📚 Phase 1: Building Learning Plan",
            expanded=True
        ) as status:
            st.write("🔍 Querying knowledge base...")
            st.write("🗺️ Building skill map...")
            st.write("📅 Generating study schedule...")
            st.write("⏰ Calculating study windows...")
            
            learning_result = post_api("learn", {
                "learner_id": learner_id,
                "role": role,
                "certification": certification,
                "target_weeks": target_weeks
            })
            
            if not learning_result:
                status.update(
                    label="❌ Learning phase failed", 
                    state="error"
                )
                return
            
            status.update(
                label="✅ Phase 1 Complete — Learning Plan Ready",
                state="complete"
            )
        
        # Show learning results inline
        state = get_api_state()
        skill_map = state.get("skill_map", [])
        skill_count = len(skill_map)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Skills Identified",
                skill_count
            )
        with col2:
            st.metric("Study Weeks", target_weeks)
        with col3:
            risk = state.get("work_signals", {}).get(
                "workload_risk", "Unknown"
            )
            st.metric("Workload Risk", risk)
        
        # Show skill map if available
        if skill_map:
            with st.expander(f"📚 View Skill Map ({skill_count} skills)"):
                cols = st.columns(2)
                for i, skill in enumerate(skill_map):
                    cols[i % 2].write(f"• {skill}")

    overall_progress.progress(0.2)

    # PHASE 2: Council
    current_phase_text.write("⚖️ Convening readiness council...")
    
    with phase_containers["council"]:
        with st.status(
            "⚖️ Phase 2: Readiness Council Debate",
            expanded=True
        ) as status:
            st.write("😊 Optimist analyzing strengths...")
            st.write("🔍 Skeptic finding weaknesses...")
            st.write("🛡️ Advocate checking workload...")
            st.write("📚 Historian searching past patterns...")
            st.write("⚠️ Risk Analyst calculating gaps...")
            
            council_result = post_api("readiness", {
                "learner_id": learner_id
            })
            
            st.write("⚖️ Critic synthesising weighted votes...")
            
            if not council_result:
                status.update(
                    label="❌ Council phase failed",
                    state="error"
                )
                return
            
            # Check for discrepancies
            votes = council_result.get("council_votes", {})
            verdicts = [v.get("verdict") for v in votes.values()]
            has_discrepancy = len(set(verdicts)) > 2
            
            if has_discrepancy:
                st.write(
                    "⚡ Discrepancy detected — adapting learning plan..."
                )
            
            status.update(
                label="✅ Phase 2 Complete — Verdict Ready",
                state="complete"
            )
        
        # Show council results inline
        state = get_api_state()
        votes = state.get("council_votes", {})
        verdict = state.get("readiness_verdict", "")
        confidence = state.get("readiness_confidence", 0)
        
        # Mini agent cards (compact)
        cols = st.columns(5)
        
        agent_icons = {
            "optimist": "😊",
            "skeptic": "🔍",
            "advocate": "🛡️",
            "historian": "📚",
            "risk_analyst": "⚠️"
        }
        
        for i, (agent, vote) in enumerate(votes.items()):
            with cols[i]:
                verdict = vote.get("verdict", "")
                confidence = vote.get("confidence", 0)
                evidence = vote.get("evidence", [])
                
                border_color = (
                    "#00ff00" if verdict == "READY"
                    else "#ff4444" if verdict == "NOT_READY"
                    else "#ffaa00"
                )
                
                verdict_icon = (
                    "✅" if verdict == "READY"
                    else "❌" if verdict == "NOT_READY"
                    else "⏳"
                )
                
                st.markdown(
                    f"""
                    <div style='
                      border: 2px solid {border_color};
                      border-radius: 12px;
                      padding: 14px;
                      min-height: 320px;
                      background: rgba(255,255,255,0.03);
                    '>
                      <div style='font-size:13px; color:#aaa; 
                           text-transform:uppercase; 
                           letter-spacing:1px;'>
                        {agent_icons.get(agent, "🤖")} {agent.replace("_", " ")}
                      </div>
                      <div style='font-size:22px; font-weight:bold; 
                           color:{border_color}; margin:8px 0;'>
                        {verdict_icon} {verdict.replace("_", " ")}
                      </div>
                      <div style='font-size:28px; font-weight:bold; 
                           color:white; margin-bottom:12px;'>
                        {confidence}%
                      </div>
                      <hr style='border-color:{border_color}; opacity:0.3;'/>
                      <div style='font-size:12px; color:#ccc;'>
                        {''.join([f"<div style='margin:4px 0;'>• {e[:60]}...</div>" if len(e)>60 else f"<div style='margin:4px 0;'>• {e}</div>" for e in evidence[:3]])}
                      </div>
                      <hr style='border-color:{border_color}; opacity:0.3;'/>
                      <div style='font-size:11px; color:#aaa; 
                           font-style:italic; margin-top:8px;'>
                        {vote.get("recommendation", "")[:80]}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Critic verdict prominent
        v_color = (
            "green" if verdict == "READY" 
            else "red" if verdict == "NOT_READY" 
            else "orange"
        )
        st.markdown(
            f"### ⚖️ Verdict: "
            f":{v_color}[{verdict}] — {confidence}% confidence"
        )
        st.caption(state.get("readiness_reasoning", ""))
        
        # Show adaptation if made
        adaptations = state.get("adaptations", [])
        if adaptations:
            for a in adaptations:
                st.warning(
                    f"⚡ Plan adapted: {a.get('reason')}  \n"
                    f"Action: {a.get('action')}"
                )

    overall_progress.progress(0.4)

    # PHASE 3: Assessment
    current_phase_text.write("📝 Running mock assessment...")
    
    with phase_containers["assessment"]:
        with st.status(
            "📝 Phase 3: Mock Assessment",
            expanded=True
        ) as status:
            st.write("📋 Generating exam questions from Foundry IQ...")
            
            assessment_result = post_api("assessment", {
                "learner_id": learner_id
            })
            
            if not assessment_result:
                status.update(
                    label="❌ Assessment phase failed",
                    state="error"
                )
                return
            
            questions = assessment_result.get("questions", [])
            st.write(f"✅ {len(questions)} questions generated")
            st.write("📤 Auto-evaluating based on practice score...")
            
            # Auto-submit with simulated answers
            state = get_api_state()
            practice_score = 65  # Default
            
            # Simulate answers based on practice score
            import random
            simulated = {}
            for q in questions:
                qid = str(q["id"])
                correct = q.get("correct_answer", "A")
                options = list(q.get("options", {}).keys())
                if random.random() < (practice_score / 100):
                    simulated[qid] = correct
                else:
                    wrong = [o for o in options if o != correct]
                    simulated[qid] = (
                        random.choice(wrong) if wrong else correct
                    )
            
            submit_result = post_api("submit", {
                "learner_id": learner_id,
                "answers": simulated
            })
            
            if not submit_result:
                status.update(
                    label="❌ Assessment submission failed",
                    state="error"
                )
                return
            
            score = submit_result.get("score", 0)
            outcome = submit_result.get("outcome", "")
            
            status.update(
                label=f"✅ Phase 3 Complete — Score: {score:.1f}% ({outcome})",
                state="complete"
            )
        
        # Show assessment results inline
        state = get_api_state()
        score = state.get("assessment_score", 0)
        outcome = state.get("assessment_outcome", "")
        breakdown = state.get("assessment_breakdown", {})
        
        col1, col2 = st.columns(2)
        with col1:
            if outcome == "PASS":
                st.success(f"🎉 PASS — {score:.1f}%")
            else:
                st.error(f"❌ FAIL — {score:.1f}%")
        with col2:
            st.metric(
                "Questions Answered",
                f"{len(simulated)} / {len(questions)}"
            )
        
        # Topic breakdown
        if breakdown:
            topics = list(breakdown.keys())
            scores_vals = [breakdown[t]["score"] for t in topics]
            colors = [
                "green" if s >= 70 else "red" 
                for s in scores_vals
            ]
            
            fig = go.Figure(go.Bar(
                x=scores_vals, y=topics,
                orientation='h',
                marker_color=colors
            ))
            fig.add_vline(
                x=70, line_dash="dash",
                line_color="yellow",
                annotation_text="70% threshold"
            )
            fig.update_layout(
                title="Topic Performance",
                height=250,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Adaptation if failed
        if outcome == "FAIL":
            weak = state.get("weak_topics", [])
            st.warning(
                f"⚡ Study plan adapted: Added reinforcement for "
                f"{', '.join(weak[:3])}"
            )

    overall_progress.progress(0.6)

    # PHASE 4: Coaching
    current_phase_text.write("🧠 Running Socratic coaching...")
    
    with phase_containers["coaching"]:
        state = get_api_state()
        outcome = state.get("assessment_outcome", "")
        
        if outcome == "FAIL":
            with st.status(
                "🧠 Phase 4: Socratic Coaching",
                expanded=True
            ) as status:
                st.write("🔍 Identifying root misconceptions...")
                st.write("❓ Generating Socratic questions...")
                st.write("📋 Building remediation plan...")
                
                coaching_result = post_api("coaching", {
                    "learner_id": learner_id
                })
                
                status.update(
                    label="✅ Phase 4 Complete — Diagnosis Ready",
                    state="complete"
                )
            
            state = get_api_state()
            misconceptions = state.get("misconceptions", [])
            socratic_qs = state.get("socratic_questions", [])
            remediation = state.get("remediation", {})
            
            if misconceptions:
                st.error(
                    f"🔍 Root misconception: {misconceptions[0]}"
                )
            
            if socratic_qs:
                with st.expander(
                    f"❓ {len(socratic_qs)} Socratic Questions"
                ):
                    for i, q in enumerate(socratic_qs):
                        st.markdown(
                            f"**Q{i+1}:** {q.get('question', '')}"
                        )
                        st.caption(
                            f"💡 Leads to: {q.get('leads_to', '')}"
                        )
            
            if remediation:
                st.info(
                    f"📋 Remediation: {remediation.get('study_approach', '')}  \n"
                    f"⏱️ Estimated: {remediation.get('estimated_hours', 0)} hours"
                )
        else:
            with st.status(
                "🧠 Phase 4: Coaching",
                expanded=False
            ) as status:
                status.update(
                    label="✅ Phase 4 Skipped — Assessment Passed",
                    state="complete"
                )
            st.success("🎉 No coaching needed — learner is ready!")

    overall_progress.progress(0.8)

    # PHASE 5: Reflection
    current_phase_text.write("🔄 Running reflection...")
    
    with phase_containers["reflection"]:
        with st.status(
            "🔄 Phase 5: Reflection & Agent Learning",
            expanded=True
        ) as status:
            st.write("📊 Comparing prediction vs actual outcome...")
            st.write("🏆 Updating agent reputation scores...")
            st.write("🧠 Generating system learning insights...")
            
            state = get_api_state()
            actual_outcome = state.get("assessment_outcome", "FAIL")
            
            reflection_result = post_api("reflection", {
                "learner_id": learner_id,
                "actual_outcome": actual_outcome
            })
            
            status.update(
                label="✅ Phase 5 Complete — Agents Updated",
                state="complete"
            )
        
        reflection = reflection_result.get("reflection", {})
        rep_scores = reflection_result.get(
            "updated_reputation", []
        )
        
        if reflection.get("analysis"):
            st.info(f"💡 {reflection.get('analysis', '')}")
        
        # Show reputation updates compactly
        if rep_scores:
            cols = st.columns(len(rep_scores))
            for i, agent in enumerate(sorted(
                rep_scores, 
                key=lambda x: x.get("accuracy_score", 0),
                reverse=True
            )):
                with cols[i]:
                    score = agent.get("accuracy_score", 75)
                    name = agent.get("agent_name", "")
                    color = (
                        "green" if score >= 80 
                        else "orange" if score >= 70 
                        else "red"
                    )
                    st.markdown(
                        f"**{name.title()}**  \n"
                        f":{color}[{score:.1f}%]"
                    )

    overall_progress.progress(1.0)
    current_phase_text.write("✅ Pipeline complete!")

    # COMPLETION BANNER
    state = get_api_state()
    verdict = state.get("readiness_verdict", "")
    score = state.get("assessment_score", 0)
    adaptations_count = len(state.get("adaptations", []))
    
    if verdict:
        if verdict == "READY":
            banner_color = "#00aa00"
            banner_emoji = "✅"
            banner_text = "READY FOR EXAM"
        elif verdict == "NOT_READY":
            banner_color = "#ff4444"
            banner_emoji = "❌"
            banner_text = "MORE STUDY NEEDED"
        else:
            banner_color = "#ffaa00"
            banner_emoji = "⏳"
            banner_text = "EXAM DELAYED"
        
        st.markdown(
            f"""
            <div style='
              background: linear-gradient(90deg, {banner_color}22 0%, {banner_color}11 100%);
              border-left: 5px solid {banner_color};
              border-radius: 8px;
              padding: 20px;
              margin: 20px 0;
              text-align: center;
            '>
              <div style='font-size: 36px; margin-bottom: 10px;'>{banner_emoji}</div>
              <div style='font-size: 28px; font-weight: bold; color:{banner_color}; 
                   margin-bottom: 10px;'>{banner_text}</div>
              <div style='font-size: 16px; color: white; margin: 10px 0;'>
                <strong>Assessment Score:</strong> {score:.1f}% | 
                <strong>Plan Adaptations:</strong> {adaptations_count}
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # CONSOLIDATED REPORT
    with consolidated_container:
        st.markdown("---")
        st.subheader("📋 Consolidated Analysis Report")
        
        state = get_api_state()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        verdict = state.get("readiness_verdict", "")
        score = state.get("assessment_score", 0)
        adaptations = state.get("adaptations", [])
        
        with col1:
            st.metric(
                "Readiness Verdict",
                verdict,
                delta=f"{state.get('readiness_confidence', 0)}% confidence"
            )
        with col2:
            st.metric(
                "Assessment Score",
                f"{score:.1f}%",
                delta=f"{'Above' if score >= 70 else 'Below'} threshold"
            )
        with col3:
            st.metric(
                "Plan Adaptations",
                len(adaptations),
                delta="Auto-applied" if adaptations else "None needed"
            )
        with col4:
            weak_count = len(state.get("weak_topics", []))
            st.metric("Weak Topics", weak_count)
        
        # Adaptations made
        if adaptations:
            st.subheader("⚡ Adaptations Made to Your Plan")
            for i, a in enumerate(adaptations):
                with st.expander(
                    f"Adaptation {i+1}: {a.get('reason', '')}"
                ):
                    st.write(f"**Action taken:** {a.get('action', '')}")
                    if a.get("signals"):
                        st.write("**Signals detected:**")
                        for s in a.get("signals", []):
                            st.write(f"  • {s}")
        
        # Final study plan (adapted)
        st.subheader("📅 Final Study Plan")
        study_plan = state.get("study_plan", {})
        
        for week, data in study_plan.items():
            if not isinstance(data, dict):
                continue
            
            # Use helper to normalize dict keys across formats
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
        
        # Next recommended action
        st.subheader("🎯 Recommended Next Action")
        
        if verdict == "READY":
            st.success(
                "✅ You are ready to book your exam. "
                "Schedule within the next 5-7 days while knowledge is fresh."
            )
        elif verdict == "DELAY":
            st.warning(
                "⏳ Delay your exam by 1-2 weeks. "
                "Follow the adapted study plan focusing on weak topics."
            )
        else:
            # Fallback chain for weak topics
            weak = state.get("weak_topics", [])
            if not weak:
                # Try extracting from assessment breakdown
                assessment_breakdown = state.get("assessment_breakdown", {})
                if assessment_breakdown:
                    weak = [
                        t for t, d in assessment_breakdown.items()
                        if d.get("score", 100) < 70
                    ]
            if not weak:
                weak = ["Review all exam domains"]
            
            st.error(
                f"❌ Not ready yet. Focus on: "
                f"{', '.join(weak[:3])}. "
                f"Re-run analysis after 2 weeks of focused study."
            )
        
        # Export report
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
        
        st.download_button(
            "📥 Export Full Report",
            data=json.dumps(report_data, indent=2),
            file_name=f"certops_{learner_id}_{certification}.json",
            mime="application/json"
        )


def show_consolidated_results():
    """Show results if pipeline has been run before"""
    st.markdown("---")
    st.subheader("📋 Last Analysis Results")
    
    state = get_api_state()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    verdict = state.get("readiness_verdict", "")
    score = state.get("assessment_score", 0)
    adaptations = state.get("adaptations", [])
    
    with col1:
        st.metric(
            "Readiness Verdict",
            verdict,
            delta=f"{state.get('readiness_confidence', 0)}% confidence"
        )
    with col2:
        st.metric(
            "Assessment Score",
            f"{score:.1f}%",
            delta=f"{'Above' if score >= 70 else 'Below'} threshold"
        )
    with col3:
        st.metric(
            "Plan Adaptations",
            len(adaptations),
            delta="Auto-applied" if adaptations else "None needed"
        )
    with col4:
        weak_count = len(state.get("weak_topics", []))
        st.metric("Weak Topics", weak_count)
    
    # Adaptations made
    if adaptations:
        st.subheader("⚡ Adaptations Made to Your Plan")
        for i, a in enumerate(adaptations):
            with st.expander(
                f"Adaptation {i+1}: {a.get('reason', '')}"
            ):
                st.write(f"**Action taken:** {a.get('action', '')}")
                if a.get("signals"):
                    st.write("**Signals detected:**")
                    for s in a.get("signals", []):
                        st.write(f"  • {s}")
    
    # Final study plan (adapted)
    st.subheader("📅 Final Study Plan")
    study_plan = state.get("study_plan", {})
    
    for week, data in study_plan.items():
        adapted = data.get("adapted", False)
        label = f"{week}: {data.get('focus', '')}"
        if adapted:
            label += " ⚡ (adapted)"
        
        with st.expander(label):
            st.write(
                f"**Topics:** {', '.join(data.get('topics', []))}"
            )
            st.write(f"**Hours:** {data.get('hours', 0)}")
            st.write(
                f"**Milestone:** {data.get('milestone', '')}"
            )
            if adapted:
                st.info("✨ This week was adapted based on findings")

    st.divider()
    st.info("→ Use sidebar to explore deep-dive views")


# ============================================================================
# DEEP-DIVE PAGES (Read-Only Views — No New Execution)
# ============================================================================

def render_council_deepdive():
    st.title("⚖️ Council Debate — Deep Dive")
    st.markdown("Review the detailed council voting breakdown from the pipeline")
    
    state = get_api_state()
    votes = state.get("council_votes", {})
    
    if not votes:
        st.warning("Run the pipeline first to see council votes")
        return
    
    # 5 agent cards
    cols = st.columns(5)
    
    agent_icons = {
        "optimist": "😊",
        "skeptic": "🔍",
        "advocate": "🛡️",
        "historian": "📚",
        "risk_analyst": "⚠️"
    }
    
    verdict_colors = {
        "READY": "green",
        "NOT_READY": "red",
        "DELAY": "orange"
    }
    
    for i, (agent, vote) in enumerate(votes.items()):
        with cols[i]:
            verdict = vote.get("verdict", "")
            confidence = vote.get("confidence", 0)
            color = verdict_colors.get(verdict, "grey")
            icon = agent_icons.get(agent, "🤖")
            
            st.markdown(
                f"""
                <div style='border: 2px solid {color}; 
                     border-radius: 10px; padding: 10px; height: auto;'>
                <h4>{icon} {agent.upper()}</h4>
                <h3 style='color: {color};'>
                  {verdict}
                </h3>
                <p><strong>{confidence}% confidence</strong></p>
                <hr/>
                {''.join([f"<p style='font-size: 0.9em;'>• {e}</p>" for e in vote.get('evidence', [])])}
                <hr/>
                <small>{vote.get('recommendation', '')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Critic verdict
    st.divider()
    st.subheader("⚖️ Final Critic Verdict")
    
    verdict = state.get("readiness_verdict", "")
    confidence = state.get("readiness_confidence", 0)
    reasoning = state.get("readiness_reasoning", "")
    
    v_color = (
        "green" if verdict == "READY" 
        else "red" if verdict == "NOT_READY" 
        else "orange"
    )
    
    st.markdown(
        f"""
        <div style='border: 3px solid {v_color};
             border-radius: 15px; padding: 20px; text-align: center;'>
        <h2 style='color: {v_color};'>
          {'✅' if verdict=='READY' else '❌' if verdict=='NOT_READY' else '⏳'} {verdict}
        </h2>
        <h3>Confidence: {confidence}%</h3>
        <p>{reasoning}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_manager_insights():
    st.title("📊 Manager Insights")
    st.markdown("Team-level analytics from pipeline executions")
    
    try:
        insights = get_api("manager")
        
        if not insights or not insights.get("learners"):
            st.info("No team data available yet. Run pipeline to see insights.")
            return
        
        learners = insights.get("learners", [])
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ready = sum(1 for l in learners if l.get("readiness_verdict") == "READY")
            st.metric("Ready", f"{ready}/{len(learners)}")
        with col2:
            avg_score = sum(l.get("assessment_score", 0) for l in learners) / len(learners) if learners else 0
            st.metric("Avg Score", f"{avg_score:.0f}%")
        with col3:
            failed = sum(1 for l in learners if l.get("assessment_outcome") == "FAIL")
            st.metric("At Risk", failed)
        with col4:
            completed = sum(1 for l in learners if l.get("reflection"))
            st.metric("Completed", completed)
        
        st.divider()
        
        # Learner table
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
        
        # Weak topics
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
        
        # Bar chart
        agent_names = [a.get("agent_name", "").upper() for a in agents]
        accuracies = [a.get("accuracy_score", 0) for a in agents]
        
        fig = go.Figure(go.Bar(
            x=agent_names,
            y=accuracies,
            marker_color=["green" if x >= 80 else "orange" if x >= 70 else "red" for x in accuracies],
            text=[f"{x:.0f}%" for x in accuracies],
            textposition="auto",
        ))
        fig.update_layout(
            title="Agent Accuracy Comparison",
            xaxis_title="Agent",
            yaxis_title="Accuracy %",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📈 Detailed Scores")
        agent_table = []
        for a in agents:
            total = a.get("total_predictions", 0)
            correct = a.get("correct_predictions", 0)
            wrong = total - correct
            agent_table.append({
                "Agent": a.get("agent_name", "").upper(),
                "Accuracy": f"{a.get('accuracy_score', 0):.1f}%",
                "Total": total,
                "Correct": correct,
                "Wrong": wrong,
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
    
    # Full log
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
