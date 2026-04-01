# AI Viva (Flask Prototype)

AI Viva is a polished, frontend-first Flask web app for university oral-assessment practice with mock AI behavior.

## Features
- Landing page + About + Help
- Student flow: dashboard, setup, interactive session, results, history, analytics, reflection
- Faculty flow: dashboard, cohort analytics, rubric review
- Mock question bank, scoring, and feedback (no real AI or external APIs)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install flask
python app.py
```
Open: `http://127.0.0.1:5000`

## Project structure
- `app.py` Flask routes and mock logic
- `templates/` Jinja2 pages
- `static/css/style.css` design system
- `static/js/` interaction and charts
- `data/` question bank and mock datasets

## Notes
This prototype uses local in-memory/session behavior and JSON mock files for demo reliability.
