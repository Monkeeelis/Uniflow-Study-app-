// Dashboard: quote, the free-running study timer, quick stats and upcoming
// tasks. The timer's digits (#dashboard-time et al.) are re-painted directly
// by timers.js every 100ms — see that file for why this isn't state-driven.

import { h } from "../dom.js";
import { clockTime, plural } from "../format.js";
import { icon } from "../icons.js";
import { act, navigate } from "../state.js";
import { clock } from "../timers.js";
import { eyebrow, emptyState, priorityBadge, statCard } from "../ui.js";

const QUICK_LINKS = [
  { href: "/tasks", icon: "list-checks", title: "Tasks", desc: "Manage your to-dos" },
  { href: "/calendar", icon: "calendar-days", title: "Calendar", desc: "Plan your schedule" },
  { href: "/focus", icon: "timer", title: "Focus", desc: "Pomodoro & timer" },
  { href: "/quiz", icon: "layers", title: "Cards", desc: "Study with flashcards" },
];

function quoteCard(dashboard) {
  return h(
    "div",
    { class: "quote-card mb-8" },
    icon("quote"),
    h(
      "div",
      { class: "grow" },
      h("p", { class: "p quote-text" }, dashboard.quote.text),
      h("p", { class: "p tiny muted mono mt-2" }, `— ${dashboard.quote.author}`),
    ),
    h(
      "button",
      {
        class: "icon-btn",
        title: "Show another quote",
        "aria-label": "Show another quote",
        onClick: () => act("dashboard/quote/next"),
      },
      icon("refresh-cw", "icon-sm"),
    ),
  );
}

function timerWidget(dashboard) {
  const seconds = clock.dashSeconds;
  return h(
    "div",
    { class: "card card-lg mb-8" },
    h(
      "div",
      { class: "row-between row-top mb-6" },
      h(
        "div",
        {},
        h(
          "div",
          { class: "row" },
          icon("timer", "icon-sm"),
          h("h2", { class: "h2" }, "Study timer"),
        ),
        h("p", { class: "p small muted mt-2" }, "Track any study session and save it to your history."),
      ),
      h(
        "div",
        { class: "row" },
        h("span", { class: ["run-dot", dashboard.timer_running && "is-on"] }),
        h("span", { class: "eyebrow" }, dashboard.timer_running ? "Running" : "Idle"),
      ),
    ),
    h(
      "div",
      { class: "timer-readout" },
      h("p", { class: "p timer-digits", id: "dashboard-time" }, clockTime(seconds)),
      h(
        "p",
        { class: "p eyebrow mt-2", id: "dashboard-caption" },
        seconds > 0
          ? `${Math.floor(seconds / 60)} min pending — press stop to save`
          : "Press start when you begin studying",
      ),
    ),
    h(
      "div",
      { class: "row row-wrap", style: { gap: "12px" } },
      dashboard.timer_running
        ? h(
            "button",
            {
              class: "btn btn-lg btn-primary btn-flex",
              onClick: () => act("dashboard/timer/pause", { seconds: clock.dashSeconds }),
            },
            icon("pause"),
            "Pause",
          )
        : h(
            "button",
            { class: "btn btn-lg btn-primary btn-flex", onClick: () => act("dashboard/timer/start") },
            icon("play"),
            seconds > 0 ? "Resume" : "Start",
          ),
      h(
        "button",
        {
          class: "btn btn-lg btn-teal btn-flex",
          id: "dashboard-stop",
          disabled: seconds === 0,
          onClick: () => act("dashboard/timer/save", { seconds: clock.dashSeconds }),
        },
        icon("square"),
        "Stop & save",
      ),
    ),
    h(
      "div",
      { class: "grid grid-1-2 grid-tight mt-6" },
      h(
        "div",
        { class: "card-inset" },
        h("div", { class: "row" }, icon("clock", "icon-sm"), h("span", { class: "eyebrow" }, "Today's dashboard total")),
        h("p", { class: "p display-lg" }, dashboard.today_display),
        h("p", { class: "p tiny muted mono" }, `${plural(dashboard.sessions_today_count, "session")} saved today`),
      ),
      h(
        "div",
        { class: "card-inset" },
        h("div", { class: "row" }, icon("infinity", "icon-sm"), h("span", { class: "eyebrow" }, "All-time dashboard total")),
        h("p", { class: "p display-lg" }, dashboard.all_display),
        h("p", { class: "p tiny muted mono" }, `${plural(dashboard.sessions_total, "session")} saved overall`),
      ),
    ),
    dashboard.recent_sessions.length
      ? h(
          "div",
          { class: "card-inset mt-4" },
          eyebrow("history", "Recent saved sessions"),
          h(
            "div",
            { class: "stack-sm" },
            dashboard.recent_sessions.map((session) =>
              h(
                "div",
                { class: "card-flat row" },
                h(
                  "div",
                  { class: "grow" },
                  h("p", { class: "p mono", style: { fontWeight: "700", color: "var(--heading)" } }, session.duration),
                  h("p", { class: "p tiny muted mono" }, session.date),
                ),
                h(
                  "button",
                  {
                    class: "icon-btn icon-btn-danger icon-btn-sm",
                    "aria-label": "Delete session",
                    onClick: () => act("dashboard/sessions/delete", { session_id: session.id }),
                  },
                  icon("trash-2", "icon-sm"),
                ),
              ),
            ),
          ),
        )
      : null,
  );
}

