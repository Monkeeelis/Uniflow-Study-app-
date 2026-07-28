import reflex as rx
import datetime
from typing import TypedDict


class HeatmapCell(TypedDict):
    date: str
    label: str
    minutes: int
    level: int
    weekday: int
    is_today: str
    in_range: str


class InsightsState(rx.State):
    range_mode: str = "month"  # week, month, year

    @rx.event
    def set_range(self, mode: str):
        if mode in ("week", "month", "year"):
            self.range_mode = mode

    async def _minutes_by_date(self) -> dict[str, int]:
        from reflexuniflow.states.dashboard_state import DashboardState
        from reflexuniflow.states.focus_state import FocusState

        ds = await self.get_state(DashboardState)
        fs = await self.get_state(FocusState)
        totals: dict[str, int] = {}
        for s in ds.dashboard_sessions:
            totals[s["date"]] = totals.get(s["date"], 0) + s["duration_seconds"]
        for s in fs.sessions:
            if s["mode"] in ("pomodoro-work", "timer"):
                totals[s["date"]] = (
                    totals.get(s["date"], 0) + s["duration_seconds"]
                )
        # convert to minutes
        return {k: v // 60 for k, v in totals.items()}

    def _level_for_minutes(self, minutes: int, max_min: int) -> int:
        if minutes <= 0:
            return 0
        if max_min <= 0:
            return 1
        ratio = minutes / max_min
        if ratio < 0.25:
            return 1
        if ratio < 0.5:
            return 2
        if ratio < 0.8:
            return 3
        return 4

    @rx.var
    def days_in_range(self) -> int:
        if self.range_mode == "week":
            return 7
        if self.range_mode == "month":
            return 30
        return 371  # 53 weeks * 7 for year grid

    @rx.var
    async def heatmap_cells(self) -> list[HeatmapCell]:
        minutes_map = await self._minutes_by_date()
        today = datetime.date.today()

        if self.range_mode == "week":
            days = 7
            start = today - datetime.timedelta(days=days - 1)
            dates = [start + datetime.timedelta(days=i) for i in range(days)]
        elif self.range_mode == "month":
            days = 30
            start = today - datetime.timedelta(days=days - 1)
            dates = [start + datetime.timedelta(days=i) for i in range(days)]
        else:
            # year: 53 weeks ending this week, aligned by weekday
            weeks = 53
            end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
            start = end_of_week - datetime.timedelta(days=weeks * 7 - 1)
            dates = [
                start + datetime.timedelta(days=i) for i in range(weeks * 7)
            ]

        # compute max for scaling levels
        in_range_min = [minutes_map.get(d.isoformat(), 0) for d in dates]
        max_min = max(in_range_min) if in_range_min else 0

        out: list[HeatmapCell] = []
        for d in dates:
            iso = d.isoformat()
            mins = minutes_map.get(iso, 0)
            in_range = "true"
            if self.range_mode == "year" and d > today:
                in_range = "false"
            out.append(
                HeatmapCell(
                    date=iso,
                    label=d.strftime("%a, %b %d"),
                    minutes=mins,
                    level=self._level_for_minutes(mins, max_min)
                    if in_range == "true"
                    else 0,
                    weekday=d.weekday(),
                    is_today="true" if d == today else "false",
                    in_range=in_range,
                )
            )
        return out

    @rx.var
    async def total_minutes(self) -> int:
        cells = await self.heatmap_cells
        return sum(c["minutes"] for c in cells if c["in_range"] == "true")

    @rx.var
    async def active_days(self) -> int:
        cells = await self.heatmap_cells
        return len(
            [c for c in cells if c["minutes"] > 0 and c["in_range"] == "true"]
        )

    @rx.var
    async def average_active_minutes(self) -> int:
        active = await self.active_days
        if active == 0:
            return 0
        total = await self.total_minutes
        return total // active

    @rx.var
    async def best_day_minutes(self) -> int:
        cells = await self.heatmap_cells
        vals = [c["minutes"] for c in cells if c["in_range"] == "true"]
        return max(vals) if vals else 0

    @rx.var
    async def best_day_label(self) -> str:
        cells = await self.heatmap_cells
        best = None
        for c in cells:
            if c["in_range"] != "true":
                continue
            if best is None or c["minutes"] > best["minutes"]:
                best = c
        if best is None or best["minutes"] == 0:
            return "—"
        return best["label"]

    @rx.var
    def total_display(self) -> str:
        # depends on total_minutes but computed off same data
        return ""

    @rx.var
    async def total_display_str(self) -> str:
        total = await self.total_minutes
        h, m = divmod(total, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    @rx.var
    async def average_display_str(self) -> str:
        avg = await self.average_active_minutes
        h, m = divmod(avg, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    @rx.var
    async def best_display_str(self) -> str:
        best = await self.best_day_minutes
        if best == 0:
            return "0m"
        h, m = divmod(best, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    @rx.var
    def range_label(self) -> str:
        if self.range_mode == "week":
            return "Past 7 days"
        if self.range_mode == "month":
            return "Past 30 days"
        return "Past year"

    @rx.var
    def grid_columns_class(self) -> str:
        if self.range_mode == "week":
            return "grid grid-cols-7 gap-1.5"
        if self.range_mode == "month":
            return "grid grid-cols-10 gap-1.5"
        # year: 53 weeks — laid out row-major weekday x week
        return "grid grid-flow-col grid-rows-7 auto-cols-min gap-1"
