// Calendar page: month grid, week/day time grids, category manager, and the
// event form/detail modals. All the layout maths — which cells a month has,
// where a timed block sits in pixels, which events are "all day" — is done
// server-side (services/calendar.py); this file just places the boxes it's given.

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { act } from "../state.js";
import { banner, modal, selectField } from "../ui.js";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const openDetail = (eventId) => act("calendar/event-detail", { open: true, event_id: eventId });
const openNewEvent = (date) => act("calendar/event-form", { open: true, date });

function eventPill(event) {
  return h(
    "button",
    { class: "event-pill", onClick: () => openDetail(event.id) },
    h("span", { class: "event-dot", style: { backgroundColor: event.color } }),
    event.start_time && h("span", { class: "event-time" }, event.start_time),
    h("span", { class: "event-name" }, event.title),
  );
}

function monthCell(cal, cell) {
  if (cell.in_month !== "true") return h("div", { class: "cal-cell is-blank" });
  const events = cal.events_by_date[cell.date] || [];
  return h(
    "div",
    { class: "cal-cell" },
    h(
      "div",
      { class: "cal-cell-head" },
      h("span", { class: ["cal-daynum", cell.is_today === "true" && "is-today"] }, cell.day),
      h(
        "button",
        {
          class: "icon-btn icon-btn-sm add-day",
          "aria-label": `Add event on ${cell.date}`,
          onClick: () => openNewEvent(cell.date),
        },
        icon("plus", "icon-xs"),
      ),
    ),
    h("div", { class: "stack-sm", style: { gap: "2px" } }, events.map(eventPill)),
  );
}

function monthView(cal) {
  return h(
    "div",
    { class: "cal-scroll" },
    h(
      "div",
      { class: "cal-inner" },
      h("div", { class: "cal-weekdays" }, WEEKDAYS.map((day) => h("div", { class: "cal-weekday" }, day))),
      h("div", { class: "cal-grid" }, cal.month_cells.map((cell) => monthCell(cal, cell))),
    ),
  );
}

function timedBlock(cal, block) {
  return h(
    "button",
    {
      class: "timed-block",
      style: {
        top: `${block.top}px`,
        height: `${block.height}px`,
        left: `calc(${block.left_pct}% + 4px)`,
        width: `calc(${block.width_pct}% - 8px)`,
        borderLeftColor: block.color,
      },
      onClick: () => openDetail(block.id),
    },
    h(
      "div",
      { class: "timed-block-time" },
      h("b", {}, block.start_time),
      h("span", {}, "–"),
      h("b", {}, block.end_time),
      block.duration_label && h("span", {}, `· ${block.duration_label}`),
    ),
    h("p", { class: "p timed-block-title" }, block.title),
    block.category && h("p", { class: "p timed-block-cat" }, block.category),
  );
}

function allDayPill(event) {
  return h(
    "button",
    { class: "allday-pill", onClick: () => openDetail(event.id) },
    h("span", { class: "event-dot", style: { backgroundColor: event.color } }),
    h("span", { class: "event-name" }, event.title),
  );
}

function dayColumn(cal, dateStr) {
  const blocks = cal.positioned_events_by_date[dateStr] || [];
  return h(
    "div",
    { class: "day-col", style: { height: `${cal.grid_height_px}px` } },
    cal.hour_labels.map(() => h("div", { class: "hour-line", style: { height: `${cal.hour_height_px}px` } })),
    h("div", { class: "day-blocks" }, blocks.map((block) => timedBlock(cal, block))),
  );
}

function hourColumn(cal, withSpacer) {
  return h(
    "div",
    { class: "hour-col" },
    withSpacer && h("div", { class: "hour-col-spacer" }),
    cal.hour_labels.map((hour) =>
      h("div", { class: "hour-label", style: { height: `${cal.hour_height_px}px` } }, hour.label),
    ),
  );
}

function weekView(cal) {
  return h(
    "div",
    { class: "time-grid" },
    hourColumn(cal, true),
    h(
      "div",
      { class: "day-cols" },
      cal.week_days.map((day) => {
        const allDay = cal.all_day_events_by_date[day.date] || [];
        return h(
          "div",
          { class: "week-col" },
          h(
            "div",
            { class: "week-col-head" },
            h("span", { class: ["label", day.is_today === "true" && "is-today"] }, day.label),
            h(
              "button",
              {
                class: "icon-btn icon-btn-sm",
                "aria-label": `Add event on ${day.date}`,
                onClick: () => openNewEvent(day.date),
              },
              icon("plus", "icon-xs"),
            ),
          ),
          allDay.length ? h("div", { class: "allday-strip" }, allDay.map(allDayPill)) : null,
          dayColumn(cal, day.date),
        );
      }),
    ),
  );
}

