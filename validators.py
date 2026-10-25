"""Input checks for the data sent from the browser."""
import re

from config import MAX_AMOUNT


def clean_expenses(raw):
    """Return (expenses, None) if valid, or (None, error_message) if not."""
    if not isinstance(raw, dict):
        return None, "Expenses are missing."

    expenses = {}

    for name, value in raw.items():
        name = re.sub(r"[^A-Za-z ]", "", str(name)).strip()[:30]

        if not name:
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            return None, f"Amount for {name} is not a number."

        if value < 0 or value > MAX_AMOUNT:
            return None, f"Amount for {name} is out of range."

        if value > 0:
            expenses[name] = value

    if not expenses:
        return None, "Enter at least one expense."

    return expenses, None
