// Transient toast notifications shown in the bottom corner stack.

import { h } from "./dom.js";
import { feedbackIcon } from "./icons.js";

const TOAST_MS = 3000;

export function showToast(toast) {
  if (!toast || !toast.message) return;
  const stack = document.getElementById("toasts");
  if (!stack) return;

  const kind = toast.kind || "info";
  const node = h(
    "div",
    { class: ["toast", kind === "success" && "is-success", kind === "warning" && "is-warning"] },
    feedbackIcon(kind),
    h("span", { class: "grow" }, toast.message),
    h(
      "button",
      { class: "link-btn", "aria-label": "Dismiss", onClick: () => node.remove() },
      "✕",
    ),
  );
  stack.append(node);
  setTimeout(() => node.remove(), TOAST_MS);
}
