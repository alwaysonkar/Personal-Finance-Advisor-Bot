# Personal Finance Advisor Bot

A Flask web app where you enter your monthly income, expenses and a savings goal. It sends them to Google Gemini and shows a suggested budget, which categories are overspent, and a few ways to save. Made for the SkillWallet Personal Finance Advisor Bot project.

Built with Python, Flask, Gemini API, SQLite, HTML/CSS/JavaScript.

## Setup

```
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
NGROK_AUTHTOKEN=your_token_here
```

Get a Gemini API key from https://aistudio.google.com. `GEMINI_MODEL` is optional and defaults to `gemini-2.5-flash`. `NGROK_AUTHTOKEN` is only needed for a public link.

## Run

```
python app.py
```

Open http://127.0.0.1:5000

To get a public link with ngrok, add your authtoken to `.env` and run `python run_public.py`. The free link changes every restart.

## How it works

- The form sends income, expenses and goal to `/analyse` using fetch
- `build_prompt()` makes the prompt using `CATEGORY_TIPS` and `GOAL_DESCRIPTIONS`
- Gemini replies in JSON and `extract_json()` pulls it out
- `renderResults()` in `main.js` shows the budget, status and suggestions
- The summary numbers (spent, left over, savings rate) are calculated by the app, not by the AI

## Saved data

Each successful analysis is saved to a local SQLite file (`finance.db`), created automatically on first run. It powers two sections on the page:

- `/history` shows the last 5 analyses
- `/summary` shows monthly totals for the last 6 months

Only income, goal and the summary numbers are saved, not the individual expense amounts.

## Other routes

- `/generate` (POST) writes a short promotional post for a finance product. It is included because the project spec asks for it.

## Notes

- Keep your `.env` file private. It is listed in `.gitignore`.
- Suggestions come from an AI model and are for learning purposes, not professional financial advice.
