import reflex as rx


class OnboardingState(rx.State):
    completed: bool = False
    step: int = 0
    name: str = ""
    year_level: str = ""
    subjects: list[str] = []
    subject_input: str = ""
    pomodoro_work: int = 25
    pomodoro_break: int = 5
    notifications_enabled: bool = True

    year_options: list[str] = [
        "High School",
        "Year 11",
        "Year 12",
        "Undergraduate",
        "Postgraduate",
        "Other",
    ]

    @rx.event
    def next_step(self):
        self.step += 1

    @rx.event
    def prev_step(self):
        if self.step > 0:
            self.step -= 1

    @rx.event
    def set_name(self, val: str):
        self.name = val

    @rx.event
    def set_year_level(self, val: str):
        self.year_level = val

    @rx.event
    def set_subject_input(self, val: str):
        self.subject_input = val

    @rx.event
    def add_subject(self):
        v = self.subject_input.strip()
        if v and v not in self.subjects:
            self.subjects.append(v)
        self.subject_input = ""

    @rx.event
    def remove_subject(self, s: str):
        self.subjects = [x for x in self.subjects if x != s]

    @rx.event
    def set_pomodoro_work(self, val):
        try:
            self.pomodoro_work = max(1, int(float(val)))
        except (ValueError, TypeError):
            self.pomodoro_work = 25

    @rx.event
    def set_pomodoro_break(self, val):
        try:
            self.pomodoro_break = max(1, int(float(val)))
        except (ValueError, TypeError):
            self.pomodoro_break = 5

    @rx.event
    def toggle_notifications(self):
        self.notifications_enabled = not self.notifications_enabled

    @rx.event
    def finish(self):
        self.completed = True
        return rx.redirect("/dashboard")

    @rx.event
    def check_onboarding(self):
        if not self.completed:
            return rx.redirect("/")
