"""All web routes of the app."""
import logging

from flask import Blueprint, jsonify, render_template, request

from config import MAX_AMOUNT
from database import get_monthly_totals, get_recent, save_analysis
from gemini_service import ask_gemini, build_prompt, extract_json
from validators import clean_expenses

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)


@bp.route("/")
def home():
    return render_template("index.html")


@bp.route("/analyse", methods=["POST"])
def analyse():
    data = request.get_json(silent=True) or {}

    try:
        income = float(data.get("income", 0))
    except (TypeError, ValueError):
        income = 0

    if income <= 0 or income > MAX_AMOUNT:
        return jsonify(
            success=False,
            error="Enter a monthly income between 1 and 1,00,00,000.",
        ), 400

    expenses, error = clean_expenses(data.get("expenses"))
    if error:
        return jsonify(success=False, error=error), 400

    goal = str(data.get("goal", "")).strip().lower()[:40]

    # Ask Gemini
    try:
        raw = ask_gemini(build_prompt(income, expenses, goal), json_mode=True)
    except RuntimeError as e:
        return jsonify(success=False, error=str(e)), 500
    except Exception as e:
        log.error("Gemini call failed: %s", e)
        return jsonify(
            success=False,
            error="Could not reach Gemini. Check your API key and internet, then try again.",
        ), 502

    # Parse the AI reply
    result = extract_json(raw)

    if not isinstance(result, dict) or not all(
        key in result for key in ("budget", "analysis", "suggestions")
    ):
        return jsonify(
            success=False,
            error="The AI reply was not in the expected format. Please try again.",
        ), 502

    # The summary numbers are calculated here, not by the AI
    total_spent = sum(expenses.values())
    saved = expenses.get("savings", expenses.get("Savings", 0))

    summary = {
        "income": income,
        "total_spent": total_spent,
        "left_over": income - total_spent,
        "savings_rate": round(saved / income * 100, 1),
    }

    save_analysis(income, goal, summary)

    return jsonify(
        success=True,
        budget=result["budget"],
        analysis=result["analysis"],
        suggestions=result["suggestions"],
        summary=summary,
    )


@bp.route("/history")
def history():
    return jsonify(history=get_recent(5))


@bp.route("/summary")
def monthly_summary():
    return jsonify(months=get_monthly_totals(6))


@bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}

    product_info = str(data.get("product_info", "")).strip()
    platform = str(data.get("platform", "Instagram")).strip()[:30]
    tone = str(data.get("tone", "friendly")).strip()[:30]

    if not product_info or len(product_info) > 2000:
        return jsonify(
            success=False,
            error="product_info must be between 1 and 2000 characters.",
        ), 400

    prompt = (
        f"Write a short {tone} post for {platform} promoting this finance "
        f"product or service:\n{product_info}\n\nKeep it under 100 words."
    )

    try:
        text = ask_gemini(prompt)
    except RuntimeError as e:
        return jsonify(success=False, error=str(e)), 500
    except Exception as e:
        log.error("Gemini call failed: %s", e)
        return jsonify(success=False, error="Could not reach Gemini."), 502

    return jsonify(success=True, content=text.strip())
