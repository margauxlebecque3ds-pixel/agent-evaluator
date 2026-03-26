from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import os
import re, json

client = OpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1"
)

def call_main_agent(prompt):
    response = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are an expert assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def parse_conversation(text):
    """
    Parse a raw conversation string into a list of exchanges.
    Detects timestamps like '01:33 PM' or '13:33' to split turns.
    Assumes user speaks first, then alternates with LEO.
    Returns a list of dicts: [{"role": "USER"|"LEO", "index": 1, "message": "..."}]
    """
    # Split on timestamp pattern HH:MM AM/PM or HH:MM
    parts = re.split(r'\d{1,2}:\d{2}(?:\s*[AP]M)?', text)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) < 2:
        return None  # Not a conversation, single exchange

    exchanges = []
    for i, msg in enumerate(parts):
        role = "USER" if i % 2 == 0 else "LEO"
        exchanges.append({
            "role": role,
            "index": i + 1,
            "message": msg.strip()
        })
    return exchanges

def format_conversation_for_prompt(exchanges):
    """Format parsed exchanges into a readable string for the LLM."""
    lines = []
    exchange_num = 0
    for i in range(0, len(exchanges) - 1, 2):
        exchange_num += 1
        user_msg = exchanges[i]["message"] if i < len(exchanges) else ""
        leo_msg = exchanges[i+1]["message"] if i+1 < len(exchanges) else ""
        lines.append(f"--- EXCHANGE {exchange_num} ---")
        lines.append(f"[USER]: {user_msg}")
        lines.append(f"[LEO]: {leo_msg}")
        lines.append("")
    return "\n".join(lines)

