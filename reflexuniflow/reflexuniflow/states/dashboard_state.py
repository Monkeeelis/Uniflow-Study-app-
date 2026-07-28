import reflex as rx
import asyncio
import datetime
import uuid
from typing import TypedDict


class DashboardStudySession(TypedDict):
    id: str
    duration_seconds: int
    date: str
    started_at: str
    ended_at: str


QUOTES: list[dict[str, str]] = [
    {
        "text": "The secret of getting ahead is getting started.",
        "author": "Mark Twain",
    },
    {
        "text": "Success is the sum of small efforts, repeated day in and day out.",
        "author": "Robert Collier",
    },
    {
        "text": "Don't watch the clock; do what it does. Keep going.",
        "author": "Sam Levenson",
    },
    {
        "text": "The expert in anything was once a beginner.",
        "author": "Helen Hayes",
    },
    {
        "text": "Small daily improvements are the key to staggering long-term results.",
        "author": "Robin Sharma",
    },
    {
        "text": "You don't have to be great to start, but you have to start to be great.",
        "author": "Zig Ziglar",
    },
    {
        "text": "Focus on being productive instead of busy.",
        "author": "Tim Ferriss",
    },
    {
        "text": "Learning never exhausts the mind.",
        "author": "Leonardo da Vinci",
    },
    {
        "text": "The beautiful thing about learning is that no one can take it away from you.",
        "author": "B.B. King",
    },
    {
        "text": "Discipline is the bridge between goals and accomplishment.",
        "author": "Jim Rohn",
    },
    {
        "text": "Study while others are sleeping; work while others are loafing.",
        "author": "William A. Ward",
    },
    {
        "text": "Every accomplishment starts with the decision to try.",
        "author": "John F. Kennedy",
    },
    {
        "text": "It always seems impossible until it's done.",
        "author": "Nelson Mandela",
    },
    {
        "text": "The future depends on what you do today.",
        "author": "Mahatma Gandhi",
    },
    {
        "text": "Push yourself, because no one else is going to do it for you.",
        "author": "Anonymous",
    },
]


class DashboardState(rx.State):
    quote_index: int = 0

    timer_running: bool = False
    timer_seconds: int = 0
    _tick_id: int = 0
    _timer_started_at: str = ""

    dashboard_sessions: list[DashboardStudySession] = []

    @rx.event
    def next_quote(self):
        self.quote_index = (self.quote_index + 1) % len(QUOTES)

    @rx.var
    def quote_text(self) -> str:
        return QUOTES[self.quote_index % len(QUOTES)]["text"]

    @rx.var
    def quote_author(self) -> str:
        return QUOTES[self.quote_index % len(QUOTES)]["author"]

    @rx.var
    def display_time(self) -> str:
        total = self.timer_seconds
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @rx.var
    def timer_minutes_pending(self) -> int:
        return self.timer_seconds // 60

    @rx.event
    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            if self._timer_started_at == "" or self.timer_seconds == 0:
                self._timer_started_at = datetime.datetime.now().isoformat()
            self._tick_id += 1
            return DashboardState.timer_tick(self._tick_id)

    @rx.event
    def pause_timer(self):
        self.timer_running = False

    @rx.event
    async def stop_and_save(self):
        seconds = self.timer_seconds
        self.timer_running = False
        if seconds <= 0:
            self.timer_seconds = 0
            self._timer_started_at = ""
            return
        now_iso = datetime.datetime.now().isoformat()
        started = self._timer_started_at or now_iso
        new_session: DashboardStudySession = {
            "id": str(uuid.uuid4()),
            "duration_seconds": seconds,
            "date": datetime.date.today().isoformat(),
            "started_at": started,
            "ended_at": now_iso,
        }
        self.dashboard_sessions = self.dashboard_sessions + [new_session]

        from reflexuniflow.states.notification_state import NotificationState

        notif = await self.get_state(NotificationState)
        m, s = divmod(seconds, 60)
        notif.add(
            "Study session saved!",
            f"You studied for {m}m {s}s. Nice work.",
            "success",
        )
        self.timer_seconds = 0
        self._timer_started_at = ""
        return rx.toast(
            f"Saved {m}m {s}s of study time.",
            duration=3500,
            close_button=True,
        )

    @rx.event
    def reset_timer(self):
        self.timer_running = False
        self.timer_seconds = 0
        self._timer_started_at = ""

    @rx.event
    def delete_dashboard_session(self, session_id: str):
        self.dashboard_sessions = [
            s for s in self.dashboard_sessions if s["id"] != session_id
        ]

    @rx.var
    def dashboard_seconds_today(self) -> int:
        today = datetime.date.today().isoformat()
        return sum(
            s["duration_seconds"]
            for s in self.dashboard_sessions
            if s["date"] == today
        )

    @rx.var
    def dashboard_seconds_all(self) -> int:
        return sum(s["duration_seconds"] for s in self.dashboard_sessions)

    @rx.var
    def dashboard_sessions_today_count(self) -> int:
        today = datetime.date.today().isoformat()
        return len([s for s in self.dashboard_sessions if s["date"] == today])

    @rx.var
    def dashboard_today_display(self) -> str:
        total = self.dashboard_seconds_today
        h, rem = divmod(total, 3600)
        m, _ = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    @rx.var
    def dashboard_all_display(self) -> str:
        total = self.dashboard_seconds_all
        h, rem = divmod(total, 3600)
        m, _ = divmod(rem, 60)
        return f"{h}h {m}m"

    @rx.var
    def recent_dashboard_sessions(self) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for s in list(reversed(self.dashboard_sessions))[:5]:
            secs = s["duration_seconds"]
            h, rem = divmod(secs, 3600)
            m, sec = divmod(rem, 60)
            if h > 0:
                dur = f"{h}h {m}m {sec}s"
            elif m > 0:
                dur = f"{m}m {sec}s"
            else:
                dur = f"{sec}s"
            out.append(
                {
                    "id": s["id"],
                    "date": s["date"],
                    "duration": dur,
                }
            )
        return out

    @rx.event(background=True)
    async def timer_tick(self, tick_id: int):
        while True:
            await asyncio.sleep(1)
            async with self:
                if not self.timer_running or tick_id != self._tick_id:
                    return
                self.timer_seconds += 1
