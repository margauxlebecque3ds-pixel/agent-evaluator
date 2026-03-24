# app.py

import streamlit as st
from main import evaluate_response
import json

st.set_page_config(page_title="eval.ai", layout="wide", page_icon="🔬")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap');

  .stApp { background-color: #0d0d0d; color: #e0e0e0; }
  * { box-sizing: border-box; }

  .navbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 2rem; border-bottom: 1px solid #1e1e1e; margin-bottom: 2rem;
  }
  .navbar-brand {
    display: flex; align-items: center; gap: 0.5rem;
    font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.1rem; color: white;
  }
  .ds-icon {
    background: #0050c8; color: white; width: 32px; height: 32px;
    border-radius: 6px; display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 0.8rem;
  }
  .navbar-version { font-family: 'Space Mono', monospace; font-size: 0.8rem; color: #555; }

  .hero { text-align: center; padding: 2rem 1rem 3rem 1rem; max-width: 700px; margin: 0 auto; }
  .hero-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #111; border: 1px solid #2a2a2a; border-radius: 20px;
    padding: 0.3rem 1rem; font-family: 'Space Mono', monospace;
    font-size: 0.75rem; color: #aaa; margin-bottom: 1.5rem;
  }
  .dot { width: 7px; height: 7px; background: #0050c8; border-radius: 50%; display: inline-block; }
  .hero-title { font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 700; color: white; line-height: 1.15; margin-bottom: 0.3rem; }
  .accent { color: #4d8bff; }
  .hero-subtitle { font-family: 'Inter', sans-serif; font-size: 1rem; color: #777; margin-bottom: 1rem; }
  .hero-desc { font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #555; line-height: 1.6; margin-bottom: 1rem; }
  .hero-link { font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #4d8bff; }

  .form-label { font-family: 'Space Mono', monospace; font-size: 0.7rem; letter-spacing: 0.12em; color: #555; text-transform: uppercase; margin-bottom: 0.5rem; }

  textarea {
    background: #111 !important; border: 1px solid #1e1e1e !important;
    border-radius: 10px !important; color: #c0c0c0 !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.82rem !important;
  }
  textarea:focus { border-color: #0050c8 !important; box-shadow: 0 0 0 2px rgba(0,80,200,0.2) !important; }
  textarea::placeholder { color: #333 !important; }

  .stButton { display: flex; justify-content: center; margin-top: 1.5rem; }
  .stButton > button {
    background: linear-gradient(90deg, #003189, #0050c8); color: white; border: none;
    padding: 0.75rem 2.5rem; border-radius: 10px; font-family: 'Space Mono', monospace;
    font-size: 0.9rem; font-weight: 700; letter-spacing: 0.03em;
  }
  .stButton > button:hover { opacity: 0.85; }

  .results-title { font-family: 'Inter', sans-serif; font-size: 1.3rem; font-weight: 700; color: white; margin: 2rem 0 1.5rem 0; border-bottom: 1px solid #1e1e1e; padding-bottom: 0.8rem; }

  .criterion-card { background: #111; border: 1px solid #1e1e1e; border-left: 4px solid #0050c8; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
  .criterion-card.red    { border-left-color: #e53935; }
  .criterion-card.orange { border-left-color: #f57c00; }
  .criterion-card.green  { border-left-color: #2e7d32; }
  .criterion-card.gray   { border-left-color: #444; }

  .crit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }
  .crit-name { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.95rem; color: #e0e0e0; }
  .score-pill { font-family: 'Space Mono', monospace; font-size: 0.8rem; font-weight: 700; padding: 0.2rem 0.8rem; border-radius: 20px; }
  .pill-red    { background: #2a1010; color: #e53935; }
  .pill-orange { background: #2a1a00; color: #f57c00; }
  .pill-green  { background: #0a2a0a; color: #4caf50; }
  .pill-gray   { background: #1a1a1a; color: #777; }

  .crit-detail { font-family: 'Inter', sans-serif; font-size: 0.83rem; color: #666; margin-top: 0.4rem; line-height: 1.6; }
  .crit-detail strong { color: #888; }

  .suggestions-box { background: #0a0f1a; border: 1px solid #1a2a4a; border-radius: 10px; padding: 1.5rem; margin-top: 2rem; }
  .suggestions-box h3 { font-family: 'Inter', sans-serif; color: #4d8bff; font-size: 1rem; margin-bottom: 1rem; }
  .suggestions-box li { font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #888; margin-bottom: 0.5rem; line-height: 1.6; }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0 !important; }
  label { display: none !important; }
  hr { display: none; }
</style>

<div class="navbar">
  <div class="navbar-brand"><div class="ds-icon">3DS</div> eval.ai</div>
  <div class="navbar-version">v0.1</div>
</div>

<div class="hero">
  <div class="hero-badge"><span class="dot"></span> UX-driven AI evaluation</div>
  <div class="hero-title">Évaluez les réponses<br><span class="accent">de LEO</span></div>
  <div class="hero-subtitle">Le virtual companion de Dassault Systèmes</div>
  <div class="hero-desc">Collez une question et la réponse de LEO. Obtenez une évaluation UX instantanée basée<br>sur des critères de qualité éprouvés.</div>
  <span class="hero-link">See the 10 heuristics list in details →</span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="form-label">Question Utilisateur</div>', unsafe_allow_html=True)
    prompt = st.text_area("q", height=200, placeholder="Collez la question posée à l'agent…", label_visibility="collapsed")
with col2:
    st.markdown('<div class="form-label">Réponse de l\'Agent</div>', unsafe_allow_html=True)
    response_agent = st.text_area("r", height=200, placeholder="Collez la réponse générée par l'agent…", label_visibility="collapsed")

if st.button("⚡ Run Evaluation"):
    if prompt and response_agent:
        with st.spinner("Évaluation en cours…"):
            evaluation = evaluate_response(prompt, response_agent)

        try:
            from json_repair import repair_json
            data = json.loads(repair_json(evaluation))
        except Exception as e:
            st.error(f"Erreur : {type(e).__name__} — {e}")
            st.code(evaluation)
            st.stop()

        st.markdown('<div class="results-title">Criteria Details</div>', unsafe_allow_html=True)

        for criterion, content in data["evaluation"].items():
            criterion_name = criterion.replace("_", " ").title()
            score = content.get("score")
            applicable = content.get("applicable", True)

            if not applicable or score is None:
                color = "gray"; display_score = "N/A"; pill = "pill-gray"
            elif score <= 2:
                color = "red"; display_score = f"{score} / 5"; pill = "pill-red"
            elif score <= 4:
                color = "orange"; display_score = f"{score} / 5"; pill = "pill-orange"
            else:
                color = "green"; display_score = f"{score} / 5"; pill = "pill-green"

            observed = content.get("observed_elements", "")
            justif   = content.get("justification", "")
            advice   = content.get("improvement_advice", "")

            html = f'<div class="criterion-card {color}"><div class="crit-header"><div class="crit-name">{criterion_name}</div><div class="score-pill {pill}">{display_score}</div></div>'
            if observed:
                html += f'<div class="crit-detail"><strong>🔍 Observed:</strong> {observed}</div>'
            if justif:
                html += f'<div class="crit-detail"><strong>📋 Justification:</strong> {justif}</div>'
            if advice and applicable and score is not None and score < 5:
                html += f'<div class="crit-detail"><strong>💡 Advice:</strong> {advice}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        suggestions = data.get("global_improvement_suggestions", [])
        if suggestions:
            s_html = '<div class="suggestions-box"><h3>🌐 Global Improvement Suggestions</h3><ul>'
            for s in suggestions:
                s_html += f"<li>{s}</li>"
            s_html += "</ul></div>"
            st.markdown(s_html, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Remplis les deux champs avant de lancer l'évaluation.")