function dayView(cal) {
  const allDay = cal.all_day_events_by_date[cal.day_date_str] || [];
  return h(
    "div",
    {},
    h(
      "div",
      { class: "row-between mb-3" },
      h("h3", { class: "h3" }, "Schedule"),
      h(
        "button",
        { class: "btn btn-sm btn-primary", onClick: () => openNewEvent(cal.day_date_str) },
        icon("plus", "icon-sm"),
        "Add event",
      ),
    ),
    allDay.length
      ? h(
          "div",
          { class: "card-inset mb-3" },
          h("p", { class: "p eyebrow mb-2" }, "All day"),
          h("div", { class: "stack-sm" }, allDay.map(allDayPill)),
        )
      : null,
    h("div", { class: "time-grid" }, hourColumn(cal, false), dayColumn(cal, cal.day_date_str)),
  );
}

function categoryManager(cal) {
  const nameInput = h("input", {
    class: "input input-sm grow",
    placeholder: "Category name",
    onKeyDown: (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        submit();
      }
    },
  });
  const colorInput = h("input", {
    class: "color-input",
    type: "color",
    value: cal.default_category_color,
    "aria-label": "Category colour",
  });

  function submit() {
    act("calendar/categories/add", { name: nameInput.value, color: colorInput.value });
  }

  return h(
    "div",
    { class: "card card-lg mb-6" },
    h(
      "div",
      { class: "row-between mb-3" },
      h("h3", { class: "h3" }, "Categories"),
      h(
        "button",
        {
          class: "icon-btn",
          "aria-label": cal.show_category_form ? "Close category form" : "Add category",
          onClick: () => act("calendar/categories/form"),
        },
        icon(cal.show_category_form ? "x" : "plus", "icon-sm"),
      ),
    ),
    cal.show_category_form
      ? h(
          "div",
          { class: "row mb-3" },
          nameInput,
          colorInput,
          h("button", { class: "btn btn-teal", "aria-label": "Save category", onClick: submit }, icon("check", "icon-sm")),
        )
      : null,
    h(
      "div",
      { class: "chip-list" },
      cal.categories.map((category) =>
        h(
          "div",
          { class: "cat-chip" },
          h("span", { class: "cat-dot", style: { backgroundColor: category.color } }),
          h("span", { class: "grow" }, category.name),
          h(
            "button",
            {
              "aria-label": `Remove ${category.name}`,
              onClick: () => act("calendar/categories/remove", { name: category.name }),
            },
            icon("x", "icon-xs"),
          ),
        ),
      ),
    ),
  );
}

function eventFormModal(cal) {
  if (!cal.show_event_form) return null;
  const editing = cal.editing_event;

  return modal({
    title: cal.editing_event_id ? "Edit Event" : "New Event",
    onClose: () => act("calendar/event-form", { open: false }),
    onSubmit: (form) => act("calendar/events/save", form),
    children: h(
      "div",
      {},
      h("label", { class: "label", for: "event-title" }, "Title"),
      h("input", {
        class: "input mb-4",
        id: "event-title",
        name: "title",
        value: editing.title,
        placeholder: "Event title",
        autofocus: true,
      }),
      h("label", { class: "label" }, "Category"),
      h(
        "div",
        { class: "mb-4" },
        selectField({
          name: "category",
          value: editing.category,
          options: [{ value: "", label: "—" }, ...cal.category_names],
        }),
      ),
      h("label", { class: "label", for: "event-date" }, "Date"),
      h("input", {
        class: "input mb-4",
        id: "event-date",
        name: "date",
        type: "date",
        value: editing.date || cal.selected_date,
      }),
      h(
        "div",
        { class: "grid grid-2 grid-tight mb-4" },
        h(
          "div",
          {},
          h("label", { class: "label", for: "event-start" }, "Start"),
          h("input", { class: "input", id: "event-start", name: "start_time", type: "time", value: editing.start_time }),
        ),
        h(
          "div",
          {},
          h("label", { class: "label", for: "event-end" }, "End"),
          h("input", { class: "input", id: "event-end", name: "end_time", type: "time", value: editing.end_time }),
        ),
      ),
      h("label", { class: "label", for: "event-notes" }, "Notes"),
      h("textarea", { class: "textarea mb-6", id: "event-notes", name: "notes", rows: "3" }, editing.notes),
    ),
    footer: h(
      "div",
      { class: "row", style: { gap: "12px" } },
      h(
        "button",
        { class: "btn btn-outline btn-flex", type: "button", onClick: () => act("calendar/event-form", { open: false }) },
        "Cancel",
      ),
      h("button", { class: "btn btn-primary btn-flex", type: "submit" }, "Save"),
    ),
  });
}

