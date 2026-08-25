// Client-side mirror of the server's view model, plus the current route.
// Nothing here computes app state — it only holds what the backend sent and
// tells subscribers to re-render.

import * as api from "./api.js";
import { showToast } from "./toast.js";

const PAGES = ["/dashboard", "/tasks", "/calendar", "/focus", "/quiz", "/notes", "/profile"];

let current = null;
let route = normalisePath(window.location.pathname);
const listeners = new Set();

export function normalisePath(path) {
  const clean = (path || "/").replace(/\/+$/, "") || "/";
  return PAGES.includes(clean) ? clean : "/dashboard";
}

export function state() {
  return current;
}

export function currentRoute() {
  return route;
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function emit() {
  for (const fn of listeners) fn();
}

// For UI toggles that are pure client-side preference (not server data) —
// e.g. collapsing a sidebar — and just need the page to re-render without a
// round trip through act().
export function refresh() {
  emit();
}

export function setState(next) {
  current = next;
  const root = document.documentElement;
  root.dataset.theme = next?.onboarding?.theme || "light";
  root.dataset.mode = next?.onboarding?.dark_mode ? "dark" : "light";
  const colorblind = next?.onboarding?.colorblind_mode || "none";
  if (colorblind === "none") delete root.dataset.colorblind;
  else root.dataset.colorblind = colorblind;
  emit();
}

export function navigate(path, { replace = false } = {}) {
  const target = normalisePath(path);
  if (replace) window.history.replaceState({}, "", target);
  else if (target !== window.location.pathname) window.history.pushState({}, "", target);
  route = target;
  window.scrollTo({ top: 0 });
  emit();
}

export function syncRouteFromUrl() {
  route = normalisePath(window.location.pathname);
  emit();
}

export async function load() {
  const res = await api.fetchState();
  setState(res.state);
}

export async function act(action, payload = {}) {
  try {
    const res = await api.post(action, payload);
    if (res && res.state) setState(res.state);
    if (res && res.toast) showToast(res.toast);
    return res;
  } catch (error) {
    console.error(error);
    showToast({ message: "Could not reach the server. Is it still running?", kind: "warning" });
    return null;
  }
}
