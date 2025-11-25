from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from server.mapper import schedule_mapper
from server.service.gemini.gemini_service import gemini_service
from server.service.lms.lms_service import LmsService
from server.service.telegram.telegram_service import telegram_service
from server.util import gemini_utils


def lesson_notification_job(course_name: str, lesson_name: str, due_time: datetime):
    print("on lesson_notification_job...")
    contents = [
        gemini_utils.create_user_content(
            "Bạn là một hệ thống gửi thông báo học tập.\n"
            "Hãy tạo một tin nhắn thân thiện để thông báo cho phụ huynh về buổi học sắp tới của học sinh"
            "dựa theo thông tin sau:\n\n"
            f"Khóa học: {course_name}\n"
            f"Bài học: {lesson_name}\n"
            f"Thời gian bắt đầu: {due_time}\n"
            "Yêu cầu: Hãy viết nội dung ngắn gọn, thân thiện, dễ hiểu."
        )
    ]
    message = gemini_service.generate_simple_message(contents)
    telegram_service.send_message(message)

class LearningNotificationService:

    def __init__(self):
        self.lms_service = LmsService()
        self.scheduler = BackgroundScheduler()
        pass

    def scan_schedule(self):
        print("scan_schedule")
        schedules = self.lms_service.get_due_schedule()

        if schedules:
            for schedule in schedules:
                print("schedule", schedule)
                telegram_schedule = schedule_mapper.to_telegram_schedule(schedule)
                if telegram_schedule is None:
                    print("Failed to create schedule")
                    continue
                if telegram_schedule.due_time >= datetime.now():
                    print('TODO notify now')
                else:
                    print("scheduling")
                    self.scheduler.add_job(
                        lesson_notification_job,
                        'cron',
                        hour=telegram_schedule.due_time.hour,
                        minute=telegram_schedule.due_time.minute,
                        id="daily_greeting",
                        kwargs={"course_name": telegram_schedule.course_name,
                                "lesson_name": telegram_schedule.lesson_name,
                                "due_time": telegram_schedule.due_time},
                        replace_existing=True
                    )
                    print("done scheduling")

    # Called only on start-up
    def schedule_daily_scan(self):
        print("schedule_daily_scan")
        self.scheduler.add_job(
            self.scan_schedule,
            'cron',
            hour=0,
            minute=0,
            id="daily_scan",
            replace_existing=True
        )