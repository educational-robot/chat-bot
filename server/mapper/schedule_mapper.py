from datetime import datetime, date

from server.dto.schedule import Schedule
from server.models.schedule import TelegramSchedule
from server.service.lms.lms_service import LmsService


def to_telegram_schedule(schedule: Schedule) -> TelegramSchedule | None:
    lms_service = LmsService()
    telegram_schedule = TelegramSchedule(schedule)
    lesson = lms_service.get_detail_lesson(schedule.lesson_id)

    if lesson is None:
        return None

    telegram_schedule.course_name = lesson.course_title
    telegram_schedule.lesson_name = lesson.title
    time_obj = datetime.strptime(schedule.time_hhmm, "%H:%M").time()
    telegram_schedule.due_time = datetime.combine(date.today(), time_obj)
    #TODO them timezone VN

    return telegram_schedule