from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Lesson(BaseModel):
    id: str
    course_id: str
    course_title: str
    title: str
    youtube_id: str
    youtube_url: str
    youtube_embed_url: str
    youtube_watch_url: str
    order: int
    is_published: bool
    duration_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime