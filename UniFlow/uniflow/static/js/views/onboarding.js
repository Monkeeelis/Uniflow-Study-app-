// First-run wizard, shown instead of any page until onboarding.completed is
// true (see main.js). Each step saves straight to the backend as you type/
// pick, same fields the Profile page edits later — there's no local draft
// state or a final "submit"; `finish()` just flips the completed flag.

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { act, navigate } from "../state.js";
import { selectField } from "../ui.js";

function stepIndicator(step) {
  return h(
    "div",
    { class: "steps" },
    [0, 1, 2, 3].map((i) => h("div", { class: ["step-bar", step >= i && "is-done"] })),
  );
}

function stepName(ob) {
  return h(
    "div",
    {},
    h("h2", { class: "h1 mb-2" }, "Welcome!"),
    h("p", { class: "p muted mb-6" }, "Let's get to know you."),
    h("label", { class: "label", for: "ob-name" }, "Your name"),
    h("input", {
      class: "input",
      id: "ob-name",
      value: ob.name,
      placeholder: "e.g. Alex",
      onChange: (event) => act("onboarding/update", { name: event.target.value }),
    }),
    h("label", { class: "label mt-4" }, "Year level"),
    selectField({
      value: ob.year_level,
      options: [{ value: "", label: "Choose a year level" }, ...ob.year_options],
      onChange: (value) => act("onboarding/update", { year_level: value }),
    }),
  );
}

function stepSubjects(ob) {
  const input = h("input", {
    class: "input grow",
    placeholder: "e.g. Mathematics",
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

  return h(
    "div",
    {},
    h("h2", { class: "h1 mb-2" }, "Your subjects"),
    h("p", { class: "p muted mb-6" }, "Add subjects you're studying."),
    h(
      "div",
      { class: "row mb-4" },
      input,
      h("button", { class: "btn btn-primary", type: "button", onClick: submit, "aria-label": "Add subject" }, icon("plus")),
    ),
    h(
      "div",
      { class: "chip-list" },
      ob.subjects.map((subject) =>
        h(
          "div",
          { class: "chip" },
          h("span", {}, subject),
          h(
            "button",
            {
              type: "button",
              "aria-label": `Remove ${subject}`,
              onClick: () => act("onboarding/subjects/remove", { name: subject }),
            },
            icon("x", "icon-xs"),
          ),
        ),
      ),
    ),
  );
}

function stepPomodoro(ob) {
  return h(
    "div",
    {},
    h("h2", { class: "h1 mb-2" }, "Focus preferences"),
    h("p", { class: "p muted mb-6" }, "Customize your Pomodoro timer."),
    h("label", { class: "label", for: "ob-work" }, "Work duration (minutes)"),
    h("input", {
      class: "input",
      id: "ob-work",
      type: "number",
      min: "1",
      value: String(ob.pomodoro_work),
      onChange: (event) => act("onboarding/update", { pomodoro_work: event.target.value }),
    }),
    h("label", { class: "label mt-4", for: "ob-break" }, "Break duration (minutes)"),
    h("input", {
      class: "input",
      id: "ob-break",
      type: "number",
      min: "1",
      value: String(ob.pomodoro_break),
      onChange: (event) => act("onboarding/update", { pomodoro_break: event.target.value }),
    }),
    h("label", { class: "label mt-4", for: "ob-goal" }, "Weekly study goal (minutes)"),
    h("input", {
      class: "input",
      id: "ob-goal",
      type: "number",
      min: "1",
      value: String(ob.weekly_goal_minutes),
      onChange: (event) => act("onboarding/update", { weekly_goal_minutes: event.target.value }),
    }),
  );
}

function stepNotifications(ob) {
  return h(
    "div",
    {},
    h("h2", { class: "h1 mb-2" }, "Notifications"),
    h("p", { class: "p muted mb-6" }, "Get reminders for tasks and study time."),
    h(
      "button",
      {
        class: ["toggle-card", ob.notifications_enabled && "is-on"],
        type: "button",
        onClick: () => act("onboarding/notifications/toggle"),
      },
      h(
        "div",
        { class: "row", style: { gap: "16px" } },
        icon(ob.notifications_enabled ? "bell" : "bell-off", "icon-lg"),
        h(
          "div",
          {},
          h("p", { class: "p", style: { fontWeight: "600" } }, ob.notifications_enabled ? "Enabled" : "Disabled"),
          h("p", { class: "p small muted" }, "Tap to toggle"),
        ),
      ),
    ),
  );
}

const STEPS = [stepName, stepSubjects, stepPomodoro, stepNotifications];

export function onboardingPage(state) {
  const ob = state.onboarding;
  const step = Math.min(ob.step, STEPS.length - 1);

  return h(
    "div",
    { class: "onboarding" },
    h(
      "div",
      { class: "onboarding-card" },
      h(
        "div",
        { class: "onboarding-brand" },
        h("img", { src: "/static/img/logo-mark.png", alt: "", class: "onboarding-mark" }),
        h("span", {}, "UniFlow"),
      ),
      stepIndicator(step),
      h("div", { class: "mb-8" }, STEPS[step](ob)),
      h(
        "div",
        { class: "row-between" },
        step > 0
          ? h(
              "button",
              { class: "btn btn-outline", onClick: () => act("onboarding/step", { delta: -1 }) },
              icon("arrow-left", "icon-sm"),
              "Back",
            )
          : h("div"),
        step < ob.last_step
          ? h(
              "button",
              { class: "btn btn-primary", onClick: () => act("onboarding/step", { delta: 1 }) },
              "Next",
              icon("arrow-right", "icon-sm"),
            )
          : h(
              "button",
              {
                class: "btn btn-teal",
                onClick: async () => {
                  await act("onboarding/finish");
                  navigate("/dashboard");
                },
              },
              "Get Started",
              icon("check", "icon-sm"),
            ),
      ),
    ),
  );
}
