"""Everything that talks to Google Gemini: client, prompt and reply parsing."""
import json
import os
import re

from google import genai
from google.genai import types

from config import CATEGORY_TIPS, GOAL_DESCRIPTIONS, MODEL


def get_client():
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    return genai.Client(api_key=key)


def ask_gemini(prompt, json_mode=False):
    """Send a prompt to Gemini and return the reply text."""
    client = get_client()

    config = types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=4096,
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config,
    )

    return response.text or ""


def build_prompt(income, expenses, goal):
    """Turn the user's numbers into the prompt for the AI."""
    lines = []

    for name, amount in expenses.items():
        percent = round(amount / income * 100, 1)
        tip = CATEGORY_TIPS.get(name.lower())

        line = f"- {name}: Rs {amount:,.0f} ({percent}% of income)"
        if tip:
            line += f" | guideline: {tip}"

        lines.append(line)

    goal_text = GOAL_DESCRIPTIONS.get(
        goal, "General financial health and better saving habits."
    )

    return f"""You are a personal finance advisor for someone in India. All amounts are in Indian rupees.

Monthly income: Rs {income:,.0f}

Monthly spending:
{chr(10).join(lines)}

Financial goal: {goal}
{goal_text}

Do three things:
1. budget: a recommended monthly budget. One entry per category above (add "savings" if it is missing). The amounts should add up to at most the monthly income.
2. analysis: for each category, the percent of income currently spent, and a status: "over" if it is above the guideline or clearly too high, otherwise "ok". Add a one-line note.
3. suggestions: 3 to 5 specific actions. Each one must include a rupee amount and what it is for. Tie them to the goal.

Reply with ONLY valid JSON in exactly this shape, nothing else:
{{
  "budget": [{{"category": "rent", "amount": 15000}}],
  "analysis": [{{"category": "rent", "percent": 30.0, "status": "ok", "note": "short note"}}],
  "suggestions": ["Cut dining by Rs 1500 and move it to your emergency fund."]
}}"""


def extract_json(text):
    """Pull a JSON object out of the AI reply. Returns None if it cannot."""
    text = (text or "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Sometimes Gemini returns JSON inside markdown fences
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Last attempt: extract the outer JSON object
    braces = re.search(r"\{.*\}", text, re.DOTALL)
    if braces:
        try:
            return json.loads(braces.group(0))
        except json.JSONDecodeError:
            pass

    return None
