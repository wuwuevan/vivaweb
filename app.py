from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "ai-viva-demo-secret"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename: str) -> Any:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


QUESTION_BANK = load_json("question_bank.json")
IDEAL_ANSWERS = load_json("ideal_answers.json")
MOCK_HISTORY = load_json("mock_sessions.json")
FACULTY_DATA = load_json("faculty_data.json")


DISCIPLINES = [
    "Medicine / Orthopaedics",
    "Law",
    "Languages",
    "Humanities",
]
TOPICS = list(QUESTION_BANK["Medicine / Orthopaedics"].keys())
MODES = ["core concepts", "keywords", "application", "analysis/evaluation"]


def analyze_answer(answer: str, keywords: list[str], ideal_answer: str) -> dict[str, Any]:
    text = answer.lower().strip()
    token_hits = [k for k in keywords if k.lower() in text]
    keyword_coverage = round((len(token_hits) / max(1, len(keywords))) * 100)

    conceptual_accuracy = min(100, 55 + keyword_coverage // 2 + (10 if len(text) > 120 else 0))
    reasoning_quality = min(100, 50 + (15 if any(w in text for w in ["because", "therefore", "however"]) else 0) + keyword_coverage // 3)
    clarity = min(100, 50 + min(30, len(text.split()) // 2))
    confidence = min(100, 45 + (20 if len(text) > 100 else 5) + random.randint(0, 20))
    overall = round((conceptual_accuracy + reasoning_quality + clarity + confidence) / 4)

    strengths = []
    improvements = []
    if keyword_coverage >= 60:
        strengths.append("Good keyword coverage tied to the domain vocabulary.")
    else:
        improvements.append("Include more clinical keywords to improve precision.")

    if reasoning_quality >= 70:
        strengths.append("Reasoning structure is clear and defensible.")
    else:
        improvements.append("Add explicit clinical reasoning (e.g., why one option is preferred).")

    if clarity >= 70:
        strengths.append("Expression is coherent and easy to follow.")
    else:
        improvements.append("Use shorter, well-structured points to improve clarity.")

    if not strengths:
        strengths.append("You maintained a focused response and attempted the core concept.")

    return {
        "overall_score": overall,
        "keyword_coverage": keyword_coverage,
        "conceptual_accuracy": conceptual_accuracy,
        "reasoning_quality": reasoning_quality,
        "clarity": clarity,
        "confidence": confidence,
        "keyword_hits": token_hits,
        "strengths": strengths,
        "improvements": improvements,
        "ideal_answer": ideal_answer,
    }


def get_current_session() -> dict[str, Any]:
    return session.get("current_session", {})


@app.context_processor
def inject_globals():
    return {"app_name": "AI Viva"}


@app.route("/")
def home():
    return render_template("index.html", disciplines=DISCIPLINES)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/student/dashboard")
def student_dashboard():
    recent = sorted(MOCK_HISTORY, key=lambda x: x["date"], reverse=True)[:4]
    avg_score = round(sum(s["score"] for s in MOCK_HISTORY) / len(MOCK_HISTORY))
    return render_template("student/dashboard.html", recent=recent, avg_score=avg_score, topics=TOPICS)


@app.route("/student/setup", methods=["GET", "POST"])
def student_setup():
    if request.method == "POST":
        topic = request.form.get("topic", TOPICS[0])
        mode = request.form.get("mode", MODES[0])
        num_questions = int(request.form.get("num_questions", 4))
        selected_questions = QUESTION_BANK["Medicine / Orthopaedics"][topic][:num_questions]
        current = {
            "discipline": request.form.get("discipline", "Medicine / Orthopaedics"),
            "topic": topic,
            "difficulty": request.form.get("difficulty", "Intermediate"),
            "mode": mode,
            "num_questions": num_questions,
            "timer_mode": request.form.get("timer_mode") == "on",
            "estimated_duration": request.form.get("estimated_duration", "12 minutes"),
            "questions": selected_questions,
            "answers": [],
            "started_at": datetime.utcnow().isoformat(),
        }
        session["current_session"] = current
        return redirect(url_for("student_session"))

    return render_template("student/setup.html", disciplines=DISCIPLINES, topics=TOPICS, modes=MODES)


@app.route("/student/session")
def student_session():
    current = get_current_session()
    if not current:
        return redirect(url_for("student_setup"))
    return render_template("student/session.html", current=current)


@app.route("/api/session/answer", methods=["POST"])
def submit_answer():
    payload = request.get_json(force=True)
    current = get_current_session()
    idx = int(payload.get("question_index", 0))
    answer = payload.get("answer", "")
    topic = current.get("topic", TOPICS[0])

    question_obj = current["questions"][idx]
    keywords = question_obj["keywords"]
    ideal = IDEAL_ANSWERS.get(topic, {}).get(question_obj["id"], "A structured, evidence-based answer discussing diagnosis and management.")

    feedback = analyze_answer(answer, keywords, ideal)
    item = {
        "question": question_obj["question"],
        "answer": answer,
        "feedback": feedback,
        "timestamp": datetime.utcnow().isoformat(),
    }
    current["answers"].append(item)
    session["current_session"] = current
    return jsonify({"ok": True, "feedback": feedback})


@app.route("/student/results")
def student_results():
    current = get_current_session()
    if not current or not current.get("answers"):
        return redirect(url_for("student_setup"))

    answers = current["answers"]
    metrics = [
        "overall_score",
        "keyword_coverage",
        "conceptual_accuracy",
        "reasoning_quality",
        "clarity",
        "confidence",
    ]
    summary = {m: round(sum(a["feedback"][m] for a in answers) / len(answers)) for m in metrics}

    recap = [
        {
            "label": f"Q{i+1} answered",
            "detail": a["question"][:80] + "...",
            "time": (datetime.utcnow() - timedelta(minutes=(len(answers)-i))).strftime("%H:%M"),
        }
        for i, a in enumerate(answers)
    ]

    mock_record = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "topic": current["topic"],
        "mode": current["mode"],
        "score": summary["overall_score"],
        "duration": current["estimated_duration"],
        "status": "Completed",
    }
    MOCK_HISTORY.insert(0, mock_record)

    return render_template(
        "student/results.html",
        current=current,
        answers=answers,
        summary=summary,
        recap=recap,
        recommended_next="Sports medicine" if current["topic"] != "Sports medicine" else "Spine problems",
    )


@app.route("/student/history")
def student_history():
    return render_template("student/history.html", sessions=MOCK_HISTORY)


@app.route("/student/analytics")
def student_analytics():
    return render_template("student/analytics.html", sessions=MOCK_HISTORY)


@app.route("/student/reflection", methods=["GET", "POST"])
def student_reflection():
    saved = False
    if request.method == "POST":
        session["reflection"] = request.form.to_dict()
        saved = True
    return render_template("student/reflection.html", saved=saved)


@app.route("/faculty/dashboard")
def faculty_dashboard():
    return render_template("faculty/dashboard.html", data=FACULTY_DATA)


@app.route("/faculty/analytics")
def faculty_analytics():
    return render_template("faculty/analytics.html", data=FACULTY_DATA)


@app.route("/faculty/rubric")
def faculty_rubric():
    sample = get_current_session().get("answers", [])
    return render_template("faculty/rubric.html", data=FACULTY_DATA, sample=sample)


if __name__ == "__main__":
    app.run(debug=True)
