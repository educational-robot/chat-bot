from typing import Optional

from pydantic import BaseModel


class Schedule(BaseModel):
    id: str
    course_id: str
    lesson_id: Optional[str] = None
    time_hhmm: str