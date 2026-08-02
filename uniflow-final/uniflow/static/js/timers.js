// The two running clocks live here.
//
// Polling the server ten times a second would be wasteful, so the browser
// counts the ticks and patches just the digits on screen. Python still owns
// everything that matters: it decides when a phase is over, logs the session
// and totals the stats. Elapsed time is reported back on pause, skip, phase
// completion, and via a heartbeat every few seconds so a closed tab doesn't
// lose the current run.

import { ping } from "./api.js";
import { clockTime, countdown } from "./format.js";
import { act, state, subscribe } from "./state.js";

const SYNC_EVERY_MS = 5000;

export const clock = { focusDs: 0, dashSeconds: 0 };

let focusBase = null; // { ds, at } — monotonic baseline, so ticks never drift
let dashBase = null;
let phaseChangePending = false;
let lastSyncAt = 0;

subscribe(() => {
  const current = state();
  if (!current) return;
  // While a clock runs the server value is deliberately stale, so only adopt
  // it when the server says the clock is stopped.
  if (!current.focus.running) {
    clock.focusDs = current.focus.elapsed_ds;
    focusBase = null;
  }
  if (!current.dashboard.timer_running) {
    clock.dashSeconds = current.dashboard.timer_seconds;
    dashBase = null;
  }
});

/** Called after an action that resets a clock while it keeps running. */
export function rebaseFocus(ds = 0) {
  clock.focusDs = ds;
  focusBase = null;
}

export function rebaseDashboard(seconds = 0) {
  clock.dashSeconds = seconds;
  dashBase = null;
}

function tick() {
  const current = state();
  if (!current) return;
  const now = performance.now();

  if (current.focus.running) {
    if (!focusBase) focusBase = { ds: clock.focusDs, at: now };
    clock.focusDs = focusBase.ds + Math.floor((now - focusBase.at) / 100);
    const targetDs = current.focus.target_seconds * 10;
    if (clock.focusDs >= targetDs && !phaseChangePending) {
      phaseChangePending = true;
      clock.focusDs = targetDs;
      act("focus/complete", { elapsed_ds: targetDs }).then(() => {
        rebaseFocus(0);
        phaseChangePending = false;
      });
    }
  } else {
    focusBase = null;
  }

  if (current.dashboard.timer_running) {
    if (!dashBase) dashBase = { seconds: clock.dashSeconds, at: now };
    clock.dashSeconds = dashBase.seconds + Math.floor((now - dashBase.at) / 1000);
  } else {
    dashBase = null;
  }

  paint(current);

  if (current.focus.running || current.dashboard.timer_running) {
    if (now - lastSyncAt > SYNC_EVERY_MS) {
      lastSyncAt = now;
      if (current.focus.running) ping("focus/sync", { elapsed_ds: clock.focusDs });
      if (current.dashboard.timer_running)
        ping("dashboard/timer/sync", { seconds: clock.dashSeconds });
    }
  }
}

/** Patch only the digits, so typing elsewhere on the page is never disturbed. */
function paint(current) {
  const focusTime = document.getElementById("focus-time");
  if (focusTime) {
    const targetDs = current.focus.target_seconds * 10;
    focusTime.textContent = countdown(targetDs - clock.focusDs);
    const ring = document.getElementById("focus-ring");
    if (ring) {
      const percent = targetDs > 0 ? Math.min(100, (clock.focusDs / targetDs) * 100) : 0;
      ring.style.setProperty("--progress", `${percent}%`);
    }
  }

  const dashTime = document.getElementById("dashboard-time");
  if (dashTime) {
    dashTime.textContent = clockTime(clock.dashSeconds);
    const caption = document.getElementById("dashboard-caption");
    if (caption) {
      caption.textContent =
        clock.dashSeconds > 0
          ? `${Math.floor(clock.dashSeconds / 60)} min pending — press stop to save`
          : "Press start when you begin studying";
    }
    const stop = document.getElementById("dashboard-stop");
    if (stop) stop.disabled = clock.dashSeconds === 0;
  }
}

export function startTicking() {
  setInterval(tick, 100);
  // Report the final position if the tab closes mid-session.
  window.addEventListener("pagehide", () => {
    const current = state();
    if (!current) return;
    if (current.focus.running) ping("focus/sync", { elapsed_ds: clock.focusDs });
    if (current.dashboard.timer_running)
      ping("dashboard/timer/sync", { seconds: clock.dashSeconds });
  });
}
