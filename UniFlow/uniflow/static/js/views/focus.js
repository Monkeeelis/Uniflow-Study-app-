// Focus page: pomodoro/timer mode switch, the countdown dial, and session
// stats. The dial's digits and progress ring are re-painted directly by
// timers.js every 100ms rather than through a full re-render — see that file.
// `rebaseFocus` is called after actions that reset the clock server-side
// while it keeps running (skip), where the next state push won't do it for us.

import { AMBIENT_OPTIONS, currentPrefs, play, setVolume, stop as stopAmbient } from "../ambient.js";
import { h } from "../dom.js";
import { countdown } from "../format.js";
import { icon } from "../icons.js";
import { act } from "../state.js";
import { clock, rebaseFocus } from "../timers.js";
import { eyebrow, tile } from "../ui.js";

function modePill(focus, { label, value, icon: iconName }) {
  return h(
    "button",
    {
      class: ["pill", focus.mode === value && "is-active"],
      onClick: async () => {
        await act("focus/mode", { mode: value });
        rebaseFocus(0);
      },
    },
    icon(iconName, "icon-sm"),
    h("span", {}, label),
  );
}

function dial(focus) {
  const targetDs = focus.target_seconds * 10;
  const percent = targetDs > 0 ? Math.min(100, (clock.focusDs / targetDs) * 100) : 0;
  const isWork = focus.pomodoro_phase === "work";

  return h(
    "div",
    { class: "dial-wrap" },
    h(
      "div",
      { class: "dial" },
      h("div", { class: "dial-ring", id: "focus-ring", style: { "--progress": `${percent}%` } }),
      h(
        "div",
        { class: "dial-inner" },
        h("p", { class: "p dial-time", id: "focus-time" }, countdown(targetDs - clock.focusDs)),
        focus.mode === "pomodoro"
          ? h("p", { class: ["p dial-phase", isWork ? "is-work" : "is-break"] }, isWork ? "FOCUS TIME" : "BREAK TIME")
          : h("p", { class: "p dial-phase" }, "TIMER"),
      ),
    ),
  );
}

function controls(focus) {
  return h(
    "div",
    { class: "row row-wrap", style: { justifyContent: "center", gap: "12px" } },
    focus.running
      ? h(
          "button",
          {
            class: "btn btn-lg btn-primary",
            onClick: () => act("focus/pause", { elapsed_ds: clock.focusDs }),
          },
          icon("pause"),
          "Pause",
        )
      : h(
          "button",
          { class: "btn btn-lg btn-primary", onClick: () => act("focus/start") },
          icon("play"),
          "Start",
        ),
    h(
      "button",
      { class: "btn btn-lg btn-outline", onClick: () => act("focus/reset") },
      icon("rotate-ccw"),
      "Reset",
    ),
    focus.mode === "pomodoro"
      ? h(
          "button",
          {
            class: "btn btn-lg btn-outline",
            onClick: async () => {
              await act("focus/skip", { elapsed_ds: clock.focusDs });
              rebaseFocus(0);
            },
          },
          icon("skip-forward"),
          "Skip",
        )
      : null,
  );
}

function settings(focus) {
  if (focus.mode === "pomodoro") {
    return h(
      "div",
      { class: "row row-wrap", style: { justifyContent: "center", gap: "24px" } },
      h(
        "div",
        { class: "center" },
        h("p", { class: "p eyebrow mb-2" }, "Cycles"),
        h(
          "div",
          { class: "cycle-dots" },
          focus.cycle_dots.map((dot) => h("div", { class: ["dot", dot.filled && "is-filled"] })),
        ),
      ),
      h(
        "div",
        {},
        h("label", { class: "label label-sm", for: "focus-cycles" }, "Total cycles"),
        h("input", {
          class: "input input-sm input-tiny",
          id: "focus-cycles",
          type: "number",
          min: "1",
          value: String(focus.total_cycles),
          onChange: (event) => act("focus/settings", { total_cycles: event.target.value }),
        }),
      ),
    );
  }
  return h(
    "div",
    { class: "row row-wrap", style: { justifyContent: "center", gap: "16px" } },
    h(
      "div",
      { class: "center" },
      h("label", { class: "label label-sm", for: "focus-duration-min" }, "Minutes"),
      h("input", {
        class: "input input-sm input-narrow",
        id: "focus-duration-min",
        type: "number",
        min: "0",
        value: String(focus.timer_duration_minutes),
        // No rebase here: changing the target while idle is already reflected
        // (elapsed is 0 either way), and forcing it while running would zero
        // out an in-progress countdown the server was never told to reset.
        onChange: (event) => act("focus/settings", { timer_duration_minutes: event.target.value }),
      }),
    ),
    h(
      "div",
      { class: "center" },
      h("label", { class: "label label-sm", for: "focus-duration-sec" }, "Seconds"),
      h("input", {
        class: "input input-sm input-narrow",
        id: "focus-duration-sec",
        type: "number",
        min: "0",
        max: "59",
        value: String(focus.timer_duration_seconds),
        onChange: (event) => act("focus/settings", { timer_duration_seconds: event.target.value }),
      }),
    ),
  );
}

