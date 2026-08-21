// Tasks page: the filtered/sorted list plus the create/edit modal.
// Filtering, sorting and the active/completed split all happen server-side
// (see services/tasks.py) — this file only renders what `state.tasks` gives it.

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { act, navigate } from "../state.js";
import { banner, emptyState, modal, priorityBadge, selectField } from "../ui.js";

function taskRow(task) {
  return h(
    "div",
    { class: "task-row" },
    h(
      "button",
      {
        class: ["task-check", task.completed && "is-done"],
        "aria-label": task.completed ? "Mark as not done" : "Mark as done",
        onClick: () => act("tasks/toggle", { task_id: task.id }),
      },
      icon(task.completed ? "circle-check" : "circle", "icon-lg"),
    ),
    h(
      "div",
      { class: "grow" },
      h(
        "div",
        { class: "row row-wrap", style: { gap: "12px" } },
        h("p", { class: ["p task-title", task.completed && "is-done"] }, task.title),
        priorityBadge(task.priority),
      ),
      h(
        "div",
        { class: "task-meta" },
        task.subject && h("span", { class: "badge badge-subject" }, task.subject),
        task.category && h("span", {}, task.category),
        task.due_date &&
          h("span", { class: "mono" }, `📅 ${task.due_date}${task.due_time ? ` ${task.due_time}` : ""}`),
        task.show_on_calendar && h("span", { class: "tiny muted" }, "· on calendar"),
      ),
      task.notes && h("p", { class: "p small muted mt-2" }, task.notes),
    ),
    h(
      "div",
      { class: "row", style: { gap: "4px", flex: "none" } },
      !task.completed &&
        h(
          "button",
          {
            class: "icon-btn",
            "aria-label": "Start a focus session for this task",
            title: "Start a focus session",
            onClick: async () => {
              await act("focus/mode", { mode: "timer" });
              navigate("/focus");
            },
          },
          icon("timer", "icon-sm"),
        ),
      h(
        "button",
        {
          class: "icon-btn",
          "aria-label": "Edit task",
          onClick: () => act("tasks/form", { open: true, task_id: task.id }),
        },
        icon("pencil", "icon-sm"),
      ),
      h(
        "button",
        {
          class: "icon-btn icon-btn-danger",
          "aria-label": "Delete task",
          onClick: () => act("tasks/delete", { task_id: task.id }),
        },
        icon("trash-2", "icon-sm"),
      ),
    ),
  );
}

function taskFormModal(state) {
  const { tasks, onboarding } = state;
  if (!tasks.show_form) return null;
  const editing = tasks.editing_task;

  return modal({
    title: tasks.editing_id ? "Edit Task" : "New Task",
    onClose: () => act("tasks/form", { open: false }),
    onSubmit: (form) => act("tasks/save", form),
    children: h(
      "div",
      {},
      h("label", { class: "label", for: "task-title" }, "Title"),
      h("input", {
        class: "input mb-4",
        id: "task-title",
        name: "title",
        value: editing.title,
        placeholder: "What do you need to do?",
        autofocus: true,
      }),
      h(
        "div",
        { class: "grid grid-1-2 mb-4" },
        h(
          "div",
          {},
          h("label", { class: "label" }, "Subject"),
          selectField({
            name: "subject",
            value: editing.subject,
            options: [{ value: "", label: "—" }, ...onboarding.subjects],
          }),
        ),
        h(
          "div",
          {},
          h("label", { class: "label", for: "task-category" }, "Category"),
          h("input", {
            class: "input",
            id: "task-category",
            name: "category",
            value: editing.category,
            placeholder: "e.g. Assignment",
          }),
        ),
      ),
      h(
        "div",
        { class: "grid grid-1-2 mb-4" },
        h(
          "div",
          {},
          h("label", { class: "label", for: "task-date" }, "Due date"),
          h("input", { class: "input", id: "task-date", name: "due_date", type: "date", value: editing.due_date }),
        ),
        h(
          "div",
          {},
          h("label", { class: "label", for: "task-time" }, "Due time"),
          h("input", { class: "input", id: "task-time", name: "due_time", type: "time", value: editing.due_time }),
        ),
      ),
      h("label", { class: "label" }, "Priority"),
      h(
        "div",
        { class: "radio-group mb-4" },
        tasks.priority_options.map((option) =>
          h(
            "label",
            { class: "radio-option" },
            h("input", {
              type: "radio",
              name: "priority",
              value: option,
              checked: editing.priority === option,
            }),
            h("span", {}, option),
          ),
        ),
      ),
      h("label", { class: "label", for: "task-notes" }, "Notes"),
      h("textarea", {
        class: "textarea mb-4",
        id: "task-notes",
        name: "notes",
        rows: "3",
        placeholder: "Optional notes...",
      }, editing.notes),
      h(
        "label",
        { class: "check-row mb-6" },
        h("input", {
          type: "checkbox",
          name: "show_on_calendar",
          value: "true",
          checked: editing.show_on_calendar,
        }),
        h("span", {}, "Show on calendar"),
      ),
    ),
    footer: h(
      "div",
      { class: "row", style: { gap: "12px" } },
      h(
        "button",
        { class: "btn btn-outline btn-flex", type: "button", onClick: () => act("tasks/form", { open: false }) },
        "Cancel",
      ),
      h("button", { class: "btn btn-primary btn-flex", type: "submit" }, "Save"),
    ),
  });
}

