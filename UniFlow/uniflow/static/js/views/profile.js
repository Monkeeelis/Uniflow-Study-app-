// Profile page: productivity stats, the study-time heatmap, and settings that
// double back into onboarding's fields (name, year, subjects, pomodoro
// durations, notifications) — profile is just a second place to edit them.

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { act } from "../state.js";
import { metric, selectField, tile } from "../ui.js";

function section(title, body) {
  return h("div", { class: "card mb-6" }, h("h2", { class: "h3 mb-4" }, title), body);
}

function initials(name) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "🙂";
  return parts
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function heatmapCell(cell) {
  return h("div", {
    class: [
      "heat-cell",
      !cell.in_range && "is-empty",
      cell.in_range && `level-${cell.level}`,
      cell.is_today && "is-today",
    ],
    title: `${cell.label} — ${cell.minutes} min`,
  });
}

function heatmapLegend() {
  return h(
    "div",
    { class: "heat-legend" },
    h("span", { class: "tiny muted mono" }, "0"),
    [0, 1, 2, 3, 4, 5].map((level) => h("span", { class: ["swatch", `heat-cell`, `level-${level}`] })),
    h("span", { class: "tiny muted mono" }, "2h+"),
  );
}

function rangeButton(insights, label, mode) {
  return h(
    "button",
    {
      class: ["pill pill-sm", insights.range_mode === mode && "is-active"],
      onClick: () => act("insights/range", { mode }),
    },
    label,
  );
}

function weeklyGoalBar(insights) {
  return h(
    "div",
    { class: "mb-6" },
    h(
      "div",
      { class: "row-between mb-2" },
      h("p", { class: "p small", style: { fontWeight: "600", color: "var(--heading)" } }, "Weekly study goal"),
      h(
        "p",
        { class: "p tiny muted mono" },
        `${insights.weekly_minutes_display} / ${insights.weekly_goal_display}`,
      ),
    ),
    h(
      "div",
      { class: "goal-track" },
      h("div", {
        class: ["goal-fill", insights.weekly_goal_met && "is-met"],
        style: { width: `${insights.weekly_goal_percent}%` },
      }),
    ),
  );
}

function insightsSection(insights) {
  return h(
    "div",
    { class: "card mb-6" },
    h(
      "div",
      { class: "row-between mb-4" },
      h(
        "div",
        {},
        h("h2", { class: "h3" }, "Study Insights"),
        h("p", { class: "p tiny muted mono" }, insights.range_label),
      ),
      h(
        "div",
        { class: "seg" },
        rangeButton(insights, "Week", "week"),
        rangeButton(insights, "Month", "month"),
        rangeButton(insights, "Year", "year"),
      ),
    ),
    weeklyGoalBar(insights),
    h(
      "div",
      { class: "grid grid-2 grid-tight grid-sm-4 mb-6" },
      metric("clock", "Total time", insights.total_display),
      metric("calendar-check", "Active days", insights.active_days),
      metric("chart-line", "Avg / active day", insights.average_display),
      metric("trophy", "Best day", insights.best_display),
    ),
    h(
      "div",
      { class: "heat-wrap mb-3" },
      h("div", { class: ["heat", `range-${insights.range_mode}`] }, insights.cells.map(heatmapCell)),
    ),
    h(
      "div",
      { class: "row-between" },
      h(
        "div",
        {},
        h("p", { class: "p eyebrow" }, "Best day"),
        h("p", { class: "p small", style: { fontWeight: "600", color: "var(--heading)" } }, insights.best_day_label),
      ),
      heatmapLegend(),
    ),
  );
}

function subjectsSection(onboarding) {
  const input = h("input", {
    class: "input grow",
    placeholder: "Add a subject",
    onKeyDown: (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        submit();
      }
    },
  });

  async function submit() {
    const name = input.value.trim();
    if (!name) return;
    input.value = "";
    await act("onboarding/subjects/add", { name });
  }

  return section(
    "Subjects",
    h(
      "div",
      {},
      h(
        "div",
        { class: "row mb-3" },
        input,
        h("button", { class: "btn btn-primary", "aria-label": "Add subject", onClick: submit }, icon("plus", "icon-sm")),
      ),
      h(
        "div",
        { class: "chip-list" },
        onboarding.subjects.map((subject) =>
          h(
            "div",
            { class: "chip" },
            h("span", {}, subject),
            h(
              "button",
              {
                "aria-label": `Remove ${subject}`,
                onClick: () => act("onboarding/subjects/remove", { name: subject }),
              },
              icon("x", "icon-xs"),
            ),
          ),
        ),
      ),
    ),
  );
}

