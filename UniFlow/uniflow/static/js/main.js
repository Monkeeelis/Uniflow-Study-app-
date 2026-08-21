// Entry point: fetch the view model, render the route, re-render on change.

import { clear } from "./dom.js";
import { act, currentRoute, load, navigate, state, subscribe, syncRouteFromUrl } from "./state.js";
import { startTicking } from "./timers.js";
import { calendarPage } from "./views/calendar.js";
import { dashboardPage } from "./views/dashboard.js";
import { focusPage } from "./views/focus.js";
import { pageShell } from "./views/nav.js";
import { notesPage } from "./views/notes.js";
import { onboardingPage } from "./views/onboarding.js";
import { profilePage } from "./views/profile.js";
import { quizPage } from "./views/quiz.js";
import { tasksPage } from "./views/tasks.js";

const PAGES = {
  "/dashboard": dashboardPage,
  "/tasks": tasksPage,
  "/calendar": calendarPage,
  "/focus": focusPage,
  "/quiz": quizPage,
  "/notes": notesPage,
  "/profile": profilePage,
};

const root = document.getElementById("app");

// Tracks the last rendered route so the page-enter animation only plays
// when the user actually switches tabs, not on every re-render triggered
// by an unrelated action (typing, toggling a setting, a timer tick, etc.).
let lastRoute = null;

function render() {
  const current = state();
  if (!current) return;
  root.classList.remove("app-loading");

  const route = currentRoute();
  const routeChanged = route !== lastRoute;
  lastRoute = route;

  // Until onboarding is finished every route shows the wizard, the same way the
  // Reflex build wrapped each page in a completed check.
  const view = current.onboarding.completed
    ? pageShell(current, (PAGES[route] || dashboardPage)(current), routeChanged)
    : onboardingPage(current);

  clear(root).append(view);
}

subscribe(render);

window.addEventListener("popstate", syncRouteFromUrl);

// Keep deep links working: /tasks in the address bar renders the tasks page.
navigate(window.location.pathname, { replace: true });

load()
  .then(startTicking)
  .catch((error) => {
    console.error(error);
    root.textContent = "Could not reach the UniFlow server. Start it with: python -m uniflow";
  });

// A couple of page-scoped single-key shortcuts. Ignored while typing
// anywhere (input/textarea/contenteditable) so they don't fire mid-sentence.
window.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const target = event.target;
  const typing =
    target instanceof HTMLElement &&
    (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
  if (typing) return;

  if (event.key === "n" && currentRoute() === "/tasks") {
    event.preventDefault();
    act("tasks/form", { open: true });
  } else if (event.key === "/" && currentRoute() === "/notes") {
    event.preventDefault();
    document.getElementById("notes-search")?.focus();
  }
});
