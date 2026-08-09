// Small building blocks reused across the pages.

import { h } from "./dom.js";
import { feedbackIcon, icon } from "./icons.js";

export function eyebrow(iconName, text) {
  return h(
    "div",
    { class: "row mb-3" },
    iconName && icon(iconName, "icon-sm"),
    h("span", { class: "eyebrow" }, text),
  );
}

export function selectField({ name, value, options, onChange, small = false }) {
  const select = h(
    "select",
    {
      class: small ? "select select-sm" : "select",
      name,
      onChange: onChange && ((event) => onChange(event.target.value)),
    },
    options.map((option) => {
      const label = typeof option === "string" ? option : option.label;
      const val = typeof option === "string" ? option : option.value;
      return h("option", { value: val }, label);
    }),
  );
  // Set after the options exist, so this is the one place that decides
  // which one is selected — no need to duplicate the check per-option.
  select.value = value ?? "";
  return h(
    "div",
    { class: "select-wrap" },
    select,
    icon("chevron-down", small ? "icon-xs chev" : "icon-sm chev"),
  );
}

export function banner(feedback) {
  if (!feedback || !feedback.message) return null;
  const kind = feedback.kind || "info";
  return h(
    "div",
    {
      class: ["banner", kind === "success" && "is-success", kind === "warning" && "is-warning"],
      role: "status",
    },
    feedbackIcon(kind),
    h("span", {}, feedback.message),
  );
}

export function emptyState(iconName, message) {
  return h(
    "div",
    { class: "card-empty" },
    h("div", { class: "row", style: { justifyContent: "center", marginBottom: "12px" } },
      icon(iconName, "icon-hero")),
    h("p", { class: "p" }, message),
  );
}

export function modal({ title, onClose, children, footer, onSubmit, small = false }) {
  const inner = h(
    onSubmit ? "form" : "div",
    {
      class: ["modal", small && "modal-sm"],
      onClick: (event) => event.stopPropagation(),
      onSubmit:
        onSubmit &&
        ((event) => {
          event.preventDefault();
          onSubmit(readForm(event.currentTarget));
        }),
    },
    h(
      "div",
      { class: "modal-head" },
      h("h2", { class: "h2" }, title),
      h(
        "button",
        { class: "icon-btn", type: "button", "aria-label": "Close", onClick: onClose },
        icon("x"),
      ),
    ),
    children,
    footer,
  );
  return h("div", { class: "modal-overlay", onClick: onClose }, inner);
}

export function readForm(form) {
  const out = {};
  for (const [key, value] of new FormData(form)) out[key] = value;
  return out;
}

export function statCard(iconName, label, value, tone = "accent") {
  return h(
    "div",
    { class: "card" },
    h("div", { class: ["stat-icon", tone === "teal" && "is-teal"] }, icon(iconName, "icon-lg")),
    h("p", { class: "p small muted", style: { fontWeight: "500" } }, label),
    h("p", { class: "p stat-value" }, String(value)),
  );
}

export function tile(label, value) {
  return h(
    "div",
    { class: "tile" },
    h("p", { class: "p eyebrow" }, label),
    h("p", { class: "p tile-value" }, String(value)),
  );
}

export function metric(iconName, label, value) {
  return h(
    "div",
    { class: "metric" },
    h(
      "div",
      { class: "row mb-1" },
      icon(iconName, "icon-sm"),
      h("p", { class: "p eyebrow" }, label),
    ),
    h("p", { class: "p tile-value" }, String(value)),
  );
}

export function priorityBadge(priority) {
  const tone =
    { High: "badge-high", Medium: "badge-medium", Low: "badge-low" }[priority] ||
    "badge-neutral";
  return h("span", { class: ["badge", tone] }, priority);
}
