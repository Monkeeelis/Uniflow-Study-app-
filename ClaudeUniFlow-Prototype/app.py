from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, date, timedelta
import calendar as calendar_module

app = Flask(__name__)
app.secret_key = "uniflow-secret-key-change-this"

FLASHCARD_DECK = [
    {"front": "What is the main purpose of active recall?", "back": "To strengthen memory by retrieving information from your own mind."},
    {"front": "What does a Pomodoro cycle usually last?", "back": "25 minutes of focused work, followed by a short break."},
    {"front": "Why should you review your notes regularly?", "back": "It improves long-term retention and helps you spot gaps earlier."},
]


def get_user():
    return {
        "name": session.get("name", ""),
        "grade": session.get("grade", ""),
        "streak": session.get("streak", 0),
    }


def greeting():
    h = datetime.now().hour
    if h < 12:
        return "Good morning"
    if h < 17:
        return "Good afternoon"
    return "Good evening"


def get_tasks():
    if "tasks" not in session:
        session["tasks"] = []
    return session["tasks"]


def get_study_sessions():
    if "study_sessions" not in session:
        session["study_sessions"] = []
    return session["study_sessions"]


def get_flashcards():
    if "flashcards" not in session:
        session["flashcards"] = FLASHCARD_DECK.copy()
    return session["flashcards"]


def get_study_stats():
    sessions = get_study_sessions()
    today = date.today().isoformat()
    today_total = sum(item["duration"] for item in sessions if item["date"] == today)
    all_total = sum(item["duration"] for item in sessions)
    tasks = get_tasks()
    return {
        "today_mins": today_total,
        "today_sessions": len([item for item in sessions if item["date"] == today]),
        "all_mins": all_total,
        "all_sessions": len(sessions),
        "active_tasks": len([task for task in tasks if not task.get("done")]),
        "completed_tasks": len([task for task in tasks if task.get("done")]),
    }


def get_calendar_events():
    events = []
    for task in get_tasks():
        task_date = task.get("due_date")
        if task_date:
            try:
                event_date = date.fromisoformat(task_date)
            except ValueError:
                event_date = date.today()
            events.append({
                "date": event_date,
                "title": task["title"],
                "done": task.get("done", False),
            })
    return events


def get_calendar_context(view):
    now = datetime.now()
    today = now.date()
    view = view if view in {"day", "week", "month", "year"} else "month"

    if view == "day":
        dates = [today]
    elif view == "week":
        start = today - timedelta(days=today.weekday())
        dates = [start + timedelta(days=i) for i in range(7)]
    elif view == "year":
        dates = [date(today.year, m, 1) for m in range(1, 13)]
    else:
        month_days = calendar_module.monthrange(today.year, today.month)[1]
        dates = [date(today.year, today.month, d) for d in range(1, month_days + 1)]

    event_map = {}
    for event in get_calendar_events():
        event_map.setdefault(event["date"], []).append(event)

    return {
        "mode": view,
        "today": today,
        "now": now,
        "dates": dates,
        "events": event_map,
    }


@app.route("/")
def index():
    if session.get("name"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        grade = (request.form.get("grade") or "").strip()
        if not name:
            return render_template("login.html", error="Please enter your name.")

        session["name"] = name
        session["grade"] = grade
        session["streak"] = max(int(session.get("streak", 0)), 1)
        session["tasks"] = []
        session["study_sessions"] = []
        session.modified = True
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    user = get_user()
    today = date.today().strftime("%A, %d %B %Y")
    stats = get_study_stats()
    return render_template("dashboard.html", user=user, greeting=greeting(), today=today, stats=stats, tasks=get_tasks())


@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":
        title = (request.form.get("task_title") or "").strip()
        due_date = request.form.get("task_due_date") or date.today().isoformat()
        if title:
            get_tasks().append({"title": title, "done": False, "due_date": due_date})
            session.modified = True
        return redirect(url_for("tasks"))

    return render_template("tasks.html", user=get_user(), tasks=get_tasks(), stats=get_study_stats(), today=date.today().isoformat())


@app.route("/tasks/<int:task_index>/toggle", methods=["POST"])
def toggle_task(task_index):
    tasks = get_tasks()
    if 0 <= task_index < len(tasks):
        tasks[task_index]["done"] = not tasks[task_index].get("done", False)
        session.modified = True
    return redirect(url_for("tasks"))


@app.route("/calendar")
def calendar():
    view = request.args.get("view", "month")
    context = get_calendar_context(view)
    return render_template("calendar.html", user=get_user(), context=context)


@app.route("/focus")
def focus():
    return render_template("focus.html", user=get_user(), focus_goal="Pomodoro focus block")


@app.route("/flashcards")
def flashcards():
    return render_template("flashcards.html", user=get_user(), flashcards=get_flashcards())


@app.route("/quiz")
def quiz():
    return redirect(url_for("flashcards"))


@app.route("/profile")
def profile():
    return render_template("profile.html", user=get_user(), stats=get_study_stats())


@app.route("/api/study-sessions", methods=["GET", "POST"])
def study_sessions_api():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        duration = int(payload.get("duration_mins", 0) or 0)
        if duration > 0:
            get_study_sessions().append({"date": date.today().isoformat(), "duration": duration})
            session.modified = True
    return jsonify(get_study_stats())


if __name__ == "__main__":
    app.run(debug=True)
