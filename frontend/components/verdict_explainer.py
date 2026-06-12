"""
Verdict Explainer Component

Shows exactly why the system gave a verdict with full evidence chain.
No vague claims — every number explained, every agent cited.

Use in assessment page:
  from frontend.components.verdict_explainer import render_verdict_explainer
  render_verdict_explainer(get_api_state())
"""

import streamlit as st
from typing import Dict, List, Tuple


def render_verdict_explainer(state: Dict):
    """
    Shows exactly why the system gave this verdict.
    Every number explained. Every agent cited.
    """
    
    verdict = state.get("readiness_verdict", "")
    confidence = state.get("readiness_confidence", 0)
    reasoning = state.get("readiness_reasoning", "")
    votes = state.get("council_votes", {})
    score = state.get("assessment_score", 0)
    breakdown = state.get("assessment_breakdown", {})
    weak_topics = state.get("weak_topics", [])
    
    if not verdict:
        return  # No verdict yet
    
    # Color and icon maps
    color_map = {
        "READY": "#00c896",
        "NOT_READY": "#ff4757",
        "DELAY": "#ffa502"
    }
    icon_map = {
        "READY": "✅",
        "NOT_READY": "❌",
        "DELAY": "⏳"
    }
    
    color = color_map.get(verdict, "#8b8b9e")
    icon = icon_map.get(verdict, "❓")
    
    # === MAIN VERDICT BANNER ===
    st.markdown(
        f"""
        <div style='
          background: {color}11;
          border: 2px solid {color};
          border-radius: 16px;
          padding: 24px;
          margin: 16px 0;
        '>
          <div style='font-size: 28px; font-weight: 900;
               color: {color}; margin-bottom: 8px;'>
            {icon} {verdict.replace("_", " ")}
          </div>
          <div style='font-size: 36px; font-weight: 900;
               color: white; margin-bottom: 8px;'>
            {confidence}% confidence
          </div>
          <div style='font-size: 15px; color: #c0c0d0;
               line-height: 1.6;'>
            {reasoning}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # === WHY THIS VERDICT — STEP BY STEP ===
    st.markdown("### 🔍 Why this verdict?")
    
    # Step 1: Assessment Score
    threshold = 70
    score_gap = score - threshold
    score_color = "#00c896" if score >= threshold else "#ff4757"
    
    st.markdown(
        f"""
        <div style='
          background: rgba(255,255,255,0.03);
          border-left: 3px solid {score_color};
          border-radius: 8px;
          padding: 14px 16px;
          margin: 8px 0;
        '>
          <div style='font-weight: 600; margin-bottom: 6px;'>
            1️⃣ Assessment Score: 
            <span style='color: {score_color}'>
              {score:.1f}%
            </span>
            (threshold: {threshold}%)
          </div>
          <div style='color: #8b8b9e; font-size: 13px;'>
            {"✅ Above threshold — exam score looks good." if score >= threshold
            else f"❌ {abs(score_gap):.1f}% below the passing threshold of {threshold}%."}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Step 2: Topic Breakdown
    if breakdown and isinstance(breakdown, dict):
        weak_topics_list = [
            (t, d) for t, d in breakdown.items() 
            if isinstance(d, dict) and d.get("score", 0) < threshold
        ]
        strong_topics_list = [
            (t, d) for t, d in breakdown.items()
            if isinstance(d, dict) and d.get("score", 0) >= threshold
        ]
        
        # Build HTML for weak topics
        weak_html = ""
        for t, d in sorted(weak_topics_list, key=lambda x: x[1].get("score", 0)):
            score_val = d.get("score", 0)
            correct = d.get("correct", 0)
            total = d.get("total", 0)
            weak_html += (
                f"<div style='color: #ff4757; margin: 3px 0;'>"
                f"❌ <strong>{t}</strong>: {score_val:.0f}% "
                f"({correct}/{total} correct)"
                f"</div>"
            )
        
        # Build HTML for strong topics
        strong_html = ""
        for t, d in strong_topics_list:
            score_val = d.get("score", 0)
            strong_html += (
                f"<div style='color: #00c896; margin: 3px 0;'>"
                f"✅ <strong>{t}</strong>: {score_val:.0f}%"
                f"</div>"
            )
        
        st.markdown(
            f"""
            <div style='
              background: rgba(255,255,255,0.03);
              border-left: 3px solid #ffa502;
              border-radius: 8px;
              padding: 14px 16px;
              margin: 8px 0;
            '>
              <div style='font-weight: 600; margin-bottom: 8px;'>
                2️⃣ Topic Analysis: 
                <span style='color: #ff4757;'>{len(weak_topics_list)} weak</span> / 
                <span style='color: #00c896;'>{len(strong_topics_list)} strong</span>
              </div>
              <div style='font-size: 13px;'>
                {weak_html}
                {strong_html}
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Step 3: Council Evidence
    if votes and isinstance(votes, dict):
        not_ready_agents = [
            (agent, vote) for agent, vote in votes.items()
            if isinstance(vote, dict) and vote.get("verdict") in ["NOT_READY", "DELAY"]
        ]
        
        if not_ready_agents:
            evidence_html = ""
            for agent, vote in not_ready_agents:
                agent_display = agent.replace("_", " ").title()
                evidence_list = vote.get("evidence", [])
                if isinstance(evidence_list, list):
                    for e in evidence_list[:2]:
                        evidence_html += (
                            f"<div style='color: #ff4757; "
                            f"margin: 3px 0; font-size: 13px;'>"
                            f"⚠️ <strong>{agent_display}:</strong> {e}</div>"
                        )
            
            st.markdown(
                f"""
                <div style='
                  background: rgba(255,255,255,0.03);
                  border-left: 3px solid #ff4757;
                  border-radius: 8px;
                  padding: 14px 16px;
                  margin: 8px 0;
                '>
                  <div style='font-weight: 600; margin-bottom: 8px;'>
                    3️⃣ Council Concerns 
                    ({len(not_ready_agents)} agents flagged issues)
                  </div>
                  {evidence_html}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Step 4: What Needs to Improve
    if weak_topics:
        topics_html = ""
        for t in weak_topics:
            topics_html += (
                f"<div style='margin: 4px 0; font-size: 13px;'>"
                f"→ <strong>{t}</strong> — needs focused study"
                f"</div>"
            )
        
        st.markdown(
            f"""
            <div style='
              background: rgba(79,142,247,0.06);
              border-left: 3px solid #4f8ef7;
              border-radius: 8px;
              padding: 14px 16px;
              margin: 8px 0;
            '>
              <div style='font-weight: 600; margin-bottom: 8px;'>
                4️⃣ What You Need to Improve
              </div>
              {topics_html}
              <div style='color: #8b8b9e; font-size: 12px; 
                   margin-top: 8px;'>
                Scroll down to see your adapted learning path
                and resources for each weak topic.
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
