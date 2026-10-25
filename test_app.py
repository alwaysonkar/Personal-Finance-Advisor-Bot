"""Automated tests. Run with:  python -m unittest test_app.py -v

Gemini is replaced with a fixed reply, so no API key or internet is needed.
Every test uses its own temporary database, so finance.db is never touched.
"""
import json
import os
import tempfile
import unittest

import database

# Use a temporary database for the whole test run (set before the app is created)
database.DB_PATH = os.path.join(tempfile.mkdtemp(), "test_import.db")

import gemini_service  # noqa: E402
import routes  # noqa: E402
import validators  # noqa: E402
from app import create_app  # noqa: E402

FAKE_REPLY = json.dumps(
    {
        "budget": [{"category": "rent", "amount": 15000}],
        "analysis": [{"category": "rent", "percent": 30.0, "status": "ok", "note": "fine"}],
        "suggestions": ["Cut dining by Rs 1500 and move it to your emergency fund."],
    }
)

GOOD_REQUEST = {
    "income": 50000,
    "expenses": {"rent": 15000, "food": 8000, "savings": 5000},
    "goal": "vacation",
}


class BaseTest(unittest.TestCase):
    def setUp(self):
        # fresh empty database for every test
        database.DB_PATH = os.path.join(tempfile.mkdtemp(), "test.db")
        database.init_db()

        self._original_ask = routes.ask_gemini
        routes.ask_gemini = lambda prompt, json_mode=False: FAKE_REPLY if json_mode else " Post text "

        self.client = create_app().test_client()

    def tearDown(self):
        routes.ask_gemini = self._original_ask


class TestRoutes(BaseTest):
    def test_home_page_loads(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_analyse_success(self):
        res = self.client.post("/analyse", json=GOOD_REQUEST)
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("budget", data)
        self.assertIn("analysis", data)
        self.assertIn("suggestions", data)

    def test_summary_numbers_are_calculated_by_app(self):
        data = self.client.post("/analyse", json=GOOD_REQUEST).get_json()
        summary = data["summary"]
        self.assertEqual(summary["total_spent"], 28000)
        self.assertEqual(summary["left_over"], 22000)
        self.assertEqual(summary["savings_rate"], 10.0)

    def test_income_zero_rejected(self):
        res = self.client.post("/analyse", json={"income": 0, "expenses": {"rent": 100}})
        self.assertEqual(res.status_code, 400)

    def test_income_too_large_rejected(self):
        res = self.client.post("/analyse", json={"income": 99999999999, "expenses": {"rent": 100}})
        self.assertEqual(res.status_code, 400)

    def test_expense_not_a_number_rejected(self):
        res = self.client.post("/analyse", json={"income": 1000, "expenses": {"rent": "abc"}})
        self.assertEqual(res.status_code, 400)
        self.assertIn("rent", res.get_json()["error"])

    def test_no_expenses_rejected(self):
        res = self.client.post("/analyse", json={"income": 1000, "expenses": {"rent": 0}})
        self.assertEqual(res.status_code, 400)

    def test_missing_api_key_gives_500(self):
        def no_key(prompt, json_mode=False):
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

        routes.ask_gemini = no_key
        res = self.client.post("/analyse", json=GOOD_REQUEST)
        self.assertEqual(res.status_code, 500)

    def test_gemini_failure_gives_502(self):
        def broken(prompt, json_mode=False):
            raise ConnectionError("network down")

        routes.ask_gemini = broken
        res = self.client.post("/analyse", json=GOOD_REQUEST)
        self.assertEqual(res.status_code, 502)

    def test_bad_ai_reply_gives_502(self):
        routes.ask_gemini = lambda prompt, json_mode=False: "this is not json"
        res = self.client.post("/analyse", json=GOOD_REQUEST)
        self.assertEqual(res.status_code, 502)

    def test_history_returns_saved_analysis(self):
        self.client.post("/analyse", json=GOOD_REQUEST)
        history = self.client.get("/history").get_json()["history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["income"], 50000)
        self.assertEqual(history[0]["goal"], "vacation")

    def test_failed_analysis_is_not_saved(self):
        routes.ask_gemini = lambda prompt, json_mode=False: "not json"
        self.client.post("/analyse", json=GOOD_REQUEST)
        self.assertEqual(self.client.get("/history").get_json()["history"], [])

    def test_monthly_summary(self):
        self.client.post("/analyse", json=GOOD_REQUEST)
        months = self.client.get("/summary").get_json()["months"]
        self.assertEqual(len(months), 1)
        self.assertEqual(months[0]["income"], 50000)
        self.assertEqual(months[0]["expense"], 28000)
        self.assertEqual(months[0]["net_savings"], 22000)

    def test_generate_success(self):
        res = self.client.post("/generate", json={"product_info": "A monthly SIP plan"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["content"], "Post text")

    def test_generate_needs_product_info(self):
        self.assertEqual(self.client.post("/generate", json={}).status_code, 400)


class TestHelpers(unittest.TestCase):
    def test_extract_json_plain(self):
        self.assertEqual(gemini_service.extract_json('{"a": 1}'), {"a": 1})

    def test_extract_json_in_markdown_fence(self):
        self.assertEqual(gemini_service.extract_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_extract_json_with_extra_text(self):
        self.assertEqual(gemini_service.extract_json('Here you go: {"a": 1} Hope it helps'), {"a": 1})

    def test_extract_json_garbage_returns_none(self):
        self.assertIsNone(gemini_service.extract_json("no json here"))

    def test_prompt_contains_income_and_guideline(self):
        prompt = gemini_service.build_prompt(50000, {"rent": 15000}, "vacation")
        self.assertIn("Rs 50,000", prompt)
        self.assertIn("at most 30% of income", prompt)

    def test_clean_expenses_removes_symbols_and_zero_values(self):
        expenses, error = validators.clean_expenses({"rent!!": 100, "food": 0})
        self.assertIsNone(error)
        self.assertEqual(expenses, {"rent": 100.0})


if __name__ == "__main__":
    unittest.main()
