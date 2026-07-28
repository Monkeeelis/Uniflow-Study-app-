import reflex as rx
from typing import TypedDict
import uuid
import datetime
import calendar as pycal
import logging


GRID_START_HOUR = 6
GRID_HOURS = 18  # 6am -> midnight
HOUR_HEIGHT_PX = 48
DEFAULT_TASK_DURATION_MIN = 60


class Event(TypedDict):
    id: str
    title: str
    category: str
    date: str
    start_time: str
    end_time: str
    notes: str
    color: str


class TimedBlock(TypedDict):
    id: str
    title: str
    category: str
    color: str
    start_time: str
    end_time: str
    duration_label: str
    notes: str
    top: str
    height: str


class CalendarCategory(TypedDict):
    name: str
    color: str


def _parse_hm(t: str) -> tuple[int, int] | None:
    if not t:
        return None
    try:
        parts = t.split(":")
        if len(parts) != 2:
            return None
        hour, minute = int(parts[0]), int(parts[1])
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            return None
        return hour, minute
    except (TypeError, ValueError) as e:
        logging.exception(f"Error parsing time value: {e}")
        return None


def _format_hm(total_min: int) -> str:
    total_min = max(0, min(24 * 60 - 1, total_min))
    h, m = divmod(total_min, 60)
    return f"{h:02d}:{m:02d}"


def _format_duration_label(minutes: int) -> str:
    if minutes <= 0:
        return ""
    h, m = divmod(minutes, 60)
    if h > 0 and m > 0:
        return f"{h}h {m}m"
    if h > 0:
        return f"{h}h"
    return f"{m}m"


