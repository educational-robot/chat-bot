from pydantic import BaseModel


class Schedule(BaseModel):
    id: str
    course_id: str
    lesson_id: str
    time_hhmm: str