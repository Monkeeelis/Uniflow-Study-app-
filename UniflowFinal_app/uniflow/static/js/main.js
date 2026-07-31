// Entry point: fetch the view model, render the route, re-render on change.

import { clear } from "./dom.js";
import { currentRoute, load, navigate, state, subscribe, syncRouteFromUrl } from "./state.js";
import { startTicking } from "./timers.js";
import { calendarPage } from "./views/calendar.js";
import { dashboardPage } from "./views/dashboard.js";
import { focusPage } from "./views/focus.js";
import { pageShell } from "./views/nav.js";
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
  "/profile": profilePage,
};

const root = document.getElementById("app");

function render() {
  const current = state();
  if (!current) return;
  root.classList.remove("app-loading");

  // Until onboarding is finished every route shows the wizard, the same way the
  // Reflex build wrapped each page in a completed check.
  const view = current.onboarding.completed
    ? pageShell(current, (PAGES[currentRoute()] || dashboardPage)(current))
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
