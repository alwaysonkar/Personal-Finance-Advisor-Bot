"""Settings and constants shared by the whole app."""
import os

from dotenv import load_dotenv

load_dotenv()

# Gemini
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# SQLite file sits next to this file, in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")

# Largest amount we accept for income or any single expense (Rs)
MAX_AMOUNT = 10_000_000

# Rules of thumb that are passed to the AI inside the prompt
CATEGORY_TIPS = {
    "rent": "should be at most 30% of income",
    "food": "should stay under 15% of income",
    "transport": "should stay within 10% of income",
    "entertainment": "should be around 5-8% of income",
    "savings": "should be at least 20% of income",
}

GOAL_DESCRIPTIONS = {
    "emergency fund": "Build an emergency fund worth 3-6 months of expenses. Focus on cutting non-essentials and saving steadily.",
    "vacation": "Save up for a trip. Focus on short-term saving and trimming discretionary spending like dining and entertainment.",
    "gadget purchase": "Save for a big gadget purchase (phone, laptop etc). Suggest a monthly target and what to cut to reach it.",
    "investment": "Free up money to start investing. Focus on raising the savings rate and keeping fixed costs low.",
}
