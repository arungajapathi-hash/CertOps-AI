import streamlit as st
import httpx

st.set_page_config(page_title="CertOps AI", layout="wide")

st.sidebar.title("CertOps AI")
st.sidebar.markdown("Self-Learning Certification Readiness Intelligence Platform")

pages = [
    "Learner Dashboard",
    "Readiness Council",
    "Assessment",
    "Coaching",
    "Manager Insights",
    "Agent Reputation",
    "Reasoning Trace",
]
selected_page = st.sidebar.radio("Navigation", pages)

st.title(selected_page)

if selected_page == "Learner Dashboard":
    col1, col2 = st.columns(2)
    with col1:
        cert = st.text_input(
            "Certification",
            value="AZ-204",
            help="Enter any Microsoft certification (e.g., AZ-204, AZ-900, SC-900, MS-700, DP-203)"
        )
        role = st.text_input("Role", value="Cloud Engineer")
    
    with col2:
        learner_id = st.text_input("Learner ID", value="L-1001")
        target_weeks = st.slider("Target weeks", 1, 12, 6)

    if st.button("🚀 Build My Learning Plan", use_container_width=True):
        payload = {
            "learner_id": learner_id,
            "role": role,
            "certification": cert.upper(),
            "target_weeks": target_weeks,
        }
        with st.spinner(f"🤖 Building your {cert.upper()} learning plan..."):
            try:
                resp = httpx.post("http://localhost:8000/learn", json=payload, timeout=60.0)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                st.error(f"❌ API error: {exc}")
                data = None

        if data:
            st.success(f"✅ Plan created for {cert.upper()}")
            
            # Show knowledge source badge
            knowledge_source = data.get("knowledge_source", "Unknown")
            citations = data.get("citations", [])
            
            if knowledge_source == "Foundry IQ":
                st.success("⚡ **Powered by Azure AI Foundry IQ** — Web-grounded knowledge")
            elif knowledge_source == "Dynamic Web":
                st.info("🌐 **Powered by Dynamic Web Retrieval** — Real-time content")
            elif knowledge_source == "LLM Knowledge":
                st.warning("🤖 **Powered by LLM Knowledge** — AI-generated content")
            else:
                st.caption(f"📚 Knowledge source: {knowledge_source}")
            
            # Show citations if available
            if citations and len(citations) > 0:
                with st.expander("📎 Sources & Citations"):
                    for i, citation in enumerate(citations, 1):
                        if citation and citation != "":
                            st.write(f"{i}. {citation}")
            
            cols = st.columns(3)
            # Column 1: Skill Map
            with cols[0]:
                st.header("Skill Map")
                skill_map = data.get("skill_map", [])
                if skill_map:
                    for s in skill_map:
                        st.write(f"• {s}")
                else:
                    st.info("No skills identified — check logs")

            # Column 2: Study Plan
            with cols[1]:
                st.header("Study Plan")
                plan = data.get("study_plan", {})
                if isinstance(plan, dict) and plan:
                    for week_key in sorted(plan.keys()):
                        week_data = plan[week_key]
                        if isinstance(week_data, dict):
                            with st.expander(f"📅 {week_key}"):
                                st.markdown(f"**Focus:** {week_data.get('focus', 'N/A')}")
                                topics = week_data.get("topics", [])
                                if topics:
                                    st.markdown(f"**Topics:** {', '.join(topics)}")
                                st.markdown(f"**Hours:** {week_data.get('hours', 0)}")
                                st.markdown(f"**Milestone:** {week_data.get('milestone', 'N/A')}")
                                resources = week_data.get("resources", [])
                                if resources:
                                    st.markdown(f"**Resources:** {', '.join(resources)}")
                else:
                    st.info("Study plan empty — check logs")

            # Column 3: Study Windows
            with cols[2]:
                st.header("Study Windows")
                ws = data.get("work_signals", {})
                rec = ws.get("recommended_windows", []) if isinstance(ws, dict) else []
                risk = ws.get("workload_risk", "Unknown") if isinstance(ws, dict) else "Unknown"
                
                # Badge color
                color = "black"
                if risk == "Low":
                    color = "green"
                elif risk == "Medium":
                    color = "orange"
                elif risk == "High":
                    color = "red"
                
                st.markdown(f"**Workload risk:** <span style='color:{color}'>● {risk}</span>", unsafe_allow_html=True)
                
                if rec:
                    for r in rec:
                        # Safely format duration
                        duration = r.get("duration_hours") or r.get("duration", 0)
                        try:
                            duration_str = f"{float(duration):.1f}h"
                        except (ValueError, TypeError):
                            duration_str = "1.5h"
                        
                        day = r.get("day", "")
                        time = r.get("time", "")
                        reason = r.get("reason", "")
                        st.write(f"• **{day}** {time} — {duration_str} ({reason})")
                else:
                    st.info("No study windows recommended")

            # Reasoning trace
            with st.expander("🔍 Reasoning Trace"):
                logs = data.get("session_log", [])
                if logs:
                    for line in logs:
                        st.write(line)
                else:
                    st.info("No reasoning logs available")

else:
    st.write(f"Coming soon — {selected_page}")
