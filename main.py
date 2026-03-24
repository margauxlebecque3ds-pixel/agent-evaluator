from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import os
import re, json

# Mistral client (compatible OpenAI SDK)
client = OpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1"
)

# 1️⃣ Main agent
def call_main_agent(prompt):
    response = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are an expert assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# 2️⃣ Evaluator agent
def evaluate_response(prompt, response_text):
    evaluation_prompt = f"""
You are a senior UX researcher specializing in AI agent evaluation within complex industrial software (CAD/simulation).

Your task is to evaluate an AI agent's response against a heuristic framework specifically designed for AI agents in complex software environments (not simple chatbots). This framework was built upon Nielsen (1994) and extends it to AI agents.

You must score each criterion using the detailed rubric below. Each score must be justified by citing specific elements observed (or absent) in the agent's response. Your justification must be at least 3 sentences and include concrete improvement advice if the score is below 5.

HEURISTIC EVALUATION FRAMEWORK WITH SCORING RUBRIC
====================================================

CRITERION 1 — Reasoning Transparency ("Why")
The agent must make its reasoning process visible. The user should not have to trust the AI blindly — they must be able to verify how a recommendation was produced.
Sub-questions: Does it explain why it proposes this action? Does it reveal its sources or assumptions? Can the user trace back the origin of a recommendation?

SCORING RUBRIC:
0 — No explanation whatsoever. The agent states a result or action with zero reasoning. Pure black box.
1 — A vague or generic explanation is given ("because it is best practice") but no specific reasoning tied to the actual context.
2 — Partial reasoning: the agent explains some steps but omits key assumptions or sources. The user cannot fully verify the logic.
3 — The agent explains its reasoning adequately and mentions at least one source or assumption, but the chain of logic has gaps or is not fully traceable.
4 — Clear, structured reasoning with explicit assumptions. Minor elements are missing (e.g., confidence level, source citation) but the overall logic is followable.
5 — Fully transparent: the agent explicitly states its reasoning chain step by step, cites sources or assumptions, and invites the user to verify or challenge the output.

----------------------------------------------------

CRITERION 2 — Contextual Relevance ("Where")
The agent must adapt its response to the user's role, expertise level, and the current workflow step. A junior engineer and a senior simulation expert must not receive the same response.
Sub-questions: Are suggestions adapted to the selected object and workflow step? Does the agent adapt vocabulary and detail level to the user's profile? Does it avoid suggesting unavailable actions or repeating known information?

SCORING RUBRIC:
0 — The response is completely generic, showing no awareness of the user's context, role, or current workflow step.
1 — Minimal context awareness: the agent uses some domain vocabulary but does not adapt to the user's role or workflow position.
2 — Partial adaptation: the agent shows awareness of either the workflow step OR the user profile, but not both simultaneously.
3 — The agent adapts to the context reasonably well but occasionally suggests irrelevant actions or uses an inappropriate level of detail.
4 — Well-adapted response: vocabulary, detail level, and suggestions match the user's role and workflow step. Minor mismatches possible.
5 — Perfectly tailored: the agent explicitly acknowledges the user's context, adjusts depth and vocabulary accordingly, avoids redundant information, and proposes only actions available at the current step.

----------------------------------------------------

CRITERION 3 — Human Controllability (Human Intervention)
The agent must preserve the user's ability to intervene, modify, or cancel at any point. The agent is an assistant, not an autonomous decision-maker.
Sub-questions: Can the user interrupt or manually override a suggestion? Are these actions easy to perform mid-interaction? Is cancellation reversible and free of side effects?

SCORING RUBRIC:
0 — The agent takes or strongly implies irreversible actions without any warning, confirmation request, or override mechanism.
1 — The agent mentions an action but offers no way to stop, modify, or undo it.
2 — The agent vaguely implies the user can change things but provides no concrete mechanism or instruction.
3 — The agent acknowledges user control in principle (e.g., "you can adjust this") but does not detail how, or does not address reversibility.
4 — The agent actively invites the user to validate, modify, or cancel the proposed action and provides basic guidance on how to do so.
5 — Full controllability: the agent presents the action as a suggestion pending user approval, explains how to modify or cancel it, and confirms no irreversible change was made without consent.

----------------------------------------------------

CRITERION 4 — Cognitive Load Reduction ("Less is More")
The agent must reduce the user's mental effort, not increase it. Both over-explaining and under-explaining are penalized.
Sub-questions: Is the interaction simpler than using classic menus? Are responses clear and proportionate? Does the agent offer summaries when the answer is complex?

SCORING RUBRIC:
0 — The response is overwhelming (walls of text, irrelevant info) or uselessly empty. The user must do significant extra work.
1 — The response has the right content but is poorly structured, making it hard to quickly identify the key message.
2 — The response is understandable but noticeably too long or too short for the complexity of the request. No synthesis is offered.
3 — The response is reasonably sized and structured, but could be more concise or offer a summary for a complex answer.
4 — Well-calibrated: clear, appropriately detailed, easy to act on. Minor improvements in structure or conciseness possible.
5 — Optimal cognitive load: exactly as long as needed, uses clear formatting where appropriate, offers a condensed summary when the answer is complex. Faster than any alternative.

----------------------------------------------------

CRITERION 5 — Uncertainty Management ("Doubt")
The agent must explicitly acknowledge the limits of its knowledge and avoid confident responses to ambiguous queries. In engineering contexts, a confidently wrong answer can cause costly errors.
Sub-questions: Does the AI express when it lacks sufficient data? Does it ask clarifying questions? Does it associate a confidence level to its responses? Does it propose multiple interpretations?

SCORING RUBRIC:
0 — The agent responds confidently to an ambiguous or underspecified request without acknowledging any uncertainty. High hallucination risk.
1 — The agent makes a guess without flagging it. No clarification is requested.
2 — The agent adds a generic disclaimer ("I may be wrong") but does not reformulate the query, ask for clarification, or propose alternatives.
3 — The agent identifies the ambiguity and either asks a clarifying question OR proposes one alternative interpretation, but not both.
4 — The agent clearly identifies uncertainty, asks a relevant clarifying question, and offers at least one alternative interpretation.
5 — Exemplary: explicitly flags what it does and does not know, asks targeted clarifying questions, proposes multiple interpretations, assigns explicit confidence levels.

----------------------------------------------------

CRITERION 6 — Action Segmentation ("How")
The agent must decompose complex requests into ordered, achievable steps.
Sub-questions: Does the AI break down a complex request into logical sub-steps? Are the steps ordered correctly and feasible? Does the agent indicate dependencies between steps?

SCORING RUBRIC:
0 — The agent provides a single undifferentiated response to a complex request, with no decomposition.
1 — The agent lists some steps but they are unordered, incomplete, or not feasible.
2 — The agent provides a partial step sequence but omits critical steps or fails to indicate dependencies.
3 — The agent provides a logical sequence covering main actions, but some steps lack detail or dependency information.
4 — Clear, ordered, actionable step sequence. Dependencies are mostly indicated. Minor gaps in completeness.
5 — Optimal: complete, ordered sequence, explicit dependencies, checks for prerequisite conditions before each step.

----------------------------------------------------

CRITERION 7 — Error Prevention ("The Guardrail")
The agent must anticipate and prevent user errors before they cause damage.
Sub-questions: Does the AI detect potentially destructive or erroneous requests? Can it identify inconsistencies with known physical or business constraints? Does it propose a corrected alternative?

SCORING RUBRIC:
0 — The agent executes or validates a clearly problematic request without any warning.
1 — The agent detects the problem but only blocks the action without explanation or alternative.
2 — The agent flags a potential issue vaguely with no specific guidance.
3 — The agent identifies the specific risk and explains why it is a problem, but offers no corrected alternative.
4 — The agent identifies the risk, explains it clearly, and proposes a corrected alternative. Minor gaps in proactivity.
5 — Full guardrail: proactively flags the inconsistency, explains the specific constraint violated, proposes a corrected alternative, and asks for confirmation before proceeding.

----------------------------------------------------

CRITERION 8 — Relationship with the Interface and 3D Model
The agent must bridge dialogue and direct 3D manipulation.
Sub-questions: Can the user designate a 3D object as the subject of a question? Can the AI highlight zones in the 3D view? Does it maintain sync between dialogue and 3D state? Can it annotate the model?
NOT APPLICABLE if the response involves no 3D model interaction.

SCORING RUBRIC:
0 — No awareness of the 3D context. All responses are purely textual with no reference to the interface or model state.
1 — Vaguely references the 3D environment but cannot interact with it or reference specific objects/zones.
2 — Acknowledges a 3D object mentioned by the user but cannot highlight, annotate, or synchronize with the view.
3 — Can reference selected 3D objects and describes relevant zones in text, but lacks true graphical interaction.
4 — Can reference, describe, and partially interact with the 3D environment (e.g., suggest zones to examine).
5 — Full 3D integration: references user-selected objects, highlights or annotates relevant zones in the view, maintains real-time sync between dialogue and 3D state.

----------------------------------------------------

CRITERION 9 — Interoperability (Access to Data and Project History)
The agent must act as an expert who has read the entire project file.
Sub-questions: Can the agent answer using data not currently visible in the interface? Does it clearly state which data source it consulted?
NOT APPLICABLE if the task requires no external data beyond what is in the prompt.

SCORING RUBRIC:
0 — The agent only uses information explicitly present in the current interaction.
1 — The agent alludes to external data but cannot actually access or cite it. References are fabricated or unverified.
2 — The agent accesses one external source but does not identify it clearly or explain how it was used.
3 — The agent draws on at least one identified external source and explains its relevance, but coverage is partial.
4 — The agent actively cross-references multiple relevant data sources and cites them clearly.
5 — Full interoperability: seamlessly integrates data from multiple systems (CAD, PDM, requirements, materials), cites each source explicitly, explains how cross-referencing shaped the response.

----------------------------------------------------

CRITERION 10 — Consistency Over Time ("Memory")
The agent must remember context, decisions, and user preferences from earlier in the session.
Sub-questions: Are responses consistent throughout the session? Does the agent remember prior information? Does it detect contradictions with earlier decisions? Does it distinguish session memory from long-term project memory?
NOT APPLICABLE if this is the first and only exchange in the session.

SCORING RUBRIC:
0 — No memory of prior context. Each response treats the conversation as if it started fresh.
1 — Vaguely references prior context but with inaccuracies or inconsistencies.
2 — Recalls some prior information but fails to apply it consistently, leading to contradictory suggestions.
3 — Maintains session context reasonably well but does not proactively detect contradictions with earlier decisions.
4 — Demonstrates consistent memory throughout the session and references earlier decisions appropriately.
5 — Full memory coherence: accurate session memory, applied proactively, detects and flags contradictions, distinguishes session memory from long-term project memory.

====================================================

USER PROMPT: {prompt}
AGENT RESPONSE: {response_text}

====================================================
OUTPUT FORMAT — STRICTLY VALID JSON — NO EXTRA TEXT
====================================================

{{
  "evaluation": {{
    "reasoning_transparency": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "Specific elements from the response that informed this score (quote or describe them, or note their absence).",
      "justification": "At least 3 sentences explaining the score based on the rubric above.",
      "improvement_advice": "Concrete and specific advice for the agent developer (not generic). Example: 'Add a confidence percentage after each recommendation' rather than 'be clearer'."
    }},
    "contextual_relevance": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "...",
      "justification": "...",
      "improvement_advice": "..."
    }},
    "human_controllability": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "...",
      "justification": "...",
      "improvement_advice": "..."
    }},
    "cognitive_load_reduction": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "...",
      "justification": "...",
      "improvement_advice": "..."
    }},
    "uncertainty_management": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "...",
      "justification": "...",
      "improvement_advice": "..."
    }},
    "action_segmentation": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "...",
      "justification": "...",
      "improvement_advice": "..."
    }},
    "error_prevention": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "...",
      "justification": "...",
      "improvement_advice": "..."
    }},
    "interface_and_3d_model_relationship": {{
      "score": null,
      "applicable": false,
      "observed_elements": "...",
      "justification": "Explain why this criterion is not applicable to this response.",
      "improvement_advice": "..."
    }},
    "interoperability": {{
      "score": null,
      "applicable": false,
      "observed_elements": "...",
      "justification": "Explain why this criterion is not applicable to this response.",
      "improvement_advice": "..."
    }},
    "consistency_over_time": {{
      "score": null,
      "applicable": false,
      "observed_elements": "...",
      "justification": "Explain why this criterion is not applicable to this response.",
      "improvement_advice": "..."
    }}
  }},
  "global_improvement_suggestions": [
    "High-priority suggestion 1",
    "High-priority suggestion 2",
    "High-priority suggestion 3"
  ]
}}

STRICT RULES:
- If a criterion is NOT APPLICABLE: "score": null, "applicable": false, explain why in justification.
- NEVER force a score if the criterion cannot be evaluated.
- Do NOT compute a global score.
- "observed_elements" must cite concrete elements from the response (or note their absence).
- "improvement_advice" must be specific and actionable, not generic.
- Scores must strictly follow the rubric levels. Anchor your score to the rubric descriptor that best matches.
- Respond ONLY with this JSON. No preamble, no explanation outside the JSON, no markdown code fences.
"""
    # Mistral API call
    evaluation = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are a senior UX researcher evaluating AI agents using a structured rubric. You respond only in valid JSON."},
            {"role": "user", "content": evaluation_prompt}
        ]
    ).choices[0].message.content

    # Cleanup: strictly extract JSON if the model adds extra text
    match = re.search(r'\{.*\}', evaluation, re.DOTALL)

    if match:
        evaluation_json = match.group(0)

        try:
            data = json.loads(evaluation_json)

            for c in data["evaluation"]:
                criterion = data["evaluation"][c]
                if criterion.get("applicable") == False:
                    continue
                score = criterion.get("score")
                if score is None:
                    continue
                if not isinstance(score, (int, float)):
                    continue
                data["evaluation"][c]["score"] = max(0, min(5, score))

            return json.dumps(data)

        except json.JSONDecodeError:
            return evaluation_json

    else:
        return evaluation