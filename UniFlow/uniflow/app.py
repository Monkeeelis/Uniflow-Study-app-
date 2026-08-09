"""Flask application: serves the page shell and the JSON action API.

Every action follows the same shape — load the document, run one service
function, save, and hand the freshly computed view model back to the browser.
The browser never computes app state itself, it just renders what it is given.
"""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Any, Callable

from flask import Flask, g, jsonify, render_template, request

from uniflow import store
from uniflow.services import (
    calendar,
    dashboard,
    flashcards,
    focus,
    insights,
    notes,
    notifications,
    onboarding,
    system,
    tasks,
)
from uniflow.services.common import text
from uniflow.state import build_state

PAGE_ROUTES = (
    "/",
    "/dashboard",
    "/tasks",
    "/calendar",
    "/focus",
    "/quiz",
    "/notes",
    "/profile",
)

Action = Callable[[dict[str, Any], dict[str, Any]], Any]

# endpoint name -> service call. Handlers may return a toast dict or None.
ACTIONS: dict[str, Action] = {
    "onboarding/update": onboarding.update,
    "onboarding/step": onboarding.set_step,
    "onboarding/subjects/add": onboarding.add_subject,
    "onboarding/subjects/remove": lambda data, p: onboarding.remove_subject(
        data, text(p, "name")
    ),
    "onboarding/notifications/toggle": lambda data, p: onboarding.toggle_notifications(
        data
    ),
    "settings/theme/toggle": lambda data, p: onboarding.toggle_theme(data),
    "settings/theme/set": onboarding.set_theme,
    "settings/colorblind/set": onboarding.set_colorblind_mode,
    "onboarding/finish": lambda data, p: onboarding.finish(data, g.device_id),
    "tasks/save": tasks.submit,
    "tasks/delete": lambda data, p: tasks.delete(data, text(p, "task_id")),
    "tasks/toggle": lambda data, p: tasks.toggle_complete(data, text(p, "task_id")),
    "tasks/view": tasks.set_view,
    "tasks/show-completed/toggle": lambda data, p: tasks.toggle_show_completed(data),
    "tasks/form": tasks.set_form,
    "tasks/feedback/clear": lambda data, p: tasks.clear_feedback(data),
    "calendar/view": calendar.set_view,
    "calendar/navigate": calendar.navigate,
    "calendar/event-form": calendar.set_event_form,
    "calendar/events/save": calendar.submit_event,
    "calendar/events/delete": lambda data, p: calendar.delete_event(
        data, text(p, "event_id")
    ),
    "calendar/event-detail": calendar.set_event_detail,
    "calendar/categories/form": lambda data, p: calendar.toggle_category_form(data),
    "calendar/categories/add": calendar.add_category,
    "calendar/categories/remove": lambda data, p: calendar.remove_category(
        data, text(p, "name")
    ),
    "calendar/feedback/clear": lambda data, p: calendar.clear_feedback(data),
    "focus/mode": focus.set_mode,
    "focus/settings": focus.set_settings,
    "focus/start": lambda data, p: focus.start(data),
    "focus/pause": focus.pause,
    "focus/reset": lambda data, p: focus.reset(data),
    "focus/skip": focus.skip,
    "focus/complete": focus.complete,
    "focus/sync": focus.sync,
    "dashboard/quote/next": lambda data, p: dashboard.next_quote(data),
    "dashboard/timer/start": lambda data, p: dashboard.start_timer(data),
    "dashboard/timer/pause": dashboard.pause_timer,
    "dashboard/timer/save": dashboard.stop_and_save,
    "dashboard/timer/reset": lambda data, p: dashboard.reset_timer(data),
    "dashboard/timer/sync": dashboard.sync_timer,
    "dashboard/sessions/delete": lambda data, p: dashboard.delete_session(
        data, text(p, "session_id")
    ),
    "flashcards/deck-form": lambda data, p: flashcards.toggle_deck_form(data),
    "flashcards/decks/create": flashcards.create_deck,
    "flashcards/decks/delete": lambda data, p: flashcards.delete_deck(
        data, text(p, "deck_id")
    ),
    "flashcards/decks/select": flashcards.select_deck,
    "flashcards/card-form": flashcards.set_card_form,
    "flashcards/cards/save": flashcards.submit_card,
    "flashcards/cards/delete": lambda data, p: flashcards.delete_card(
        data, text(p, "card_id")
    ),
    "flashcards/review/start": flashcards.start_review,
    "flashcards/review/flip": lambda data, p: flashcards.flip_card(data),
    "flashcards/review/mark": flashcards.mark_result,
    "flashcards/review/answer": flashcards.submit_answer,
    "flashcards/review/next": lambda data, p: flashcards.next_card(data),
    "flashcards/review/exit": lambda data, p: flashcards.exit_review(data),
    "flashcards/feedback/clear": lambda data, p: flashcards.clear_feedback(data),
    "notes/select": notes.select_note,
    "notes/new": lambda data, p: notes.new_note(data),
    "notes/save": notes.submit,
    "notes/delete": lambda data, p: notes.delete(data, text(p, "note_id")),
    "notes/pin": lambda data, p: notes.toggle_pin(data, text(p, "note_id")),
    "notes/folder/toggle": notes.toggle_folder,
    "notes/font": notes.set_font,
    "notes/view": notes.set_view,
    "notes/feedback/clear": lambda data, p: notes.clear_feedback(data),
    "system/reset": lambda data, p: system.reset(data),
    "notifications/panel/toggle": lambda data, p: notifications.toggle_panel(data),
    "notifications/read-all": lambda data, p: notifications.mark_all_read(data),
    "notifications/clear": lambda data, p: notifications.clear_all(data),
    "notifications/dismiss": lambda data, p: notifications.dismiss(
        data, text(p, "notification_id")
    ),
    "insights/range": insights.set_range,
}

