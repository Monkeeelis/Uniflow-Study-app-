import reflex as rx
import asyncio
import datetime
import uuid
from typing import TypedDict


class StudySession(TypedDict):
    id: str
    mode: str
    duration_seconds: int
    date: str
    completed: bool
    started_at: str
    ended_at: str


class FocusState(rx.State):
    mode: str = "pomodoro"
    running: bool = False
    # Track elapsed time in deciseconds (tenths of a second) so we can show
    # a millisecond-style display without spamming too many state updates.
    elapsed_ds: int = 0
    pomodoro_phase: str = "work"
    completed_cycles: int = 0
    total_cycles: int = 4
    timer_duration_minutes: int = 15
    sessions: list[StudySession] = []
    _tick_id: int = 0
    _session_started_at: str = ""

    @rx.var
    def elapsed_seconds(self) -> int:
        return self.elapsed_ds // 10

    @rx.var
    async def pomodoro_work_seconds(self) -> int:
        from reflexuniflow.states.onboarding_state import OnboardingState

        ob = await self.get_state(OnboardingState)
        return max(1, ob.pomodoro_work) * 60

    @rx.var
    async def pomodoro_break_seconds(self) -> int:
        from reflexuniflow.states.onboarding_state import OnboardingState

        ob = await self.get_state(OnboardingState)
        return max(1, ob.pomodoro_break) * 60

    @rx.var
    async def target_seconds(self) -> int:
        if self.mode == "pomodoro":
            if self.pomodoro_phase == "work":
                return await self.pomodoro_work_seconds
            return await self.pomodoro_break_seconds
        return max(1, self.timer_duration_minutes) * 60

    @rx.var
    async def remaining_seconds(self) -> int:
        target = await self.target_seconds
        rem = target - (self.elapsed_ds // 10)
        return rem if rem > 0 else 0

    @rx.var
    async def display_time(self) -> str:
        """Millisecond-style countdown display: MM:SS.d (tenths of a second)."""
        target_ds = (await self.target_seconds) * 10
        remaining = target_ds - self.elapsed_ds
        if remaining < 0:
            remaining = 0
        secs, tenths = divmod(remaining, 10)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}.{tenths}"
        return f"{m:02d}:{s:02d}.{tenths}"

    @rx.var
    async def elapsed_display(self) -> str:
        """Elapsed time display with tenths, useful in captions."""
        secs, tenths = divmod(self.elapsed_ds, 10)
        m, s = divmod(secs, 60)
        return f"{m:02d}:{s:02d}.{tenths}"

    @rx.var
    async def progress_percent(self) -> float:
        target_ds = (await self.target_seconds) * 10
        if target_ds <= 0:
            return 0.0
        return min(100.0, (self.elapsed_ds / target_ds) * 100.0)

    @rx.var
    def cycle_dots(self) -> list[dict[str, str]]:
        return [
            {
                "index": str(i),
                "filled": "true" if i < self.completed_cycles else "false",
            }
            for i in range(self.total_cycles)
        ]

    @rx.event
    def set_mode(self, mode: str):
        # Guard against legacy "stopwatch" mode which has been removed.
        if mode not in ("pomodoro", "timer"):
            mode = "timer"
        self.mode = mode
        self.running = False
        self.elapsed_ds = 0
        self.pomodoro_phase = "work"
        self.completed_cycles = 0
        self._session_started_at = ""

    @rx.event
    def set_timer_duration(self, val):
        try:
            self.timer_duration_minutes = max(1, int(float(val)))
        except (ValueError, TypeError):
            self.timer_duration_minutes = 15

    @rx.event
    def set_total_cycles(self, val):
        try:
            self.total_cycles = max(1, int(float(val)))
        except (ValueError, TypeError):
            self.total_cycles = 4

    @rx.event
    def start(self):
        if not self.running:
            self.running = True
            if self._session_started_at == "":
                self._session_started_at = datetime.datetime.now().isoformat()
            self._tick_id += 1
            return FocusState.tick(self._tick_id)

    @rx.event
    def pause(self):
        self.running = False

    @rx.event
    def reset_timer(self):
        self.running = False
        self.elapsed_ds = 0
        self.pomodoro_phase = "work"
        self.completed_cycles = 0
        self._session_started_at = ""

    @rx.event
    async def skip_phase(self):
        await self._advance(completed=False)

    async def _advance(self, completed: bool):
        from reflexuniflow.states.notification_state import NotificationState

        notif = await self.get_state(NotificationState)
        seconds = self.elapsed_ds // 10
        if self.mode == "pomodoro":
            if self.pomodoro_phase == "work":
                self._log_session("pomodoro-work", seconds, completed)
                self.completed_cycles += 1
                self.pomodoro_phase = "break"
                self.elapsed_ds = 0
                self._session_started_at = datetime.datetime.now().isoformat()
                notif.add(
                    "Work session complete!",
                    "Time for a break. You earned it.",
                    "success",
                )
                if self.completed_cycles >= self.total_cycles:
                    self.running = False
                    notif.add(
                        "Pomodoro set complete!",
                        f"You finished {self.total_cycles} cycles.",
                        "success",
                    )
            else:
                self._log_session("pomodoro-break", seconds, completed)
                self.pomodoro_phase = "work"
                self.elapsed_ds = 0
                self._session_started_at = datetime.datetime.now().isoformat()
                notif.add("Break over", "Back to focus!", "info")
        else:
            self._log_session("timer", seconds, completed)
            self.running = False
            self.elapsed_ds = 0
            self._session_started_at = ""
            notif.add("Timer finished!", "Nice work.", "success")

    def _log_session(self, mode: str, seconds: int, completed: bool):
        if seconds <= 0:
            return
        started = (
            self._session_started_at or datetime.datetime.now().isoformat()
        )
        self.sessions.append(
            StudySession(
                id=str(uuid.uuid4()),
                mode=mode,
                duration_seconds=seconds,
                date=datetime.date.today().isoformat(),
                completed=completed,
                started_at=started,
                ended_at=datetime.datetime.now().isoformat(),
            )
        )

    @rx.event(background=True)
    async def tick(self, tick_id: int):
        while True:
            await asyncio.sleep(0.1)
            async with self:
                if not self.running or tick_id != self._tick_id:
                    return
                self.elapsed_ds += 1
                from reflexuniflow.states.onboarding_state import OnboardingState

                ob = await self.get_state(OnboardingState)
                if self.mode == "pomodoro":
                    target_min = (
                        ob.pomodoro_work
                        if self.pomodoro_phase == "work"
                        else ob.pomodoro_break
                    )
                else:
                    target_min = self.timer_duration_minutes
                target_ds = max(1, target_min) * 600
                if self.elapsed_ds >= target_ds:
                    await self._advance(completed=True)
                    if not self.running:
                        return

    # --- summary vars ---------------------------------------------------

    @rx.var
    def total_study_seconds_today(self) -> int:
        today = datetime.date.today().isoformat()
        return sum(
            s["duration_seconds"]
            for s in self.sessions
            if s["date"] == today and s["mode"] in ("pomodoro-work", "timer")
        )

    @rx.var
    def total_study_seconds_all(self) -> int:
        return sum(
            s["duration_seconds"]
            for s in self.sessions
            if s["mode"] in ("pomodoro-work", "timer")
        )

    @rx.var
    def sessions_today(self) -> int:
        today = datetime.date.today().isoformat()
        return len(
            [
                s
                for s in self.sessions
                if s["date"] == today
                and s["mode"] in ("pomodoro-work", "timer")
            ]
        )

    @rx.var
    def study_minutes_today(self) -> int:
        return self.total_study_seconds_today // 60

    @rx.var
    def study_hours_all(self) -> str:
        total_min = self.total_study_seconds_all // 60
        h, m = divmod(total_min, 60)
        return f"{h}h {m}m"

    @rx.var
    def pomodoros_completed_today(self) -> int:
        today = datetime.date.today().isoformat()
        return len(
            [
                s
                for s in self.sessions
                if s["mode"] == "pomodoro-work"
                and s["date"] == today
                and s["completed"]
            ]
        )

    @rx.var
    def timers_completed_today(self) -> int:
        today = datetime.date.today().isoformat()
        return len(
            [
                s
                for s in self.sessions
                if s["mode"] == "timer"
                and s["date"] == today
                and s["completed"]
            ]
        )

    @rx.var
    def recent_sessions(self) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for s in list(reversed(self.sessions))[:8]:
            secs = s["duration_seconds"]
            h, rem = divmod(secs, 3600)
            m, sec = divmod(rem, 60)
            if h > 0:
                dur = f"{h}h {m}m"
            elif m > 0:
                dur = f"{m}m {sec}s"
            else:
                dur = f"{sec}s"
            label = "Pomodoro"
            if s["mode"] == "pomodoro-break":
                label = "Break"
            elif s["mode"] == "timer":
                label = "Timer"
            out.append(
                {
                    "id": s["id"],
                    "mode": label,
                    "date": s["date"],
                    "duration": dur,
                    "completed": "yes" if s["completed"] else "no",
                }
            )
        return out
