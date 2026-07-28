import reflex as rx
import datetime


class StatsState(rx.State):
    @rx.var
    async def streak_days(self) -> int:
        from reflexuniflow.states.focus_state import FocusState
        from reflexuniflow.states.task_state import TaskState

        fs = await self.get_state(FocusState)
        ts = await self.get_state(TaskState)
        active_dates: set[str] = set()
        for s in fs.sessions:
            active_dates.add(s["date"])
        for t in ts.tasks:
            if t["completed"] and t["due_date"]:
                active_dates.add(t["due_date"])
        if not active_dates:
            return 0
        streak = 0
        d = datetime.date.today()
        while d.isoformat() in active_dates:
            streak += 1
            d = d - datetime.timedelta(days=1)
        if streak == 0:
            y = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
            if y in active_dates:
                streak = 1
                d = datetime.date.today() - datetime.timedelta(days=2)
                while d.isoformat() in active_dates:
                    streak += 1
                    d = d - datetime.timedelta(days=1)
        return streak

    @rx.var
    async def motivation_message(self) -> str:
        streak = await self.streak_days
        if streak == 0:
            return "Start a session today to begin your streak!"
        if streak < 3:
            return f"Great start — {streak} day streak. Keep it going!"
        if streak < 7:
            return f"🔥 {streak} days in a row! You're building momentum."
        return f"🔥🔥 {streak} day streak! You're on fire."