class CalendarState(rx.State):
    events: list[Event] = []
    categories: list[CalendarCategory] = [
        {"name": "Class", "color": "#b45309"},
        {"name": "Study", "color": "#0d9488"},
        {"name": "Exam", "color": "#dc2626"},
        {"name": "Personal", "color": "#7c3aed"},
    ]
    view_mode: str = "month"
    current_year: int = datetime.date.today().year
    current_month: int = datetime.date.today().month
    current_day: int = datetime.date.today().day

    show_event_form: bool = False
    editing_event_id: str = ""
    selected_date: str = ""

    show_category_form: bool = False
    new_category_name: str = ""
    new_category_color: str = "#b45309"

    show_event_detail: bool = False
    detail_event_id: str = ""

    feedback_message: str = ""
    feedback_kind: str = ""

    def _set_feedback(self, message: str, kind: str = "info"):
        self.feedback_message = message
        self.feedback_kind = kind

    @rx.event
    def clear_feedback(self):
        self.feedback_message = ""
        self.feedback_kind = ""

    @rx.event
    def set_view(self, view: str):
        if view not in ("month", "week", "day"):
            return rx.toast(
                "Unknown calendar view.", duration=2500, close_button=True
            )
        self.view_mode = view
        self._set_feedback(f"Showing {view} view.", "info")

    @rx.event
    def prev_period(self):
        if self.view_mode == "month":
            if self.current_month == 1:
                self.current_month = 12
                self.current_year -= 1
            else:
                self.current_month -= 1
        elif self.view_mode == "week":
            d = datetime.date(
                self.current_year, self.current_month, self.current_day
            )
            d = d - datetime.timedelta(days=7)
            self.current_year, self.current_month, self.current_day = (
                d.year,
                d.month,
                d.day,
            )
        else:
            d = datetime.date(
                self.current_year, self.current_month, self.current_day
            )
            d = d - datetime.timedelta(days=1)
            self.current_year, self.current_month, self.current_day = (
                d.year,
                d.month,
                d.day,
            )
        self._set_feedback(f"Moved to {self.header_label}.", "info")

    @rx.event
    def next_period(self):
        if self.view_mode == "month":
            if self.current_month == 12:
                self.current_month = 1
                self.current_year += 1
            else:
                self.current_month += 1
        elif self.view_mode == "week":
            d = datetime.date(
                self.current_year, self.current_month, self.current_day
            )
            d = d + datetime.timedelta(days=7)
            self.current_year, self.current_month, self.current_day = (
                d.year,
                d.month,
                d.day,
            )
        else:
            d = datetime.date(
                self.current_year, self.current_month, self.current_day
            )
            d = d + datetime.timedelta(days=1)
            self.current_year, self.current_month, self.current_day = (
                d.year,
                d.month,
                d.day,
            )
        self._set_feedback(f"Moved to {self.header_label}.", "info")

    @rx.event
    def go_today(self):
        t = datetime.date.today()
        self.current_year, self.current_month, self.current_day = (
            t.year,
            t.month,
            t.day,
        )
        self._set_feedback("Showing today.", "info")

    @rx.event
    def open_new_event(self, date_str: str):
        chosen_date = date_str or datetime.date.today().isoformat()
        self.selected_date = chosen_date
        self.editing_event_id = ""
        self.show_event_detail = False
        self.show_event_form = True
        self._set_feedback(f"Ready to add an event on {chosen_date}.", "info")

    @rx.event
    def open_edit_event(self, event_id: str):
        if event_id.startswith("task_"):
            self._set_feedback(
                "Task events are managed from Tasks and cannot be edited here.",
                "warning",
            )
            return rx.toast(
                "Edit the original task from the Tasks page.",
                duration=3000,
                close_button=True,
            )
        for e in self.events:
            if e["id"] == event_id:
                self.selected_date = e["date"]
                self.editing_event_id = event_id
                self.show_event_form = True
                self.show_event_detail = False
                self._set_feedback(f"Editing event: {e['title']}", "info")
                return
        self._set_feedback("That event is no longer available.", "warning")
        return rx.toast(
            "That event could not be found.", duration=2500, close_button=True
        )

    @rx.event
    def close_event_form(self):
        self.show_event_form = False
        self.editing_event_id = ""

    @rx.event
    def submit_event(self, form_data: dict):
        title = form_data.get("title", "").strip()
        date_value = form_data.get("date", "").strip() or self.selected_date
        if not title:
            self._set_feedback("Please enter an event title.", "warning")
            return rx.toast(
                "Please enter an event title.", duration=2500, close_button=True
            )
        if not date_value:
            self._set_feedback("Please choose a date for the event.", "warning")
            return rx.toast(
                "Please choose a date.", duration=2500, close_button=True
            )
        try:
            datetime.date.fromisoformat(date_value)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error validating event date: {e}")
            self._set_feedback("Please choose a valid date.", "warning")
            return rx.toast(
                "Please choose a valid date.",
                duration=2500,
                close_button=True,
            )
        start_time = form_data.get("start_time", "").strip()
        end_time = form_data.get("end_time", "").strip()
        if start_time and _parse_hm(start_time) is None:
            self._set_feedback("Please choose a valid start time.", "warning")
            return rx.toast(
                "Please choose a valid start time.",
                duration=2500,
                close_button=True,
            )
        if end_time and _parse_hm(end_time) is None:
            self._set_feedback("Please choose a valid end time.", "warning")
            return rx.toast(
                "Please choose a valid end time.",
                duration=2500,
                close_button=True,
            )
        category = form_data.get("category", "").strip()
        color = "#b45309"
        for c in self.categories:
            if c["name"] == category:
                color = c["color"]
                break
        was_editing = bool(self.editing_event_id)
        saved_id = self.editing_event_id or str(uuid.uuid4())
        saved_event: Event = {
            "id": saved_id,
            "title": title,
            "category": category,
            "date": date_value,
            "start_time": start_time,
            "end_time": end_time,
            "notes": form_data.get("notes", "").strip(),
            "color": color,
        }
        if was_editing:
            updated = False
            for i, event in enumerate(self.events):
                if event["id"] == saved_id:
                    self.events[i] = saved_event
                    updated = True
                    break
            if not updated:
                self._set_feedback(
                    "That event could not be updated.", "warning"
                )
                return rx.toast(
                    "That event no longer exists.",
                    duration=2500,
                    close_button=True,
                )
        else:
            self.events.append(saved_event)
        self.show_event_form = False
        self.editing_event_id = ""
        self.selected_date = date_value
        action = "updated" if was_editing else "created"
        self._set_feedback(f"Event {action}: {title}", "success")
        return rx.toast(
            f"Event {action}: {title}", duration=2500, close_button=True
        )

    @rx.event
    def delete_event(self, event_id: str):
        self.show_event_detail = False
        self.show_event_form = False
        if event_id.startswith("task_"):
            self._set_feedback(
                "Task events cannot be deleted from Calendar.", "warning"
            )
            return rx.toast(
                "Delete the original task from the Tasks page.",
                duration=3000,
                close_button=True,
            )
        removed: Event | None = None
        remaining: list[Event] = []
        for event in self.events:
            if event["id"] == event_id:
                removed = event
            else:
                remaining.append(event)
        self.events = remaining
        if removed is None:
            self._set_feedback("That event was already removed.", "warning")
            return rx.toast(
                "That event could not be found.",
                duration=2500,
                close_button=True,
            )
        self._set_feedback(f"Deleted event: {removed['title']}", "success")
        return rx.toast(
            f"Deleted event: {removed['title']}",
            duration=2500,
            close_button=True,
        )

    @rx.event
    def open_event_detail(self, event_id: str):
        self.detail_event_id = event_id
        self.show_event_detail = True

    @rx.event
    def close_event_detail(self):
        self.show_event_detail = False
        self.detail_event_id = ""

    @rx.event
    def toggle_category_form(self):
        self.show_category_form = not self.show_category_form

    @rx.event
    def set_new_category_name(self, val: str):
        self.new_category_name = val

    @rx.event
    def set_new_category_color(self, val: str):
        self.new_category_color = val

    @rx.event
    def add_category(self):
        name = self.new_category_name.strip()
        if not name:
            self._set_feedback("Enter a category name first.", "warning")
            return rx.toast(
                "Enter a category name first.", duration=2500, close_button=True
            )
        for category in self.categories:
            if category["name"].casefold() == name.casefold():
                self._set_feedback("That category already exists.", "warning")
                return rx.toast(
                    "That category already exists.",
                    duration=2500,
                    close_button=True,
                )
        self.categories.append({"name": name, "color": self.new_category_color})
        self.new_category_name = ""
        self.new_category_color = "#b45309"
        self.show_category_form = False
        self._set_feedback(f"Category added: {name}", "success")
        return rx.toast(
            f"Category added: {name}", duration=2500, close_button=True
        )

    @rx.event
    def remove_category(self, name: str):
        found = False
        remaining: list[CalendarCategory] = []
        for category in self.categories:
            if category["name"] == name:
                found = True
            else:
                remaining.append(category)
        self.categories = remaining
        if not found:
            self._set_feedback("That category was already removed.", "warning")
            return rx.toast(
                "That category was not found.", duration=2500, close_button=True
            )
        self._set_feedback(
            f"Category removed: {name}. Existing events keep their colors.",
            "success",
        )
        return rx.toast(
            f"Removed category: {name}", duration=2500, close_button=True
        )

    @rx.var
    def month_name(self) -> str:
        return pycal.month_name[self.current_month]

    @rx.var
    def header_label(self) -> str:
        if self.view_mode == "month":
            return f"{pycal.month_name[self.current_month]} {self.current_year}"
        if self.view_mode == "week":
            d = datetime.date(
                self.current_year, self.current_month, self.current_day
            )
            start = d - datetime.timedelta(days=d.weekday())
            end = start + datetime.timedelta(days=6)
            return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
        d = datetime.date(
            self.current_year, self.current_month, self.current_day
        )
        return d.strftime("%A, %B %d, %Y")

    @rx.var
    def category_names(self) -> list[str]:
        return [c["name"] for c in self.categories]

    async def _get_task_events(self) -> list[Event]:
        """Convert calendar-enabled tasks into Event-like dicts. If the task
        has a due_time, use it as start and infer a default duration so it
        occupies a meaningful block on the day/week views. All-day tasks
        (no due_time) are still surfaced but without positioning."""
        from reflexuniflow.states.task_state import TaskState

        ts = await self.get_state(TaskState)
        result: list[Event] = []
        for t in ts.tasks:
            if not t["show_on_calendar"] or not t["due_date"]:
                continue
            start = t["due_time"] or ""
            end = ""
            if start:
                parsed = _parse_hm(start)
                if parsed is not None:
                    sh, sm = parsed
                    end_min = sh * 60 + sm + DEFAULT_TASK_DURATION_MIN
                    end = _format_hm(end_min)
            color = "#0d9488" if not t["completed"] else "#8b6f47"
            result.append(
                Event(
                    id=f"task_{t['id']}",
                    title=f"📝 {t['title']}",
                    category=t["subject"] or t["category"] or "Task",
                    date=t["due_date"],
                    start_time=start,
                    end_time=end,
                    notes=t["notes"],
                    color=color,
                )
            )
        return result

    @rx.var
    async def all_events(self) -> list[Event]:
        task_events = await self._get_task_events()
        return self.events + task_events

    @rx.var
    async def month_cells(self) -> list[dict[str, str]]:
        first_day = datetime.date(self.current_year, self.current_month, 1)
        start_weekday = first_day.weekday()
        days_in_month = pycal.monthrange(self.current_year, self.current_month)[
            1
        ]
        cells: list[dict[str, str]] = []
        for i in range(start_weekday):
            cells.append(
                {
                    "date": "",
                    "day": "",
                    "in_month": "false",
                    "is_today": "false",
                }
            )
        today = datetime.date.today()
        for d in range(1, days_in_month + 1):
            date_obj = datetime.date(self.current_year, self.current_month, d)
            cells.append(
                {
                    "date": date_obj.isoformat(),
                    "day": str(d),
                    "in_month": "true",
                    "is_today": "true" if date_obj == today else "false",
                }
            )
        while len(cells) % 7 != 0:
            cells.append(
                {
                    "date": "",
                    "day": "",
                    "in_month": "false",
                    "is_today": "false",
                }
            )
        return cells

    @rx.var
    async def events_by_date(self) -> dict[str, list[Event]]:
        result: dict[str, list[Event]] = {}
        for e in await self.all_events:
            result.setdefault(e["date"], []).append(e)
        for k in result:
            result[k].sort(key=lambda x: x["start_time"] or "99:99")
        return result

    def _to_timed_block(self, e: Event) -> TimedBlock | None:
        parsed = _parse_hm(e["start_time"])
        if parsed is None:
            return None
        sh, sm = parsed
        start_min = sh * 60 + sm
        end_parsed = _parse_hm(e["end_time"])
        if end_parsed is not None:
            eh, em = end_parsed
            end_min = eh * 60 + em
            if end_min <= start_min:
                end_min = start_min + 30
        else:
            end_min = start_min + DEFAULT_TASK_DURATION_MIN

        # Keep blocks inside the single-day grid, including events that begin
        # before 06:00 or run past midnight.
        day_end_min = 24 * 60
        end_min = min(day_end_min, end_min)
        grid_start_min = GRID_START_HOUR * 60
        visible_start_min = max(0, start_min)
        visible_end_min = max(visible_start_min + 30, end_min)
        duration = max(30, visible_end_min - visible_start_min)
        top_px = max(
            0.0,
            (visible_start_min - grid_start_min) * (HOUR_HEIGHT_PX / 60),
        )
        if visible_start_min < grid_start_min:
            duration = max(30, visible_end_min - grid_start_min)
        height_px = max(28.0, duration * (HOUR_HEIGHT_PX / 60))
        return TimedBlock(
            id=e["id"],
            title=e["title"],
            category=e["category"],
            color=e["color"],
            start_time=e["start_time"],
            end_time=_format_hm(end_min),
            duration_label=_format_duration_label(
                int(visible_end_min - visible_start_min)
            ),
            notes=e["notes"],
            top=f"{top_px:.1f}",
            height=f"{height_px:.1f}",
        )

    @rx.var
    async def positioned_events_by_date(
        self,
    ) -> dict[str, list[TimedBlock]]:
        result: dict[str, list[TimedBlock]] = {}
        for e in await self.all_events:
            block = self._to_timed_block(e)
            if block is None:
                continue
            result.setdefault(e["date"], []).append(block)
        for k in result:
            result[k].sort(key=lambda x: x["top"])
        return result

    @rx.var
    async def all_day_events_by_date(self) -> dict[str, list[Event]]:
        """Events with no start_time — shown in the 'all day' strip."""
        result: dict[str, list[Event]] = {}
        for e in await self.all_events:
            if not e["start_time"]:
                result.setdefault(e["date"], []).append(e)
        return result

    @rx.var
    def hour_labels(self) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        for i in range(GRID_HOURS):
            h = GRID_START_HOUR + i
            display_h = h % 12 or 12
            ampm = "AM" if h < 12 else "PM"
            result.append(
                {
                    "hour": str(h),
                    "label": f"{display_h} {ampm}",
                    "military": f"{h:02d}:00",
                }
            )
        return result

    @rx.var
    def grid_height_px(self) -> str:
        return f"{GRID_HOURS * HOUR_HEIGHT_PX}"

    @rx.var
    def hour_height_px(self) -> str:
        return f"{HOUR_HEIGHT_PX}"

    @rx.var
    async def week_days(self) -> list[dict[str, str]]:
        d = datetime.date(
            self.current_year, self.current_month, self.current_day
        )
        start = d - datetime.timedelta(days=d.weekday())
        today = datetime.date.today()
        result: list[dict[str, str]] = []
        for i in range(7):
            dd = start + datetime.timedelta(days=i)
            result.append(
                {
                    "date": dd.isoformat(),
                    "label": dd.strftime("%a %d"),
                    "is_today": "true" if dd == today else "false",
                }
            )
        return result

    @rx.var
    async def day_date_str(self) -> str:
        return datetime.date(
            self.current_year, self.current_month, self.current_day
        ).isoformat()

    @rx.var
    async def detail_event(self) -> Event:
        for e in await self.all_events:
            if e["id"] == self.detail_event_id:
                return e
        return Event(
            id="",
            title="",
            category="",
            date="",
            start_time="",
            end_time="",
            notes="",
            color="#b45309",
        )

    @rx.var
    async def editing_event(self) -> Event:
        for e in self.events:
            if e["id"] == self.editing_event_id:
                return e
        return Event(
            id="",
            title="",
            category="",
            date=self.selected_date,
            start_time="",
            end_time="",
            notes="",
            color="#b45309",
        )
