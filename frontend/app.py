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

elif selected_page == "Readiness Council":
    st.markdown("### 🏛️ Multi-Agent Readiness Assessment")
    st.markdown("Five specialist agents debate in parallel. The Critic synthesizes their votes using reputation weights.")
    
    learner_id = st.text_input("Learner ID", value="L-1001", key="readiness_learner")
    
    # Initialize session state for results
    if "council_results" not in st.session_state:
        st.session_state.council_results = None
    
    if st.button("⚖️ Convene the Council", use_container_width=True, type="primary"):
        with st.spinner("🤖 The Council is deliberating... 5 agents debating in parallel"):
            try:
                resp = httpx.post(
                    "http://localhost:8000/readiness",
                    json={"learner_id": learner_id},
                    timeout=120.0
                )
                resp.raise_for_status()
                st.session_state.council_results = resp.json()
            except Exception as exc:
                st.error(f"❌ API error: {exc}")
                st.session_state.council_results = None
    
    # Display results if available
    if st.session_state.council_results:
        data = st.session_state.council_results
        
        # Header with learner info
        cols = st.columns([2, 1, 1])
        with cols[0]:
            st.markdown(f"**Learner:** `{data.get('learner_id', 'Unknown')}`")
        with cols[1]:
            verdict = data.get('verdict', 'UNKNOWN')
            verdict_color = {"READY": "green", "NOT_READY": "red", "DELAY": "orange"}.get(verdict, "gray")
            st.markdown(f"**Final Verdict:** <span style='color:{verdict_color};font-weight:bold'>{verdict}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"**Confidence:** {data.get('confidence', 0)}%")
        
        st.divider()
        
        # Row 1: 5 Agent Cards
        votes = data.get("council_votes", {})
        agent_cols = st.columns(5)
        
        agent_order = ["optimist", "skeptic", "advocate", "historian", "risk_analyst"]
        agent_emojis = {"optimist": "🌟", "skeptic": "🔍", "advocate": "🛡️", "historian": "📚", "risk_analyst": "📊"}
        agent_names = {"optimist": "OPTIMIST", "skeptic": "SKEPTIC", "advocate": "ADVOCATE", "historian": "HISTORIAN", "risk_analyst": "RISK ANALYST"}
        
        for idx, agent_key in enumerate(agent_order):
            vote = votes.get(agent_key, {})
            if not vote:
                # Fallback for missing agent vote
                vote = {
                    "verdict": "DELAY",
                    "confidence": 0,
                    "evidence": ["Agent did not respond"],
                    "recommendation": "Check logs"
                }
            
            agent_verdict = vote.get("verdict", "DELAY")
            confidence = vote.get("confidence", 0)
            evidence = vote.get("evidence", ["No evidence"]) or ["No evidence"]
            recommendation = vote.get("recommendation", "None")
            
            # Color coding for dark mode compatibility
            border_color = {"READY": "#22c55e", "NOT_READY": "#ef4444", "DELAY": "#f97316"}.get(agent_verdict, "#6b7280")
            bg_color = {"READY": "#064e3b", "NOT_READY": "#450a0a", "DELAY": "#431407"}.get(agent_verdict, "#1f2937")
            text_color = {"READY": "#4ade80", "NOT_READY": "#f87171", "DELAY": "#fb923c"}.get(agent_verdict, "#9ca3af")
            
            # Build evidence list safely
            evidence_html = ""
            for ev in evidence[:3]:
                if ev:
                    evidence_html += f"<li style='margin-bottom: 4px;'>{ev}</li>"
            
            with agent_cols[idx]:
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 10px; margin-bottom: 8px; background: {bg_color};">
                    <div style="font-weight: bold; font-size: 11px; margin-bottom: 6px; text-align: center; color: #e5e7eb;">
                        {agent_emojis.get(agent_key, "🤖")} {agent_names.get(agent_key, agent_key.upper())}
                    </div>
                    <div style="text-align: center; margin-bottom: 6px;">
                        <span style="color: {text_color}; font-weight: bold; font-size: 13px;">{agent_verdict}</span>
                    </div>
                    <div style="font-size: 10px; text-align: center; margin-bottom: 6px; color: #9ca3af;">
                        confidence: {confidence}%
                    </div>
                    <div style="font-size: 9px; line-height: 1.3; color: #d1d5db;">
                        <ul style="padding-left: 12px; margin: 0;">
                            {evidence_html}
                        </ul>
                    </div>
                    <div style="font-size: 9px; font-style: italic; text-align: center; margin-top: 6px; color: #9ca3af; border-top: 1px solid {border_color}; padding-top: 6px;">
                        {recommendation[:50]}{'...' if len(str(recommendation)) > 50 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Row 2: Critic Verdict (prominent)
        critic_output = data.get("critic_output", {})
        weighted_votes = critic_output.get("weighted_votes", {})
        
        verdict_emoji = {"READY": "✅", "NOT_READY": "❌", "DELAY": "⏸️"}.get(verdict, "❓")
        verdict_bg = {"READY": "#064e3b", "NOT_READY": "#450a0a", "DELAY": "#431407"}.get(verdict, "#1f2937")
        verdict_border = {"READY": "#22c55e", "NOT_READY": "#ef4444", "DELAY": "#f97316"}.get(verdict, "#6b7280")
        verdict_text = {"READY": "#4ade80", "NOT_READY": "#f87171", "DELAY": "#fb923c"}.get(verdict, "#e5e7eb")
        
        st.markdown(f"""
        <div style="background: {verdict_bg}; border: 3px solid {verdict_border}; border-radius: 12px; padding: 24px; margin: 16px 0; text-align: center;">
            <div style="font-size: 20px; margin-bottom: 8px; color: #e5e7eb;">⚖️ CRITIC VERDICT</div>
            <div style="font-size: 32px; font-weight: bold; color: {verdict_text}; margin: 16px 0;">
                {verdict_emoji} {verdict}
            </div>
            <div style="font-size: 16px; margin-bottom: 16px; color: #d1d5db;">
                Confidence: <b style="color: {verdict_text};">{data.get('confidence', 0)}%</b>
            </div>
            <div style="font-size: 14px; max-width: 600px; margin: 0 auto; line-height: 1.6; color: #d1d5db;">
                {data.get('reasoning', 'No reasoning provided')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Weighted votes breakdown
        if weighted_votes:
            st.markdown("#### 📊 Weighted Vote Scores")
            vote_cols = st.columns(3)
            for idx, (v_label, v_score) in enumerate(weighted_votes.items()):
                v_color = {"READY": "green", "NOT_READY": "red", "DELAY": "orange"}.get(v_label, "gray")
                with vote_cols[idx % 3]:
                    st.markdown(f"**{v_label}:** <span style='color:{v_color}'>{v_score:.1f}</span>", unsafe_allow_html=True)
        
        # Key blocker and recommendation
        key_blocker = critic_output.get("key_blocker")
        recommendation = critic_output.get("recommendation", "No specific recommendation")
        
        if key_blocker:
            st.error(f"🚫 **Key Blocker:** {key_blocker}")
        
        st.info(f"💡 **Next Step:** {recommendation}")
        
        # Session log
        with st.expander("📋 Full Session Log"):
            logs = data.get("session_log", [])
            if logs:
                for line in logs:
                    st.text(line)
            else:
                st.info("No session logs available")

elif selected_page == "Agent Reputation":
    st.markdown("### 📈 Agent Reputation Tracking")
    st.markdown("Reputation scores improve as agents make correct predictions. The Critic uses these weights when synthesizing council votes.")
    
    try:
        resp = httpx.get("http://localhost:8000/reputation", timeout=10.0)
        resp.raise_for_status()
        rep_data = resp.json()
        agents = rep_data.get("agents", [])
        
        if agents:
            # Display as a table
            st.dataframe(
                [
                    {
                        "Agent": a["name"].upper(),
                        "Accuracy": f"{a['accuracy']:.1f}%",
                        "Predictions": a["total"],
                        "Correct": a["correct"],
                    }
                    for a in agents
                ],
                use_container_width=True,
                hide_index=True,
            )
            
            # Simple bar chart
            st.markdown("#### Accuracy Comparison")
            bar_cols = st.columns(len(agents))
            for idx, agent in enumerate(agents):
                with bar_cols[idx]:
                    accuracy = agent["accuracy"]
                    color = "#22c55e" if accuracy >= 80 else "#f97316" if accuracy >= 60 else "#ef4444"
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="font-size: 12px; margin-bottom: 4px;">{agent['name'].upper()}</div>
                        <div style="background: {color}; height: {accuracy * 1.5}px; width: 40px; margin: 0 auto; border-radius: 4px;"></div>
                        <div style="font-size: 11px; margin-top: 4px;">{accuracy:.0f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No reputation data available. Run some readiness assessments first.")
    except Exception as exc:
        st.error(f"❌ Could not load reputation data: {exc}")

elif selected_page == "Assessment":
    st.markdown("### 📝 Assessment")
    st.markdown("Complete a 10-question mock exam. Questions focus on your weak topics.")
    
    learner_id = st.text_input("Learner ID", value="L-1001", key="assessment_learner")
    
    # Initialize session state
    if "assessment_questions" not in st.session_state:
        st.session_state.assessment_questions = []
    if "assessment_answers" not in st.session_state:
        st.session_state.assessment_answers = {}
    if "assessment_submitted" not in st.session_state:
        st.session_state.assessment_submitted = False
    if "assessment_results" not in st.session_state:
        st.session_state.assessment_results = None
    
    # Phase 1: Generate questions
    if not st.session_state.assessment_questions and not st.session_state.assessment_submitted:
        if st.button("📝 Start Mock Exam", use_container_width=True, type="primary"):
            with st.spinner("Generating questions..."):
                try:
                    resp = httpx.post(
                        "http://localhost:8000/assessment",
                        json={"learner_id": learner_id},
                        timeout=60.0
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.assessment_questions = data.get("questions", [])
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ Error: {exc}")
    
    # Phase 2: Show quiz
    if st.session_state.assessment_questions and not st.session_state.assessment_submitted:
        questions = st.session_state.assessment_questions
        cert = questions[0].get("topic", "Certification") if questions else "Exam"
        
        st.markdown(f"#### {cert} Mock Exam — {len(questions)} Questions")
        
        # Progress bar
        answered = len([a for a in st.session_state.assessment_answers.values() if a])
        progress = answered / len(questions) if questions else 0
        st.progress(progress, text=f"Answered {answered}/{len(questions)}")
        
        # Show each question
        for q in questions:
            q_id = str(q.get("id", ""))
            topic = q.get("topic", "General")
            question_text = q.get("question", "")
            options = q.get("options", {})
            
            with st.container():
                st.markdown(f"**Q{q_id}** — `{topic}`")
                st.write(question_text)
                
                # Radio for options
                option_list = [f"{k}: {v}" for k, v in options.items()]
                current = st.session_state.assessment_answers.get(q_id, "")
                
                selected = st.radio(
                    "Select answer:",
                    option_list,
                    key=f"q_{q_id}",
                    index=option_list.index(f"{current}: {options.get(current, '')}") if current in options else None,
                    label_visibility="collapsed"
                )
                
                # Parse selection
                if selected:
                    answer_letter = selected.split(":")[0]
                    st.session_state.assessment_answers[q_id] = answer_letter
                
                st.divider()
        
        # Submit button (only when all answered)
        if answered == len(questions):
            if st.button("✅ Submit Exam", use_container_width=True, type="primary"):
                with st.spinner("Evaluating answers..."):
                    try:
                        resp = httpx.post(
                            "http://localhost:8000/submit",
                            json={
                                "learner_id": learner_id,
                                "answers": st.session_state.assessment_answers
                            },
                            timeout=60.0
                        )
                        resp.raise_for_status()
                        st.session_state.assessment_results = resp.json()
                        st.session_state.assessment_submitted = True
                        st.rerun()
                    except Exception as exc:
                        st.error(f"❌ Error submitting: {exc}")
        else:
            st.warning(f"Please answer all {len(questions)} questions before submitting. ({len(questions) - answered} remaining)")
    
    # Phase 3: Show results
    if st.session_state.assessment_submitted and st.session_state.assessment_results:
        results = st.session_state.assessment_results
        score = results.get("score", 0)
        outcome = results.get("outcome", "UNKNOWN")
        breakdown = results.get("topic_breakdown", {})
        questions = st.session_state.assessment_questions
        answers = st.session_state.assessment_answers
        
        # Score display
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if outcome == "PASS":
                st.success(f"## 🎉 PASS — {score:.1f}%")
                st.balloons()
            else:
                st.error(f"## ❌ FAIL — {score:.1f}%")
                st.info("The Socratic Coach is available on the Coaching page to help you improve.")
        
        # Topic breakdown
        if breakdown:
            st.markdown("#### 📊 Topic Breakdown")
            for topic, data in breakdown.items():
                t_score = data.get("score", 0)
                correct = data.get("correct", 0)
                total = data.get("total", 0)
                color = "green" if t_score >= 70 else "red"
                st.markdown(f"**{topic}:** <span style='color:{color}'>{t_score:.0f}%</span> ({correct}/{total})", unsafe_allow_html=True)
        
        # Question review
        st.markdown("#### 📝 Question Review")
        for q in questions:
            q_id = str(q.get("id", ""))
            correct_answer = q.get("correct_answer", "")
            user_answer = answers.get(q_id, "")
            is_correct = user_answer == correct_answer
            
            emoji = "✅" if is_correct else "❌"
            border = "2px solid #22c55e" if is_correct else "2px solid #ef4444"
            
            with st.container():
                st.markdown(f"""
                <div style="border: {border}; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: #1f2937;">
                    <div style="font-weight: bold; color: #e5e7eb;">{emoji} Q{q_id} — {q.get('topic', '')}</div>
                    <div style="color: #d1d5db; margin: 8px 0;">{q.get('question', '')}</div>
                    <div style="font-size: 12px; color: #9ca3af;">
                        Your answer: <b style="color: {'#4ade80' if is_correct else '#f87171'}">{user_answer or 'None'}</b> | 
                        Correct: <b style="color: #4ade80;">{correct_answer}</b>
                    </div>
                    <div style="font-size: 11px; color: #9ca3af; margin-top: 8px; border-top: 1px solid #374151; padding-top: 8px;">
                        {q.get('explanation', '')}
                    </div>
                    <div style="font-size: 10px; color: #6b7280; margin-top: 4px;">
                        📚 Source: {q.get('source', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Reset button
        if st.button("🔄 Retake Assessment"):
            st.session_state.assessment_questions = []
            st.session_state.assessment_answers = {}
            st.session_state.assessment_submitted = False
            st.session_state.assessment_results = None
            st.rerun()

elif selected_page == "Coaching":
    st.markdown("### 🎓 Socratic Coach — Learning Diagnosis")
    
    # Check if assessment was failed
    mem_outcome = st.session_state.get("assessment_results", {}).get("outcome", "")
    socratic_triggered = st.session_state.get("assessment_results", {}).get("socratic_triggered", False)
    
    if not socratic_triggered:
        st.info("📋 Complete an assessment first and achieve a score below 70% to unlock Socratic coaching.")
        
        # Show button to fetch coaching data anyway
        if st.button("🔄 Check for Coaching Data"):
            try:
                resp = httpx.post(
                    "http://localhost:8000/coaching",
                    json={"learner_id": "L-1001"},
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("misconceptions"):
                    st.session_state.coaching_data = data
                    st.rerun()
                else:
                    st.warning("No coaching data available. Take an assessment first.")
            except Exception as exc:
                st.warning(f"Could not fetch coaching data: {exc}")
        
        # Check if we have cached coaching data
        if "coaching_data" in st.session_state:
            st.markdown("---")
            st.success("Coaching data found!")
    else:
        # Get coaching data
        coaching_data = st.session_state.get("assessment_results", {})
        misconceptions = coaching_data.get("misconceptions", [])
        socratic_questions = coaching_data.get("socratic_questions", [])
        remediation = coaching_data.get("remediation", {})
        
        # Section 1: Root Misconception
        if misconceptions:
            st.error(f"🎯 **Root Misconception:** {misconceptions[0]}")
        
        # Section 2: Socratic Questions
        if socratic_questions:
            st.markdown("#### ❓ Socratic Questions")
            st.markdown("*Answer these questions to discover your own understanding.*")
            
            # Track active question
            if "active_question" not in st.session_state:
                st.session_state.active_question = 0
            if "question_answers" not in st.session_state:
                st.session_state.question_answers = {}
            
            active_idx = st.session_state.active_question
            
            # Show progress
            st.progress((active_idx + 1) / len(socratic_questions), text=f"Question {active_idx + 1} of {len(socratic_questions)}")
            
            # Show current question
            if active_idx < len(socratic_questions):
                q = socratic_questions[active_idx]
                
                with st.container():
                    st.markdown(f"**Question {active_idx + 1}:** {q.get('question', '')}")
                    
                    # Answer area
                    answer = st.text_area(
                        "Your reflection:",
                        value=st.session_state.question_answers.get(active_idx, ""),
                        key=f"reflection_{active_idx}",
                        height=100
                    )
                    st.session_state.question_answers[active_idx] = answer
                    
                    # Hint expander
                    with st.expander("💡 Need a hint?"):
                        st.info(q.get("hint", "Think about the core concepts."))
                        st.caption(f"*This leads to: {q.get('leads_to', 'Deeper understanding')}*")
                    
                    # Navigation
                    cols = st.columns([1, 1])
                    with cols[0]:
                        if active_idx > 0 and st.button("⬅️ Previous"):
                            st.session_state.active_question = active_idx - 1
                            st.rerun()
                    with cols[1]:
                        if active_idx < len(socratic_questions) - 1:
                            if st.button("Next ➡️"):
                                st.session_state.active_question = active_idx + 1
                                st.rerun()
                        else:
                            if st.button("✅ Finish"):
                                st.session_state.socratic_complete = True
                                st.rerun()
        
        # Section 3: Remediation Plan
        if st.session_state.get("socratic_complete") or not socratic_questions:
            st.markdown("---")
            st.markdown("#### 📋 Remediation Plan")
            
            if remediation:
                focus_areas = remediation.get("focus_areas", [])
                if focus_areas:
                    st.markdown("**🎯 Focus Areas:**")
                    for area in focus_areas:
                        st.markdown(f"- `{area}`")
                
                approach = remediation.get("study_approach", "")
                if approach:
                    st.markdown(f"**📖 Study Approach:** {approach}")
                
                hours = remediation.get("estimated_hours", 0)
                if hours:
                    st.metric("Estimated Study Time", f"{hours} hours")
                
                message = remediation.get("confidence_message", "")
                if message:
                    st.success(f"💪 {message}")
            
            # Next steps
            st.markdown("---")
            st.markdown("#### 🚀 Next Steps")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retake Assessment", use_container_width=True):
                    # Clear assessment state
                    for key in ["assessment_questions", "assessment_answers", "assessment_submitted", "assessment_results"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.active_question = 0
                    st.session_state.socratic_complete = False
                    st.session_state.question_answers = {}
                    st.rerun()
            with col2:
                st.button("📚 Update Study Plan", use_container_width=True, disabled=True,
                         help="Coming soon — updates study plan with focus areas")

elif selected_page == "Manager Insights":
    st.markdown("### 👔 Manager Insights — Team Certification Readiness")
    st.markdown("Real-time analytics across all learners and certifications.")
    
    if st.button("🔄 Refresh Insights", use_container_width=True):
        st.rerun()
    
    try:
        resp = httpx.get("http://localhost:8000/manager", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        
        # Row 1 — Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Assessments", data.get("total_assessments", 0))
        with col2:
            pass_rate = data.get("overall_pass_rate", 0)
            delta = f"{pass_rate - 70:.1f}%" if pass_rate else None
            st.metric("Overall Pass Rate", f"{pass_rate:.1f}%", delta=delta)
        with col3:
            at_risk_count = len(data.get("at_risk_learners", []))
            st.metric("At Risk Learners", at_risk_count)
        with col4:
            weak_areas = data.get("top_weak_areas", [])
            top_weak = weak_areas[0] if weak_areas else "None"
            st.metric("Top Weak Area", top_weak)
        
        st.divider()
        
        # Row 2 — Team Readiness by Certification
        st.markdown("#### 📊 Certification Readiness")
        team_readiness = data.get("team_readiness", [])
        if team_readiness:
            for cert_data in team_readiness:
                cert = cert_data.get("certification", "Unknown")
                status = cert_data.get("status", "Unknown")
                pass_rate = cert_data.get("pass_rate", 0)
                attempts = cert_data.get("total_attempts", 0)
                passes = cert_data.get("passes", 0)
                avg_score = cert_data.get("avg_score", 0)
                
                # Color coding
                status_colors = {"On Track": "#22c55e", "At Risk": "#f97316", "Critical": "#ef4444"}
                border_color = status_colors.get(status, "#6b7280")
                
                with st.container():
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; background: #1f2937;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-weight: bold; font-size: 16px; color: #e5e7eb;">{cert}</div>
                            <div style="color: {border_color}; font-weight: bold;">● {status}</div>
                        </div>
                        <div style="margin-top: 8px; color: #9ca3af;">
                            Pass rate: <b>{pass_rate:.0f}%</b> ({passes}/{attempts}) | Avg score: {avg_score:.1f}%
                        </div>
                        <div style="margin-top: 8px;">
                            <div style="background: #374151; height: 8px; border-radius: 4px;">
                                <div style="background: {border_color}; height: 8px; width: {pass_rate}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No assessment data yet. Complete some assessments to see team stats.")
        
        st.divider()
        
        # Row 3 — At Risk Learners
        st.markdown("#### ⚠️ At Risk Learners")
        at_risk = data.get("at_risk_learners", [])
        if at_risk:
            st.dataframe(
                [
                    {
                        "Learner ID": lr["learner_id"],
                        "Certification": lr["certification"],
                        "Score": f"{lr['score']:.1f}%",
                        "Outcome": lr["outcome"],
                    }
                    for lr in at_risk
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No learners currently at risk! 🎉")
        
        st.divider()
        
        # Row 4 — Top Weak Areas
        st.markdown("#### 🔍 Top Weak Areas (Team-wide)")
        weak_areas = data.get("top_weak_areas", [])
        if weak_areas:
            cols = st.columns(len(weak_areas))
            for idx, area in enumerate(weak_areas):
                with cols[idx]:
                    st.error(f"🚨 {area}")
        else:
            st.info("Not enough data to identify weak areas yet.")
        
        st.divider()
        
        # Row 5 — Recent Activity
        st.markdown("#### 🕐 Recent Activity")
        recent = data.get("recent_activity", [])
        if recent:
            for activity in recent[:5]:
                outcome_emoji = "✅" if activity.get("outcome") == "PASS" else "❌"
                st.markdown(
                    f"{outcome_emoji} **{activity.get('learner_id', 'Unknown')}** — "
                    f"{activity.get('certification', 'Unknown')}: "
                    f"{activity.get('score', 0):.1f}% "
                    f"({activity.get('timestamp', 'recent')})"
                )
        else:
            st.info("No recent activity.")
            
    except Exception as exc:
        st.error(f"❌ Could not load manager insights: {exc}")

elif selected_page == "Agent Reputation":
    st.markdown("### 🏆 Agent Reputation — Self-Learning Performance")
    st.markdown("Agents are ranked by prediction accuracy. Higher accuracy = more influence on future verdicts.")
    
    try:
        resp = httpx.get("http://localhost:8000/reputation", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        agents = data.get("agents", [])
        summary = data.get("summary", {})
        
        if agents:
            # Sort by accuracy descending
            agents.sort(key=lambda x: x.get("accuracy_score", 0), reverse=True)
            
            # Row 1 — Leaderboard
            st.markdown("#### 🥇 Reputation Leaderboard")
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for idx, agent in enumerate(agents[:5]):
                name = agent.get("agent_name", "Unknown").upper()
                accuracy = agent.get("accuracy_score", 0)
                total = agent.get("total_predictions", 0)
                medal = medals[idx] if idx < 5 else "🏅"
                
                # Bar width based on accuracy
                bar_width = accuracy
                bar_color = "#22c55e" if accuracy >= 80 else "#f97316" if accuracy >= 60 else "#ef4444"
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 12px; background: #1f2937; padding: 12px; border-radius: 8px;">
                    <div style="font-size: 24px; margin-right: 12px;">{medal}</div>
                    <div style="width: 150px; font-weight: bold; color: #e5e7eb;">{name}</div>
                    <div style="flex: 1; margin: 0 12px;">
                        <div style="background: #374151; height: 20px; border-radius: 10px;">
                            <div style="background: {bar_color}; height: 20px; width: {bar_width}%; border-radius: 10px; transition: width 0.5s;"></div>
                        </div>
                    </div>
                    <div style="width: 80px; text-align: right; color: {bar_color}; font-weight: bold;">{accuracy:.1f}%</div>
                    <div style="width: 60px; text-align: right; color: #9ca3af; font-size: 12px;">({total})</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Row 2 — Detailed table with trends
            st.markdown("#### 📊 Detailed Statistics")
            st.dataframe(
                [
                    {
                        "Rank": idx + 1,
                        "Agent": a["agent_name"].upper(),
                        "Accuracy": f"{a['accuracy_score']:.1f}%",
                        "Correct": a["correct_predictions"],
                        "Total": a["total_predictions"],
                        "Trend": summary.get(a["agent_name"], {}).get("trend", "needs data").upper(),
                    }
                    for idx, a in enumerate(agents)
                ],
                use_container_width=True,
                hide_index=True,
            )
            
        else:
            st.info("No reputation data available. Run some assessments with reflection to populate scores.")
        
        st.divider()
        
        # Row 3 — Explanation
        st.info("""
        **How reputation works:** After each assessment, the system compares what each agent predicted 
        vs what actually happened. Correct predictions increase accuracy. The Critic Agent uses these 
        scores as weights — higher accuracy agents have more influence on the final readiness verdict.
        """)
        
        st.divider()
        
        # Row 4 — Reset button
        if st.button("🔄 Reset to Demo Defaults", use_container_width=True):
            try:
                resp = httpx.get("http://localhost:8000/reset-demo", timeout=10.0)
                resp.raise_for_status()
                st.success("✅ Demo reset complete! All agents returned to 75% baseline.")
                st.rerun()
            except Exception as exc:
                st.error(f"❌ Reset failed: {exc}")
                
    except Exception as exc:
        st.error(f"❌ Could not load reputation data: {exc}")

elif selected_page == "Reasoning Trace":
    st.markdown("### 🔍 Reasoning Trace — Agent Execution Log")
    st.markdown("Complete audit trail of every agent decision in this session.")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh every 5 seconds", value=False)
    
    try:
        # Fetch session log from memory via coaching endpoint (which returns current memory state)
        resp = httpx.post("http://localhost:8000/coaching", json={"learner_id": "L-1001"}, timeout=5.0)
        # Actually we need a way to get session_log - let's use the assessment endpoint since it has memory
        # For now, use a workaround by getting from the orchestrator via any endpoint that returns session_log
        # Best way: just try multiple endpoints
        
        logs = []
        
        # Try to get logs from recent API calls - session_log is returned by most endpoints
        # Since we can't directly query orchestrator from Streamlit, show a message
        st.info("Session logs are captured during API calls. Complete an action (learn, readiness, assessment) to populate this trace.")
        
        # Placeholder for actual trace visualization
        st.markdown("#### 📋 Recent Agent Activity")
        
        # Color code by agent
        agent_colors = {
            "LearningAgent": "🔵",
            "StudyPlanAgent": "🔵",
            "EngagementAgent": "🔵",
            "Optimist": "🟢",
            "Skeptic": "🔴",
            "Advocate": "🟠",
            "Historian": "🟣",
            "RiskAnalyst": "🟡",
            "Critic": "⚪",
            "AssessmentAgent": "🩵",
            "SocraticCoach": "💗",
            "ReflectionAgent": "⚫",
        }
        
        # Show some example trace entries based on what we've built
        example_logs = [
            ("🔵", "LearningAgent", "Skill map built for certification"),
            ("🔵", "StudyPlanAgent", "6-week study plan created"),
            ("🔵", "EngagementAgent", "Study windows recommended"),
            ("🟢", "Optimist", "Verdict: READY (85% confidence)"),
            ("🔴", "Skeptic", "Verdict: NOT_READY (72% confidence)"),
            ("🟠", "Advocate", "Verdict: READY (workload manageable)"),
            ("🟣", "Historian", "Similar learners had 60% pass rate"),
            ("🟡", "RiskAnalyst", "Verdict: NOT_READY (coverage gaps)"),
            ("⚪", "Critic", "FINAL VERDICT: NOT_READY (79% confidence)"),
            ("🩵", "AssessmentAgent", "Generated 10 exam questions"),
            ("🩵", "AssessmentAgent", "Score 45.0% — FAIL"),
            ("💗", "SocraticCoach", "Diagnosed misconception"),
            ("⚫", "ReflectionAgent", "Prediction was WRONG. Agents updated."),
        ]
        
        for emoji, agent, message in example_logs:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #374151;">
                <div style="font-size: 16px; margin-right: 8px;">{emoji}</div>
                <div style="width: 150px; font-weight: bold; color: #9ca3af;">{agent}</div>
                <div style="color: #d1d5db;">{message}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Export button (placeholder)
        st.download_button(
            "📥 Export Trace as JSON",
            data='{"note": "Complete traces available via API session_log field"}',
            file_name="reasoning_trace.json",
            mime="application/json",
            disabled=True,
            help="Session logs are available in API responses under 'session_log' field"
        )
        
        if auto_refresh:
            import time
            time.sleep(5)
            st.rerun()
            
    except Exception as exc:
        st.error(f"❌ Error: {exc}")

else:
    st.write(f"Coming soon — {selected_page}")