// Ambient playback lives entirely client-side (see ambient.js), so clicks
// here update the DOM directly instead of round-tripping through act()/a
// full state re-render.
function ambientControls() {
  const prefs = currentPrefs();
  const pills = [];

  const applyActiveState = (kind) => {
    for (const pill of pills) {
      const isActive = pill.dataset.kind === kind;
      pill.classList.toggle("is-active", isActive);
    }
  };

  const optionPill = (option) => {
    const pillEl = h(
      "button",
      {
        class: ["pill", option.value === prefs.kind && "is-active"],
        type: "button",
        onClick: () => {
          if (option.value === "none") stopAmbient();
          else play(option.value);
          applyActiveState(option.value);
        },
      },
      option.label,
    );
    pillEl.dataset.kind = option.value;
    pills.push(pillEl);
    return pillEl;
  };

  const volumeSlider = h("input", {
    type: "range",
    class: "ambient-volume",
    min: "0",
    max: "100",
    value: String(Math.round(prefs.volume * 100)),
    "aria-label": "Ambient volume",
    onInput: (event) => setVolume(Number(event.target.value) / 100),
  });

  return h(
    "div",
    { class: "card card-lg mt-6" },
    eyebrow("infinity", "Ambient sound"),
    h("div", { class: "switch mb-3", style: { flexWrap: "wrap" } }, AMBIENT_OPTIONS.map(optionPill)),
    h(
      "div",
      { class: "row", style: { gap: "10px", maxWidth: "260px" } },
      icon("volume", "icon-sm"),
      volumeSlider,
    ),
  );
}

function sessionRow(session) {
  return h(
    "div",
    { class: "session-row" },
    h(
      "div",
      { class: "row" },
      icon(session.completed === "yes" ? "circle-check" : "circle-dashed", "icon-sm"),
      h("span", { class: "small", style: { fontWeight: "600", color: "var(--heading)" } }, session.mode),
    ),
    h(
      "div",
      { class: "row", style: { gap: "12px" } },
      h("span", { class: "small mono", style: { fontWeight: "700", color: "var(--accent)" } }, session.duration),
      h("span", { class: "tiny muted mono" }, session.date),
    ),
  );
}

export function focusPage(state) {
  const { focus } = state;

  return h(
    "div",
    {},
    h(
      "div",
      { class: "center mb-6" },
      h("h1", { class: "h1" }, "Focus"),
      h("p", { class: "p muted mt-2" }, "Deep work, one session at a time."),
    ),
    h(
      "div",
      { class: "switch mb-8" },
      modePill(focus, { label: "Pomodoro", value: "pomodoro", icon: "brain" }),
      modePill(focus, { label: "Timer", value: "timer", icon: "hourglass" }),
    ),
    dial(focus),
    h("div", { class: "mt-8" }, controls(focus)),
    h("div", { class: "mt-6" }, settings(focus)),
    ambientControls(),
    h(
      "div",
      { class: "grid grid-2 grid-tight grid-sm-4 mt-6" },
      tile("Study today", `${focus.study_minutes_today}m`),
      tile("Pomodoros", focus.pomodoros_completed_today),
      tile("Timers done", focus.timers_completed_today),
      tile("All time", focus.study_hours_all),
    ),
    focus.recent_sessions.length
      ? h(
          "div",
          { class: "card card-lg mt-6" },
          eyebrow("history", "Recent sessions"),
          h("div", { class: "stack-sm" }, focus.recent_sessions.map(sessionRow)),
        )
      : null,
  );
}
