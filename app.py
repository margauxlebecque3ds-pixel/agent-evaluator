# app.py

import streamlit as st
from main import evaluate_response
import json

st.set_page_config(page_title="AI Agent Evaluation", layout="wide", page_icon="🔬")

# ── CSS Dassault Systèmes ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp { background-color: #f4f6f9; }

    /* Header banner */
    .header-banner {
        background: linear-gradient(90deg, #003189 0%, #0050c8 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .header-banner h1 {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.01em;
    }
    .header-banner p {
        color: rgba(255,255,255,0.75);
        margin: 0.4rem 0 0 0;
        font-size: 0.95rem;
    }

    /* Input labels */
    label { font-weight: 600 !important; color: #003189 !important; }

    /* Criteria card */
    .criterion-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #0050c8;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .criterion-card.red   { border-left-color: #e53935; }
    .criterion-card.orange{ border-left-color: #f57c00; }
    .criterion-card.green { border-left-color: #2e7d32; }
    .criterion-card.gray  { border-left-color: #9e9e9e; }

    .criterion-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
    }
    .score-badge {
        display: inline-block;
        padding: 0.15rem 0.7rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        margin-left: 0.5rem;
    }
    .score-red    { background:#fde8e8; color:#c62828; }
    .score-orange { background:#fff3e0; color:#e65100; }
    .score-green  { background:#e8f5e9; color:#1b5e20; }
    .score-gray   { background:#f5f5f5; color:#616161; }

    .detail-row { margin-top: 0.6rem; font-size: 0.88rem; color: #333; }
    .detail-label { font-weight: 600; color: #555; }

    /* Global suggestions */
    .suggestions-box {
        background: #e8f0fe;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-top: 1.5rem;
    }
    .suggestions-box h3 { color: #003189; margin-bottom: 0.8rem; }

    /* Button */
    .stButton > button {
        background: #003189;
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: background 0.2s;
    }
    .stButton > button:hover { background: #0050c8; }

    /* Hide default streamlit divider */
    hr { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>🔬 AI Agent Evaluation</h1>
    <p>Heuristic-based evaluation of the Dassault Systèmes AI Virtual Companion — 10 UX criteria</p>
</div>
""", unsafe_allow_html=True)

# ── Inputs ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    prompt = st.text_area("User Prompt", height=150, placeholder="Enter the user's question or request...")
with col2:
    response_agent = st.text_area("Agent Response", height=150, placeholder="Paste the AI agent's response here...")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("▶ Run Evaluation"):
    if prompt and response_agent:
        with st.spinner("Evaluating with heuristic framework..."):
            evaluation = evaluate_response(prompt, response_agent)

        try:
            from json_repair import repair_json
            data = json.loads(repair_json(evaluation))
        except Exception as e:
            st.error(f"Parsing error: {type(e).__name__} — {e}")
            st.code(evaluation)
            st.stop()

        st.markdown("### Criteria Details")

        for criterion, content in data["evaluation"].items():
            criterion_name = criterion.replace("_", " ").title()
            score = content.get("score")
            applicable = content.get("applicable", True)

            if not applicable or score is None:
                color = "gray"
                display_score = "N/A"
                badge_class = "score-gray"
            elif score <= 2:
                color = "red"
                display_score = f"{score} / 5"
                badge_class = "score-red"
            elif score <= 4:
                color = "orange"
                display_score = f"{score} / 5"
                badge_class = "score-orange"
            else:
                color = "green"
                display_score = f"{score} / 5"
                badge_class = "score-green"

            observed   = content.get("observed_elements", "")
            justif     = content.get("justification", "")
            advice     = content.get("improvement_advice", "")

            card_html = f"""
            <div class="criterion-card {color}">
                <div class="criterion-title">
                    {criterion_name}
                    <span class="score-badge {badge_class}">{display_score}</span>
                </div>
            """
            if observed:
                card_html += f'<div class="detail-row"><span class="detail-label">🔍 Observed:</span> {observed}</div>'
            if justif:
                card_html += f'<div class="detail-row"><span class="detail-label">📋 Justification:</span> {justif}</div>'
            if advice and applicable and score is not None and score < 5:
                card_html += f'<div class="detail-row"><span class="detail-label">💡 Advice:</span> {advice}</div>'
            card_html += "</div>"

            st.markdown(card_html, unsafe_allow_html=True)

        # Global suggestions
        suggestions = data.get("global_improvement_suggestions", [])
        if suggestions:
            sugg_html = '<div class="suggestions-box"><h3>🌐 Global Improvement Suggestions</h3><ul>'
            for s in suggestions:
                sugg_html += f"<li style='margin-bottom:0.4rem'>{s}</li>"
            sugg_html += "</ul></div>"
            st.markdown(sugg_html, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Please fill in both the prompt and the agent response.")