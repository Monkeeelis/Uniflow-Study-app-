<div align="center">

<img src="UniFlow/uniflow/static/img/logo-mark.png" alt="UniFlow logo" width="96" />

# UniFlow

**An all-in-one study workspace — tasks, calendar, focus timers, notes, flashcards and study insights, in one tab.**

[**🌐 Live app → uniflow.pythonanywhere.com**](https://uniflow.pythonanywhere.com/)

[![Live demo](https://img.shields.io/badge/live-uniflow.pythonanywhere.com-0d9488?style=flat-square&logo=pythonanywhere&logoColor=white)](https://uniflow.pythonanywhere.com/)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Frontend](https://img.shields.io/badge/frontend-vanilla%20JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](UniFlow/README.md#tech-stack)
[![Build step](https://img.shields.io/badge/build%20step-none-success?style=flat-square)](#quick-start)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What it is

UniFlow is a study planner for students who are tired of juggling a to-do app, a
calendar, a Pomodoro timer, a notes app and a flashcard app that all know
nothing about each other. Everything shares one pool of data, so the pieces
reinforce each other — a task with a due date lands on the calendar, focus time
feeds your streak and heatmap, and a note becomes a flashcard deck in one click.

**No account, no sign-up, no database.** Open the page and start working.

| | |
| --- | --- |
| 📊 **Dashboard** | Study stopwatch, daily and all-time totals, streak, motivational quotes |
| ✅ **Tasks** | Subjects, due dates, priorities, filtering and sorting |
| 📅 **Calendar** | Month / week / day views, colour-coded categories, tasks shown inline |
| ⏱️ **Focus** | Pomodoro and plain countdown, ambient noise and rain, chime, session logging |
| 🧠 **Quiz** | Flashcard decks, flip-and-mark review, typed-answer quiz mode |
| 📝 **Notes** | Rich text, folders by subject, search, pinning, note → deck generation |
| 📈 **Insights** | GitHub-style study heatmap, weekly goal tracking |
| 🎨 **Themes** | Five palettes, light/dark mode, and five colour-blind filters |

---

## Quick start

```bash
git clone https://github.com/Monkeeelis/Uniflow-Study-app-.git
```

```bash
cd "Uniflow-Study-app-/UniFlow" && pip install -r requirements.txt
```

```bash
python -m uniflow
```

Then open **<http://127.0.0.1:5000>**. Flask is the only dependency, and there is
no build step.

---

## Repository layout

| Path | What it is |
| --- | --- |
| [`UniFlow/`](UniFlow/) | **The current app** — HTML/CSS/JS frontend with a Python (Flask) backend |
| [`UniFlow/README.md`](UniFlow/README.md) | **Full documentation** — features, configuration, architecture, API, deployment |
| [`LICENSE`](LICENSE) | MIT License |

---

## Documentation

Everything else — configuration, the state-flow architecture, the action API,
deployment to PythonAnywhere and troubleshooting — lives in
**[`UniFlow/README.md`](UniFlow/README.md)**.

---

## License

Released under the **MIT License** — see [`LICENSE`](LICENSE).
Copyright © 2026 Monkeeelis.

<div align="center">

**[Try UniFlow →](https://uniflow.pythonanywhere.com/)**

</div>
