from typing import List

import requests
from pydantic import TypeAdapter

from server.core.config import settings
from server.dto.courses import Lesson
from server.dto.schedule import Schedule


class LmsService:
    def __init__(self):
        self.student_name = settings.STUDENT_NAME

    def get_detail_lesson(self, lesson_id: str) -> Lesson:
        response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/lessons/{lesson_id}/public",
            params={"student_name": self.student_name}
        )
        lesson = Lesson.model_validate(response.json())
        return lesson

    def get_due_schedule(self) -> List[Schedule] | None:
        response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/schedules/due",
            params={"student_name": self.student_name}
        )
        adapter = TypeAdapter(list[Schedule])
        try:
            schedules = adapter.validate_python(response.json())
            return [item for item in schedules if item.lesson_id is not None]
        except Exception as e:
            print('Cannot get schedules due to error:', e)

        return None