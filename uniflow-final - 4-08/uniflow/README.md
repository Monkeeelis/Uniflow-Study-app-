# UniFlow

A study planner: tasks, calendar, focus timers, flashcards and study insights.

An **HTML/CSS/JavaScript frontend** talking to a **Python (Flask) backend**. The
backend owns all of the app's logic and data; the browser renders what it is
given and dispatches actions back.

## Running it

Flask is the only dependency.

```
pip install -r requirements.txt
python -m uniflow
```

Then open <http://127.0.0.1:5000>.

Environment variables: `UNIFLOW_PORT` (default 5000), `UNIFLOW_HOST`,
`UNIFLOW_DEBUG` (`1` by default), `UNIFLOW_DATA_DIR` (default `./data`).

## How it fits together

```
uniflow/
  app.py              Flask routes: the page shell plus one JSON action endpoint
  state.py            Assembles the view model the browser renders from
  store.py            Loads/saves the single JSON document in data/
  services/           All of the logic, one module per feature area
    onboarding.py     Wizard + the profile settings that share its fields
    tasks.py          Create/edit/complete/filter/sort
    calendar.py       Events, categories, month/week/day layout maths
    focus.py          Pomodoro phases, timer, session log
    dashboard.py      Quote rotation, free-running study timer
    flashcards.py     Decks, cards, review and quiz sessions
    insights.py       Study-time heatmap and its metrics
    stats.py          Streak counting
    notifications.py  The navbar bell feed
  templates/
    index.html        The only page the server renders
  static/
    css/styles.css    The warm cream notebook theme
    js/
      main.js         Fetches state, renders the route, re-renders on change
      state.js        Holds the server's view model + the current route
      api.js          fetch() wrapper for the action endpoints
      timers.js       The two running clocks (see below)
      dom.js          h() element builder
      icons.js        Inline SVG icon set
      ui.js           Shared building blocks (modal, select, badges, tiles)
      format.js       Countdown/clock formatting
      views/          One module per page
```

### The state flow

`GET /api/state` returns one view model containing every computed value —
filtered task lists, the month grid, positioned calendar blocks, heatmap cells,
streaks, and so on.

`POST /api/<action>` runs a single service function, saves, and returns the
recomputed view model plus an optional toast. The browser replaces its copy and
re-renders. Because there is exactly one source of truth, no piece of app state
is ever calculated twice.

Every action lives in the `ACTIONS` table in `app.py` — that table is the API.

### The timers

The Focus countdown and the dashboard stopwatch tick in the browser, because
polling the server ten times a second would be wasteful. Python still decides
when a pomodoro phase is over, logs the session, raises the notification and
totals the stats. The browser reports its elapsed time on pause, skip and phase
completion, plus a heartbeat every five seconds so closing the tab doesn't lose
the current run.

### Data

Everything lives in `data/uniflow.json`, written atomically. Delete that file to
start over. It is gitignored.