function urgentTask(task) {
  return h(
    "div",
    { class: "card-flat row-between", style: { gap: "12px" } },
    h(
      "div",
      {},
      h("p", { class: "p", style: { fontWeight: "500", color: "var(--heading)" } }, task.title),
      h("p", { class: "p tiny muted" }, [task.subject, task.due_date].filter(Boolean).join(" · ")),
    ),
    priorityBadge(task.priority),
  );
}

export function dashboardPage(state) {
  const { onboarding, tasks, dashboard, stats } = state;

  return h(
    "div",
    {},
    h(
      "div",
      { class: "row-between row-top mb-6" },
      h(
        "div",
        {},
        h("p", { class: "p small muted mono" }, "Welcome back,"),
        h("h1", { class: "h1 h1-lg" }, onboarding.name ? `Hi, ${onboarding.name}!` : "Hi there!"),
        h("p", { class: "p muted mt-2" }, stats.motivation_message),
      ),
      h(
        "div",
        { class: "streak-badge" },
        icon("flame", "icon-sm"),
        h("span", { class: "value" }, String(stats.streak_days)),
        h("span", { class: "tiny muted mono" }, "day streak"),
      ),
    ),
    quoteCard(dashboard),
    timerWidget(dashboard),
    h(
      "div",
      { class: "grid grid-2 grid-lg-4 mb-8" },
      statCard("list-checks", "Active Tasks", tasks.total_count - tasks.completed_count),
      statCard("circle-check", "Completed", tasks.completed_count, "teal"),
      statCard("timer", "Today's total time", dashboard.today_display),
      statCard("book", "Subjects", onboarding.subjects.length),
    ),
    h("h2", { class: "h2 mb-4" }, "Quick access"),
    h(
      "div",
      { class: "grid grid-1-2" },
      QUICK_LINKS.map((entry) =>
        h(
          "a",
          {
            class: "quick-link",
            href: entry.href,
            onClick: (event) => {
              event.preventDefault();
              navigate(entry.href);
            },
          },
          h("div", { class: "stat-icon" }, icon(entry.icon, "icon-lg")),
          h("p", { class: "p quick-link-title" }, entry.title),
          h("p", { class: "p small muted" }, entry.desc),
        ),
      ),
    ),
    h("h2", { class: "h2 mt-8 mb-4" }, "Coming up"),
    tasks.urgent.length
      ? h("div", { class: "card" }, h("div", { class: "stack-sm" }, tasks.urgent.map(urgentTask)))
      : emptyState("coffee", "No upcoming tasks. Enjoy your break!"),
  );
}
