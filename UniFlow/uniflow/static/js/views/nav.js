// The navbar + notification bell that wraps every page once onboarding is
// done (see pageShell, used by main.js). Not a view in its own right.

import { h } from "../dom.js";
import { feedbackIcon, icon } from "../icons.js";
import { act, currentRoute, navigate } from "../state.js";

const LINKS = [
  { label: "Dashboard", href: "/dashboard", icon: "layout-dashboard" },
  { label: "Tasks", href: "/tasks", icon: "list-checks" },
  { label: "Calendar", href: "/calendar", icon: "calendar-days" },
  { label: "Focus", href: "/focus", icon: "timer" },
  { label: "Cards", href: "/quiz", icon: "layers" },
  { label: "Notes", href: "/notes", icon: "file-text" },
  { label: "Profile", href: "/profile", icon: "user" },
];

function link({ label, href, icon: iconName }) {
  return h(
    "a",
    {
      class: ["nav-link", currentRoute() === href && "is-active"],
      href,
      onClick: (event) => {
        event.preventDefault();
        navigate(href);
      },
    },
    icon(iconName),
    h("span", {}, label),
  );
}

function notificationItem(item) {
  return h(
    "div",
    { class: ["notif-item", !item.read && "is-unread"] },
    feedbackIcon(item.kind),
    h(
      "div",
      { class: "grow" },
      h("p", { class: "p small", style: { fontWeight: "600", color: "var(--heading)" } }, item.title),
      h("p", { class: "p tiny muted", style: { marginTop: "2px" } }, item.message),
      h("p", { class: "p tiny muted mono", style: { marginTop: "4px" } }, item.timestamp),
    ),
    h(
      "button",
      {
        class: "icon-btn icon-btn-sm",
        "aria-label": "Dismiss notification",
        onClick: () => act("notifications/dismiss", { notification_id: item.id }),
      },
      icon("x", "icon-xs"),
    ),
  );
}

function notificationPanel(notifications) {
  if (!notifications.show_panel) return null;
  return h(
    "div",
    { class: "notif-overlay", onClick: () => act("notifications/panel/toggle") },
    h(
      "div",
      { class: "notif-panel", onClick: (event) => event.stopPropagation() },
      h(
        "div",
        { class: "notif-head" },
        h("h3", { class: "h3" }, "Notifications"),
        h(
          "div",
          { class: "row" },
          h("button", { class: "link-btn", onClick: () => act("notifications/read-all") }, "Mark read"),
          h("button", { class: "link-btn", onClick: () => act("notifications/clear") }, "Clear"),
        ),
      ),
      notifications.items.length
        ? h("div", { class: "notif-list" }, notifications.items.map(notificationItem))
        : h(
            "div",
            { class: "notif-empty" },
            icon("bell-off", "icon-xl"),
            h("p", { class: "p small" }, "No notifications yet."),
          ),
    ),
  );
}

// The navbar re-renders on every state change (the whole app does — see
// main.js), so this guards the intro animation to only ever play once, on
// the very first paint, rather than replaying on every click.
let hasPlayedLogoIntro = false;

function navbar(state) {
  const playIntro = !hasPlayedLogoIntro;
  hasPlayedLogoIntro = true;

  return h(
    "header",
    { class: "navbar" },
    h(
      "div",
      { class: "nav-inner" },
      h(
        "a",
        {
          class: "brand",
          href: "/dashboard",
          onClick: (event) => {
            event.preventDefault();
            navigate("/dashboard");
          },
        },
        h("span", {
          class: ["brand-mark", playIntro && "brand-mark-intro"],
          "aria-hidden": "true",
        }),
        h("span", { class: ["brand-name", playIntro && "brand-name-intro"] }, "UniFlow"),
      ),
      h("nav", { class: "nav-links" }, LINKS.map(link)),
      // High-contrast is a single fixed palette with no dark variant, so the
      // light/dark toggle has nothing to do there — hide it rather than show
      // a control that's a no-op.
      state.onboarding.theme === "high-contrast"
        ? null
        : h(
            "button",
            {
              class: "icon-btn theme-toggle",
              "aria-label": state.onboarding.dark_mode ? "Switch to light mode" : "Switch to dark mode",
              title: state.onboarding.dark_mode ? "Switch to light mode" : "Switch to dark mode",
              onClick: () => act("settings/theme/toggle"),
            },
            icon(state.onboarding.dark_mode ? "sun" : "moon", "icon-sm"),
          ),
      h(
        "div",
        { class: "bell-wrap" },
        h(
          "button",
          {
            class: "bell",
            "aria-label": "Notifications",
            onClick: () => act("notifications/panel/toggle"),
          },
          icon("bell"),
          state.notifications.unread_count > 0 &&
            h("span", { class: "bell-badge" }, String(state.notifications.unread_count)),
        ),
        notificationPanel(state.notifications),
      ),
    ),
  );
}

export function pageShell(state, content, animateEntry) {
  return h(
    "div",
    { class: "app-shell" },
    navbar(state),
    h(
      "main",
      // Notes wants the sidebar/editor to start right under the navbar
      // instead of the usual page padding, so there's more vertical room
      // for the document itself.
      { class: ["main", animateEntry && "page-enter", currentRoute() === "/notes" && "main-tight"] },
      content,
    ),
  );
}