def evaluate_response(prompt, response_text, language="en", mode="single", conversation_raw=""):
    if language == "fr":
        lang_instruction = "Réponds UNIQUEMENT en français. Tous les champs du JSON doivent être rédigés en français."
    else:
        lang_instruction = "Respond ONLY in English. All JSON fields must be written in English."

    # ── SINGLE EXCHANGE MODE ──────────────────────────────────────────────────
    if mode == "single":
        evaluation_prompt = f"""
You are a senior UX researcher specializing in AI agent evaluation within complex industrial software (CAD/simulation).

LANGUAGE INSTRUCTION: {lang_instruction}

Evaluate the AI agent's response against the heuristic framework below. Score each criterion with a detailed rubric-anchored justification.

HEURISTIC EVALUATION FRAMEWORK
================================

CRITERION 1 — Request Adequacy
Did the agent understand the request and respond in the right format?
Sub-questions: Right format? On topic? Full coverage? Key info immediately visible?
0: Completely misses the request. 1: Wrong format or partial. 2: Right topic, partially right format. 3: Main request covered, minor gaps. 4: Well-structured, full coverage. 5: Perfect format, every part answered.

CRITERION 2 — Transparency of Reasoning ("Why")
Does the agent make its reasoning visible?
Sub-questions: Explains why? Sources/assumptions visible? Traceable recommendation?
0: No explanation, pure black box. 1: Vague generic explanation. 2: Partial reasoning, key gaps. 3: Adequate reasoning, some gaps. 4: Clear structured reasoning, minor gaps. 5: Full step-by-step reasoning, sources cited, user invited to verify.

CRITERION 3 — Contextual Relevance ("Where")
Does the agent adapt to the user's role, expertise, and workflow step?
Sub-questions: Adapted to workflow step? User role understood? Vocabulary adapted? No unavailable actions? No redundant info?
0: Completely generic. 1: Minimal context awareness. 2: Partial adaptation. 3: Reasonable adaptation, minor mismatches. 4: Well-adapted, minor gaps. 5: Perfectly tailored.

CRITERION 4 — Human Controllability
Does the agent preserve user control?
Sub-questions: Can user interrupt/modify? Easy to do mid-interaction? Reversible with no side effects?
0: Irreversible actions, no warning. 1: No override mechanism. 2: Vague implication of control. 3: Acknowledges control in principle. 4: Actively invites validation/modification. 5: Full controllability, suggestions only, explains how to modify/cancel.

CRITERION 5 — Cognitive Load Reduction ("Less is More")
Does the agent reduce mental effort?
Sub-questions: Simpler than menus? Actually simplifies? Right size response? Summary offered?
0: Overwhelming or empty. 1: Right content, poor structure. 2: Understandable but wrong size. 3: Reasonable but could be tighter. 4: Well-calibrated. 5: Optimal length, clear formatting, summary when needed.

CRITERION 6 — Reliability & Anticipation ("Doubt & Guardrail")
Does the agent manage uncertainty and prevent errors?
Sub-questions: Asks clarification when ambiguous? Catches impossible parameters? Expresses confidence levels? Anticipates downstream consequences?
0: Confident on ambiguous requests AND executes problematic actions. 1: Guesses without flagging OR blocks without explanation. 2: Generic disclaimer OR vague flag. 3: Identifies ambiguity/risk, asks OR proposes one alternative. 4: Identifies + asks + proposes alternative. 5: Flags uncertainty AND errors, targeted questions, multiple alternatives, confidence levels, anticipates downstream effects.

CRITERION 7 — Task Segmentation ("How")
Does the agent break complex tasks into steps?
Sub-questions: Logical sub-steps? Coherent order? Dependencies pointed out?
0: No decomposition. 1: Unordered/incomplete steps. 2: Partial sequence, missing dependencies. 3: Logical sequence, some gaps. 4: Clear ordered sequence, mostly complete. 5: Complete sequence, explicit dependencies, prerequisites checked.

CRITERION 8 — Interface & 3D Model Relationship
Does the agent bridge conversation and 3D model?
NOT APPLICABLE if no 3D model interaction.
0: No 3D awareness. 1: Vague 3D reference. 2: Acknowledges object, no interaction. 3: References objects in text. 4: Partial 3D interaction. 5: Full sync, highlights, annotations.

CRITERION 9 — Interoperability (Data Access)
Does the agent act like an expert who read the full project?
NOT APPLICABLE if no external data needed.
0: Only current interaction data. 1: Alludes to external data, fabricated. 2: One source, unclear. 3: One identified source. 4: Multiple sources cross-referenced. 5: Full integration, all sources cited.

CRITERION 10 — Consistency Over Time ("Memory")
NOT APPLICABLE for a single exchange.

USER PROMPT: {prompt}
AGENT RESPONSE: {response_text}

OUTPUT — STRICTLY VALID JSON — NO EXTRA TEXT:
{{
  "evaluation": {{
    "request_adequacy": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "transparency_of_reasoning": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "contextual_relevance": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "human_controllability": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "cognitive_load_reduction": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "reliability_and_anticipation": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "task_segmentation": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "interface_and_3d_model_relationship": {{"score": null, "applicable": false, "observed_elements": "...", "justification": "Not applicable: single text exchange with no 3D model interaction.", "improvement_advice": "..."}},
    "interoperability": {{"score": null, "applicable": false, "observed_elements": "...", "justification": "Not applicable: no external data required.", "improvement_advice": "..."}},
    "consistency_over_time": {{"score": null, "applicable": false, "observed_elements": "...", "justification": "Not applicable: single exchange.", "improvement_advice": "..."}}
  }},
  "global_improvement_suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
STRICT RULES: No global score. observed_elements must cite concrete elements. improvement_advice must be specific. Respond ONLY with JSON.
"""

    # ── MULTI EXCHANGE MODE ───────────────────────────────────────────────────
    else:
        exchanges = parse_conversation(conversation_raw)
        if not exchanges:
            # Fallback: treat as single
            return evaluate_response(prompt, conversation_raw, language, "single", "")

        conversation_formatted = format_conversation_for_prompt(exchanges)
        n_exchanges = len(exchanges) // 2

        evaluation_prompt = f"""
You are a senior UX researcher specializing in AI agent evaluation within complex industrial software (CAD/simulation).

LANGUAGE INSTRUCTION: {lang_instruction}

You are evaluating a FULL CONVERSATION between a user and LEO (an AI agent by Dassault Systèmes). The conversation has {n_exchanges} exchanges.

The conversation is structured as:
--- EXCHANGE N ---
[USER]: user message
[LEO]: LEO's response

Your task: evaluate the overall quality of LEO's responses across the entire conversation using the 10 heuristics below.

For each criterion:
- Give a GLOBAL score (0-5) reflecting the overall quality across all exchanges
- In observed_elements: cite SPECIFIC exchanges by number (e.g. "Exchange 2", "Exchange 4") — both positive examples AND problematic ones
- In justification: explain the score with references to specific exchanges
- In improvement_advice: give actionable advice, citing which exchange(s) need improvement
- If a criterion is NOT APPLICABLE (e.g. Consistency Over Time with only 1 exchange, or 3D model with no 3D content): set applicable=false

CONVERSATION TO EVALUATE:
{conversation_formatted}

HEURISTIC EVALUATION FRAMEWORK
================================

CRITERION 1 — Request Adequacy
Did LEO understand each request and respond in the right format throughout the conversation?
0: Misses requests consistently. 1: Wrong format or partial in most exchanges. 2: Right topic, partially right format. 3: Main requests covered, some gaps. 4: Well-structured across exchanges. 5: Every request perfectly addressed.

CRITERION 2 — Transparency of Reasoning ("Why")
Does LEO consistently make its reasoning visible?
0: No explanation in any exchange. 1: Vague generic explanations. 2: Partial reasoning. 3: Adequate reasoning, some gaps. 4: Clear structured reasoning overall. 5: Full transparency across all exchanges.

CRITERION 3 — Contextual Relevance ("Where")
Does LEO adapt to the user's evolving context across the conversation?
0: Completely generic throughout. 1: Minimal adaptation. 2: Partial adaptation. 3: Reasonable adaptation overall. 4: Well-adapted, minor gaps. 5: Perfectly tailored, tracks user context evolution.

CRITERION 4 — Human Controllability
Does LEO preserve user control throughout the conversation?
0: Irreversible actions, no warning. 1: No override mechanisms. 2: Vague implication of control. 3: Acknowledges control in principle. 4: Actively invites validation. 5: Full controllability throughout.

CRITERION 5 — Cognitive Load Reduction ("Less is More")
Does LEO keep responses appropriately sized across the conversation?
0: Overwhelming or empty responses. 1: Poor structure overall. 2: Wrong size in most responses. 3: Reasonable but could be tighter. 4: Well-calibrated overall. 5: Optimal throughout.

CRITERION 6 — Reliability & Anticipation ("Doubt & Guardrail")
Does LEO manage uncertainty and prevent errors across the conversation?
0: Confident on ambiguous requests throughout. 1: Guesses without flagging consistently. 2: Generic disclaimers only. 3: Identifies some ambiguities. 4: Good uncertainty management overall. 5: Exemplary throughout.

CRITERION 7 — Task Segmentation ("How")
Does LEO break complex tasks into steps when needed?
0: No decomposition in any exchange. 1: Unordered/incomplete steps. 2: Partial sequences. 3: Logical sequences, some gaps. 4: Clear ordered sequences overall. 5: Complete sequences with dependencies throughout.

CRITERION 8 — Interface & 3D Model Relationship
Does LEO bridge conversation and 3D model?
NOT APPLICABLE if no 3D model interaction in the conversation.
0-5: same as single mode.

CRITERION 9 — Interoperability (Data Access)
Does LEO reference external project data?
NOT APPLICABLE if no external data needed in the conversation.
0-5: same as single mode.

CRITERION 10 — Consistency Over Time ("Memory") ← KEY CRITERION FOR CONVERSATIONS
Does LEO remember context, decisions, and user preferences from earlier exchanges?
APPLICABLE since this is a multi-exchange conversation.
Sub-questions: Consistent responses throughout? Remembers earlier info? Tracks what user has done? Spots contradictions? Distinguishes session vs project memory?
0: No memory, each exchange treated as fresh start. 1: Vague inconsistent references to prior context. 2: Recalls some info but inconsistently. 3: Reasonable session memory, misses some contradictions. 4: Good memory, references earlier decisions appropriately. 5: Perfect memory, proactively applies context, flags contradictions.

OUTPUT — STRICTLY VALID JSON — NO EXTRA TEXT:
{{
  "evaluation": {{
    "request_adequacy": {{
      "score": 0,
      "applicable": true,
      "observed_elements": "Cite specific exchanges: e.g. 'Exchange 1: adequate. Exchange 3: too vague.'",
      "justification": "Global assessment with exchange references.",
      "improvement_advice": "Specific advice citing which exchange(s) to improve."
    }},
    "transparency_of_reasoning": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "contextual_relevance": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "human_controllability": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "cognitive_load_reduction": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "reliability_and_anticipation": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "task_segmentation": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "interface_and_3d_model_relationship": {{"score": null, "applicable": false, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "interoperability": {{"score": null, "applicable": false, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}},
    "consistency_over_time": {{"score": 0, "applicable": true, "observed_elements": "...", "justification": "...", "improvement_advice": "..."}}
  }},
  "global_improvement_suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
STRICT RULES: No global score. Cite exchange numbers in observed_elements and justification. improvement_advice must reference specific exchanges. Respond ONLY with JSON.
"""

    evaluation = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are a senior UX researcher evaluating AI agents. You respond only in valid JSON."},
            {"role": "user", "content": evaluation_prompt}
        ]
    ).choices[0].message.content

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
                if score is None or not isinstance(score, (int, float)):
                    continue
                data["evaluation"][c]["score"] = max(0, min(5, score))
            return json.dumps(data)
        except json.JSONDecodeError:
            return evaluation_json
    else:
        return evaluation