# Heartbeats fired every few seconds by a running timer: persist and get out of
# the way rather than recomputing and shipping the whole view model.
QUIET_ACTIONS = frozenset({"focus/sync", "dashboard/timer/sync"})

# The server is threaded, so read-modify-write has to be serialised or a timer
# heartbeat could land between another request's load and save and undo it.
_write_lock = threading.Lock()

# Identifies this browser so a copied/shared data file doesn't carry someone
# else's finished onboarding onto a machine that never went through it.
DEVICE_COOKIE = "uniflow_device"


def create_app() -> Flask:
    app = Flask(__name__, template_folder=".")
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["JSON_SORT_KEYS"] = False

    for route in PAGE_ROUTES:
        app.add_url_rule(
            route,
            endpoint=f"page_{route.strip('/') or 'index'}",
            view_func=_page,
        )

    app.add_url_rule("/api/state", view_func=_state, methods=["GET"])
    app.add_url_rule(
        "/api/<path:action>", view_func=_action, methods=["POST"]
    )

    app.before_request(_load_device_id)
    app.after_request(_persist_device_id)
    return app


def _load_device_id() -> None:
    g.device_id = request.cookies.get(DEVICE_COOKIE, "")
    g.new_device_id = not g.device_id
    if g.new_device_id:
        g.device_id = uuid.uuid4().hex


def _persist_device_id(response):
    if getattr(g, "new_device_id", False):
        response.set_cookie(
            DEVICE_COOKIE, g.device_id, max_age=60 * 60 * 24 * 365 * 5, samesite="Lax"
        )
    return response


def _page() -> str:
    return render_template("index.html")


def _state():
    return jsonify({"state": build_state(store.load(), g.device_id), "toast": None})


def _action(action: str):
    handler = ACTIONS.get(action)
    if handler is None:
        return jsonify({"error": f"Unknown action: {action}"}), 404

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}

    with _write_lock:
        data = store.load()
        try:
            result = handler(data, payload)
        except Exception:
            # An unexpected bug in one handler shouldn't corrupt the saved
            # document or crash the request — reload what was on disk, tell
            # the user, and let them keep using the rest of the app.
            logging.exception(f"Action '{action}' failed")
            fresh = store.load()
            return jsonify(
                {
                    "state": build_state(fresh, g.device_id),
                    "toast": {
                        "message": "Something went wrong. Please try again.",
                        "kind": "warning",
                    },
                }
            )
        store.save(data)

    if action in QUIET_ACTIONS:
        return jsonify({"ok": True})
    toast = result if isinstance(result, dict) else None
    return jsonify({"state": build_state(data, g.device_id), "toast": toast})


app = create_app()