function dangerZoneSection() {
  const resetAll = async () => {
    const sure = window.confirm(
      "Reset all UniFlow data? This deletes every task, event, note, flashcard deck, and focus session, and takes you back through setup. This cannot be undone.",
    );
    if (!sure) return;
    await act("system/reset");
  };

  return h(
    "div",
    { class: "card mb-6 danger-zone" },
    h("h2", { class: "h3 mb-2" }, "Danger zone"),
    h(
      "p",
      { class: "p small muted mb-4" },
      "Wipes everything — tasks, calendar, focus history, flashcards and notes — and restarts onboarding. There's no undo.",
    ),
    h(
      "button",
      { class: "btn btn-danger-outline", onClick: resetAll },
      icon("trash-2", "icon-sm"),
      "Reset all data",
    ),
  );
}

export function profilePage(state) {
  const { onboarding, tasks, focus, stats, insights } = state;

  return h(
    "div",
    {},
    h(
      "div",
      { class: "row mb-6", style: { gap: "16px" } },
      h(
        "div",
        { class: "avatar", style: { display: "grid", placeItems: "center" } },
        h(
          "span",
          { class: "display-lg", style: { color: "var(--accent)" } },
          initials(onboarding.name),
        ),
      ),
      h(
        "div",
        {},
        h("h1", { class: "h1 display-lg" }, onboarding.name || "Your profile"),
        h("p", { class: "p muted" }, onboarding.year_level),
      ),
    ),
    section(
      "Productivity",
      h(
        "div",
        { class: "grid grid-2 grid-tight grid-sm-4" },
        tile("Streak", `${stats.streak_days}d`),
        tile("Tasks done", tasks.completed_count),
        tile("Sessions", focus.sessions_today),
        tile("Total time", focus.study_hours_all),
      ),
    ),
    insightsSection(insights),
    section(
      "Profile",
      h(
        "div",
        {},
        h("label", { class: "label", for: "profile-name" }, "Name"),
        h("input", {
          class: "input mb-4",
          id: "profile-name",
          value: onboarding.name,
          onChange: (event) => act("onboarding/update", { name: event.target.value }),
        }),
        h("label", { class: "label" }, "Year level"),
        selectField({
          value: onboarding.year_level,
          options: [{ value: "", label: "Choose a year level" }, ...onboarding.year_options],
          onChange: (value) => act("onboarding/update", { year_level: value }),
        }),
      ),
    ),
    subjectsSection(onboarding),
    section(
      "Focus preferences",
      h(
        "div",
        { class: "grid grid-1-2" },
        h(
          "div",
          {},
          h("label", { class: "label", for: "profile-work" }, "Work duration (minutes)"),
          h("input", {
            class: "input",
            id: "profile-work",
            type: "number",
            min: "1",
            value: String(onboarding.pomodoro_work),
            onChange: (event) => act("onboarding/update", { pomodoro_work: event.target.value }),
          }),
        ),
        h(
          "div",
          {},
          h("label", { class: "label", for: "profile-break" }, "Break duration (minutes)"),
          h("input", {
            class: "input",
            id: "profile-break",
            type: "number",
            min: "1",
            value: String(onboarding.pomodoro_break),
            onChange: (event) => act("onboarding/update", { pomodoro_break: event.target.value }),
          }),
        ),
        h(
          "div",
          {},
          h("label", { class: "label", for: "profile-goal" }, "Weekly study goal (minutes)"),
          h("input", {
            class: "input",
            id: "profile-goal",
            type: "number",
            min: "1",
            value: String(onboarding.weekly_goal_minutes),
            onChange: (event) => act("onboarding/update", { weekly_goal_minutes: event.target.value }),
          }),
        ),
      ),
    ),
    section(
      "Accessibility",
      h(
        "div",
        {},
        h("label", { class: "label" }, "Theme"),
        h(
          "p",
          { class: "p tiny muted mb-3" },
          "Pick a colour theme for the whole app.",
        ),
        selectField({
          value: onboarding.theme,
          options: onboarding.theme_options,
          onChange: (value) => act("settings/theme/set", { theme: value }),
        }),
        h("label", { class: "label mt-4" }, "Colour blind support"),
        h(
          "p",
          { class: "p tiny muted mb-3" },
          "Adjusts colours across the app to be easier to tell apart.",
        ),
        selectField({
          value: onboarding.colorblind_mode,
          options: onboarding.colorblind_options,
          onChange: (value) => act("settings/colorblind/set", { mode: value }),
        }),
      ),
    ),
    section(
      "Notifications",
      h(
        "button",
        {
          class: ["toggle-card toggle-card-sm", onboarding.notifications_enabled && "is-on"],
          onClick: () => act("onboarding/notifications/toggle"),
        },
        h(
          "div",
          { class: "row", style: { gap: "12px" } },
          icon(onboarding.notifications_enabled ? "bell" : "bell-off", "icon-sm"),
          h(
            "span",
            { style: { fontWeight: "500" } },
            onboarding.notifications_enabled ? "Notifications enabled" : "Notifications disabled",
          ),
        ),
      ),
    ),
    dangerZoneSection(),
  );
}