function eventDetailModal(cal) {
  if (!cal.show_event_detail) return null;
  const event = cal.detail_event;
  const isTaskEvent = cal.detail_event_id.startsWith("task_");
  const close = () => act("calendar/event-detail", { open: false });

  return h(
    "div",
    { class: "modal-overlay", onClick: close },
    h(
      "div",
      { class: "modal modal-sm", onClick: (e) => e.stopPropagation() },
      h(
        "div",
        { class: "row mb-2" },
        h("span", { class: "cat-dot", style: { backgroundColor: event.color } }),
        h("span", { class: "eyebrow" }, event.category),
      ),
      h("h2", { class: "h2 mb-4" }, event.title),
      h(
        "div",
        { class: "row mb-2" },
        icon("calendar", "icon-sm"),
        h("span", { class: "small mono", style: { color: "var(--heading)" } }, event.date),
      ),
      event.start_time
        ? h(
            "div",
            { class: "row mb-2" },
            icon("clock", "icon-sm"),
            h(
              "span",
              { class: "small mono", style: { color: "var(--heading)" } },
              `${event.start_time} — ${event.end_time}`,
            ),
          )
        : null,
      event.notes ? h("p", { class: "p small card-flat mt-4" }, event.notes) : null,
      h(
        "div",
        { class: "row mt-6", style: { gap: "8px" } },
        isTaskEvent
          ? h(
              "div",
              { class: "badge badge-subject btn-flex", style: { justifyContent: "center", padding: "10px" } },
              "Task event",
            )
          : h(
              "button",
              {
                class: "btn btn-primary btn-flex",
                onClick: () => act("calendar/event-form", { open: true, event_id: cal.detail_event_id }),
              },
              icon("pencil", "icon-sm"),
              "Edit",
            ),
        h(
          "button",
          {
            class: ["btn", isTaskEvent ? "btn-outline" : "btn-danger-outline"],
            "aria-label": "Delete event",
            onClick: () => act("calendar/events/delete", { event_id: cal.detail_event_id }),
          },
          icon("trash-2", "icon-sm"),
        ),
        h("button", { class: "btn btn-outline", onClick: close }, "Close"),
      ),
    ),
  );
}

export function calendarPage(state) {
  const cal = state.calendar;
  const feedback = banner(cal.feedback);
  const views = { month: monthView, week: weekView, day: dayView };
  const renderView = views[cal.view_mode] || monthView;

  return h(
    "div",
    {},
    feedback && h("div", { class: "mb-4" }, feedback),
    h(
      "div",
      { class: "row-between mb-4" },
      h(
        "div",
        {},
        h("h1", { class: "h1" }, "Calendar"),
        h("p", { class: "p small muted mono mt-2" }, cal.header_label),
      ),
      h(
        "div",
        { class: "row" },
        h(
          "button",
          {
            class: "btn btn-outline btn-sm",
            "aria-label": "Previous",
            onClick: () => act("calendar/navigate", { direction: "prev" }),
          },
          icon("chevron-left", "icon-sm"),
        ),
        h(
          "button",
          { class: "btn btn-outline btn-sm", onClick: () => act("calendar/navigate", { direction: "today" }) },
          "Today",
        ),
        h(
          "button",
          {
            class: "btn btn-outline btn-sm",
            "aria-label": "Next",
            onClick: () => act("calendar/navigate", { direction: "next" }),
          },
          icon("chevron-right", "icon-sm"),
        ),
      ),
    ),
    h(
      "div",
      { class: "row mb-6" },
      ["month", "week", "day"].map((mode) =>
        h(
          "button",
          {
            class: ["btn btn-sm", cal.view_mode === mode ? "btn-primary" : "btn-outline"],
            onClick: () => act("calendar/view", { view: mode }),
          },
          mode.charAt(0).toUpperCase() + mode.slice(1),
        ),
      ),
    ),
    categoryManager(cal),
    renderView(cal),
    eventFormModal(cal),
    eventDetailModal(cal),
  );
}
