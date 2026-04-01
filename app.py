from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "ai-viva-demo-secret"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename: str) -> Any:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


QUESTION_BANK = load_json("question_bank.json")
IDEAL_ANSWERS = load_json("ideal_answers.json")
MOCK_HISTORY = load_json("mock_sessions.json")
FACULTY_DATA = load_json("faculty_data.json")
USERS = load_json("users.json")

DISCIPLINES = ["Medicine / Orthopaedics", "Law", "Languages", "Humanities"]
TOPICS = list(QUESTION_BANK["Medicine / Orthopaedics"].keys())
MODES = ["core concepts", "keywords", "application", "analysis/evaluation"]


# ---------- helpers ----------
def get_logged_in_user() -> dict[str, Any] | None:
    email = session.get("user_email")
    if not email:
        return None
    return USERS.get(email)


def login_required():
    if not get_logged_in_user():
        flash("Please sign in to access this page.", "warning")
        return redirect(url_for("login"))
    return None


def analyze_answer(answer: str, keywords: list[str], ideal_answer: str) -> dict[str, Any]:
    text = answer.lower().strip()
    token_hits = [k for k in keywords if k.lower() in text]
    keyword_coverage = round((len(token_hits) / max(1, len(keywords))) * 100)

    conceptual_accuracy = min(100, 55 + keyword_coverage // 2 + (10 if len(text) > 120 else 0))
    reasoning_quality = min(100, 50 + (15 if any(w in text for w in ["because", "therefore", "however", "so that"]) else 0) + keyword_coverage // 3)
    clarity = min(100, 50 + min(30, len(text.split()) // 2))
    confidence = min(100, 45 + (20 if len(text) > 100 else 5) + random.randint(0, 20))
    overall = round((conceptual_accuracy + reasoning_quality + clarity + confidence) / 4)

    viva_coach = [
        "Open with a 1-line definition before diving into management.",
        "Use a three-step structure: diagnosis, reasoning, treatment plan.",
        "State one risk and one mitigation to show balanced judgement.",
    ]

    strengths, improvements = [], []
    if keyword_coverage >= 60:
        strengths.append("Good keyword coverage tied to discipline vocabulary.")
    else:
        improvements.append("Include more high-yield clinical keywords.")

    if reasoning_quality >= 70:
        strengths.append("Reasoning chain is coherent and defensible.")
    else:
        improvements.append("Use explicit logic words (because/therefore/however).")

    if clarity >= 70:
        strengths.append("Expression is concise and easy to follow.")
    else:
        improvements.append("Break your response into short verbal sections.")

    if not strengths:
        strengths.append("You stayed on-topic and attempted the core concept.")

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
        "coach_tip": random.choice(viva_coach),
    }


def get_current_session() -> dict[str, Any]:
    return session.get("current_session", {})


@app.context_processor
def inject_globals():
    return {
        "app_name": "AI Viva",
        "current_user": get_logged_in_user(),
    }


# ---------- public pages ----------
@app.route("/")
def home():
    return render_template("index.html", disciplines=DISCIPLINES)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


# ---------- auth ----------
@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = USERS.get(email)
        if not user or user.get("password") != password:
            flash("Invalid email/password for this demo account.", "danger")
            return render_template("auth/login.html")
        session["user_email"] = email
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("student_dashboard"))
    return render_template("auth/login.html")


@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email or email in USERS:
            flash("Email is invalid or already exists.", "danger")
            return render_template("auth/register.html")
        USERS[email] = {
            "name": request.form.get("name", "Student"),
            "password": request.form.get("password", "demo123"),
            "role": request.form.get("role", "student"),
            "institution": request.form.get("institution", "University Demo Campus"),
            "program": request.form.get("program", "MBBS"),
            "year": request.form.get("year", "Year 4"),
            "bio": "Focused on improving viva confidence and structured clinical reasoning.",
        }
        save_json("users.json", USERS)
        session["user_email"] = email
        flash("Registration successful. Your demo profile is ready.", "success")
        return redirect(url_for("profile"))
    return render_template("auth/register.html")


@app.route("/auth/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    guard = login_required()
    if guard:
        return guard
    user = get_logged_in_user()
    if request.method == "POST":
        for key in ["name", "institution", "program", "year", "bio"]:
            user[key] = request.form.get(key, user.get(key, ""))
        USERS[session["user_email"]] = user
        save_json("users.json", USERS)
        flash("Profile updated.", "success")
    return render_template("profile.html", user=user)


# ---------- student ----------
@app.route("/student/dashboard")
def student_dashboard():
    guard = login_required()
    if guard:
        return guard
    recent = sorted(MOCK_HISTORY, key=lambda x: x["date"], reverse=True)[:4]
    avg_score = round(sum(s["score"] for s in MOCK_HISTORY) / len(MOCK_HISTORY))
    return render_template("student/dashboard.html", recent=recent, avg_score=avg_score, topics=TOPICS)


@app.route("/student/setup", methods=["GET", "POST"])
def student_setup():
    guard = login_required()
    if guard:
        return guard

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
    guard = login_required()
    if guard:
        return guard
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
    current["answers"].append(
        {
            "question": question_obj["question"],
            "answer": answer,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    session["current_session"] = current
    return jsonify({"ok": True, "feedback": feedback})


@app.route("/student/results")
def student_results():
    guard = login_required()
    if guard:
        return guard

    current = get_current_session()
    if not current or not current.get("answers"):
        return redirect(url_for("student_setup"))

    answers = current["answers"]
    metrics = ["overall_score", "keyword_coverage", "conceptual_accuracy", "reasoning_quality", "clarity", "confidence"]
    summary = {m: round(sum(a["feedback"][m] for a in answers) / len(answers)) for m in metrics}

    recap = [
        {
            "label": f"Q{i + 1} answered",
            "detail": a["question"][:80] + "...",
            "time": (datetime.utcnow() - timedelta(minutes=(len(answers) - i))).strftime("%H:%M"),
        }
        for i, a in enumerate(answers)
    ]

    MOCK_HISTORY.insert(
        0,
        {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "topic": current["topic"],
            "mode": current["mode"],
            "score": summary["overall_score"],
            "duration": current["estimated_duration"],
            "status": "Completed",
        },
    )
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
    guard = login_required()
    if guard:
        return guard
    return render_template("student/history.html", sessions=MOCK_HISTORY)


@app.route("/student/analytics")
def student_analytics():
    guard = login_required()
    if guard:
        return guard
    return render_template("student/analytics.html", sessions=MOCK_HISTORY)


@app.route("/student/reflection", methods=["GET", "POST"])
def student_reflection():
    guard = login_required()
    if guard:
        return guard
    saved = False
    if request.method == "POST":
        session["reflection"] = request.form.to_dict()
        saved = True
    return render_template("student/reflection.html", saved=saved)


@app.route("/student/coach", methods=["GET", "POST"])
def student_coach():
    guard = login_required()
    if guard:
        return guard

    reply = None
    if request.method == "POST":
        prompt = request.form.get("prompt", "")
        reply = {
            "input": prompt,
            "response": "Mock LLM Coach: Great attempt. Try a structured 3-part response (definition → differential → management) and include one evidence-based keyword.",
        }
    return render_template("student/coach.html", reply=reply)


# ---------- faculty ----------
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