export function tasksPage(state) {
  const { tasks } = state;
  const feedback = banner(tasks.feedback);

  return h(
    "div",
    {},
    feedback && h("div", { class: "mb-4" }, feedback),
    h(
      "div",
      { class: "row-between mb-6" },
      h(
        "div",
        {},
        h("h1", { class: "h1" }, "Tasks"),
        h("p", { class: "p small muted mono mt-2" }, `${tasks.total_count} total · ${tasks.completed_count} done`),
      ),
      h(
        "button",
        { class: "btn btn-primary", onClick: () => act("tasks/form", { open: true }) },
        icon("plus"),
        "New Task",
      ),
    ),
    h(
      "div",
      { class: "grid grid-tight grid-sm-3 mb-6" },
      h(
        "div",
        {},
        h("label", { class: "label label-sm" }, "Subject"),
        selectField({
          value: tasks.filter_subject,
          options: tasks.subject_options,
          small: true,
          onChange: (value) => act("tasks/view", { filter_subject: value }),
        }),
      ),
      h(
        "div",
        {},
        h("label", { class: "label label-sm" }, "Priority"),
        selectField({
          value: tasks.filter_priority,
          options: tasks.priority_filters,
          small: true,
          onChange: (value) => act("tasks/view", { filter_priority: value }),
        }),
      ),
      h(
        "div",
        {},
        h("label", { class: "label label-sm" }, "Sort by"),
        selectField({
          value: tasks.sort_by,
          options: [
            { value: "due_date", label: "Due date" },
            { value: "priority", label: "Priority" },
            { value: "title", label: "Title" },
          ],
          small: true,
          onChange: (value) => act("tasks/view", { sort_by: value }),
        }),
      ),
    ),
    tasks.active.length
      ? h("div", { class: "stack" }, tasks.active.map(taskRow))
      : emptyState("clipboard-list", "No active tasks. Add one to get started!"),
    tasks.completed_count > 0
      ? h(
          "div",
          {},
          h(
            "button",
            { class: "ghost-link mt-6 mb-3", onClick: () => act("tasks/show-completed/toggle") },
            h("span", {}, tasks.show_completed ? "Hide completed" : "Show completed"),
            icon(tasks.show_completed ? "chevron-up" : "chevron-down", "icon-sm"),
          ),
          tasks.show_completed ? h("div", { class: "stack" }, tasks.completed.map(taskRow)) : null,
        )
      : null,
    taskFormModal(state),
  );
}
