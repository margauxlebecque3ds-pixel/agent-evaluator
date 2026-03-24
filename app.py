# app.py

import streamlit as st
from main import evaluate_response
import json

st.set_page_config(page_title="AI Agent Evaluation", layout="wide")
st.title("Evaluation of the Dassault Systèmes AI Virtual Companion")

prompt = st.text_area("User Prompt")
response_agent = st.text_area("Agent Response")

if st.button("Run Evaluation"):
    if prompt and response_agent:
        with st.spinner("Evaluating..."):
            evaluation = evaluate_response(prompt, response_agent)

        try:
            from json_repair import repair_json
            data = json.loads(repair_json(evaluation))
        except Exception as e:
            st.error(f"Erreur exacte : {type(e).__name__} — {e}")
            st.code(evaluation)
            st.stop()

        st.subheader("Criteria Details")

        for criterion, content in data["evaluation"].items():
            criterion_name = criterion.replace("_", " ").capitalize()

            score = content.get("score")
            applicable = content.get("applicable", True)

            # Determine color
            if not applicable or score is None:
                color = "gray"
                display_score = "Not applicable"
            elif score <= 2:
                color = "red"
                display_score = f"{score} / 5"
            elif score <= 4:
                color = "orange"
                display_score = f"{score} / 5"
            else:
                color = "green"
                display_score = f"{score} / 5"

            # Header with score
            st.markdown(
                f"**{criterion_name}** : <span style='color:{color}; font-size:1.1em'>{display_score}</span>",
                unsafe_allow_html=True
            )

            # Observed elements
            observed = content.get("observed_elements", "")
            if observed:
                st.markdown(f"🔍 **Observed:** {observed}")

            # Justification
            justification = content.get("justification", "")
            if justification:
                st.markdown(f"📋 **Justification:** {justification}")

            # Improvement advice (only if applicable and score < 5)
            advice = content.get("improvement_advice", "")
            if advice and applicable and score is not None and score < 5:
                st.markdown(f"💡 **Improvement advice:** {advice}")

            st.divider()

        # Global improvement suggestions
        suggestions = data.get("global_improvement_suggestions", [])
        if suggestions:
            st.subheader("Global Improvement Suggestions")
            for suggestion in suggestions:
                st.write(f"• {suggestion}")

    else:
        st.warning("Please fill in both the prompt and the agent response.")