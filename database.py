"""SQLite storage for past analyses."""
import json
import logging
import sqlite3
from datetime import datetime

from config import DB_PATH

log = logging.getLogger(__name__)


def init_db():
    """Create the analyses table if it does not exist yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            income REAL NOT NULL,
            goal TEXT,
            summary TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_analysis(income, goal, summary):
    """Save one finished analysis. A failure here must not break the response."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO analyses (created_at, income, goal, summary)
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                income,
                goal,
                json.dumps(summary),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.error("Could not save analysis: %s", e)


def get_recent(limit=5):
    """Return the latest analyses, newest first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT created_at, income, goal, summary
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    return [
        {
            "created_at": row["created_at"],
            "income": row["income"],
            "goal": row["goal"],
            "summary": json.loads(row["summary"]),
        }
        for row in rows
    ]


def get_monthly_totals(limit=6):
    """Add up income and spending per month, newest month first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT created_at, income, summary
        FROM analyses
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()

    months = {}
    for row in rows:
        month_key = row["created_at"][:7]
        data = json.loads(row["summary"])

        if month_key not in months:
            months[month_key] = {"income": 0, "expense": 0}

        months[month_key]["income"] += data["income"]
        months[month_key]["expense"] += data["total_spent"]

    result = []
    for key in sorted(months.keys(), reverse=True)[:limit]:
        month = months[key]
        net = month["income"] - month["expense"]
        rate = round(net / month["income"] * 100, 1) if month["income"] else 0
        label = datetime.strptime(key, "%Y-%m").strftime("%B %Y")

        result.append(
            {
                "month": label,
                "income": month["income"],
                "expense": month["expense"],
                "net_savings": net,
                "savings_rate": rate,
            }
        )

    return result
