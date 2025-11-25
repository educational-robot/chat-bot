from typing import List

import requests
from pydantic import TypeAdapter

from server.core.config import settings
from server.dto.courses import Lesson
from server.dto.schedule import Schedule


class LmsService:
    def __init__(self):
        self.base_url = settings.LMS_BASE_URL
        self.student_name = settings.STUDENT_NAME

    def create_learning_schedule(self, course_id: str, lesson_id: str, day_of_week: int, time_hhmm: str):
        response = requests.post(
            url=self.base_url + f"/public/schedules",
            json={
                "student_name": self.student_name,
                "course_id": course_id,
                "lesson_id": lesson_id,
                "day_of_week": day_of_week,
                "time_hhmm": time_hhmm,
            }
        )
        return response.json()

    def get_classroom_assignment(self, classroom_id: str):
        response = requests.get(
            url=self.base_url + f"/assignments/classrooms/{classroom_id}/list",
        )
        return response.json()

    def get_student_classroom(self):
        response = requests.get(
            url=self.base_url + f"/public/student/classrooms",
            params={"student_name": self.student_name}
        )
        return response.json()

    def get_course_detail(self, course_id: str):
        response = requests.get(
            url=self.base_url + f"/public/courses/{course_id}/lessons/public",
        )
        return response.json()

    def get_student_enrolled_course(self):
        response = requests.get(
            url=self.base_url + f"/public/courses",
            params={"student_name": self.student_name}
        )
        return response.json()

    def get_student_stats(self):
        response = requests.get(
            url=self.base_url + f"/public/stats/student",
            params={"student_name": self.student_name}
        )
        return response.json()

    def get_courses(self, limit: int = 100, offset: int = 0):
        response = requests.get(
            url=self.base_url + f"/public/search/courses",
            params={"limit": limit, "offset": offset}
        )
        return response.json()

    def get_detail_lesson(self, lesson_id: str) -> Lesson | None:
        response = requests.get(
            url=self.base_url + f"/public/lessons/{lesson_id}/public"
        )
        if response.status_code == 200:
            lesson = Lesson.model_validate(response.json())
            return lesson
        return None

    def get_due_schedule(self) -> List[Schedule] | None:
        response = requests.get(
            url=self.base_url + f"/public/schedules/due",
            params={"student_name": self.student_name}
        )
        adapter = TypeAdapter(list[Schedule])
        try:
            schedules = adapter.validate_python(response.json())
            return [item for item in schedules if item.lesson_id is not None]
        except Exception as e:
            print('Cannot get schedules due to error:', e)

        return None

# === export ===
lms_service = LmsService()