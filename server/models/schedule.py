from datetime import datetime

from server.dto.schedule import Schedule


class TelegramSchedule:
    schedule: Schedule
    course_name: str
    lesson_name: str
    due_time: datetime

    def __init__(self, schedule: Schedule):
        self.schedule = schedule