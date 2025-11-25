from typing import List

import redis
import requests
from google.genai import types
from google.genai.types import Content

from server.core.config import settings
from server.service.gemini.gemini import Gemini
from server.service.lms.lms_service import LmsService, lms_service
from server.service.robot_support_utils_service import RobotSupportUtilsService
from server.service.telegram.telegram_service import TelegramService, telegram_service
from server.util import telegram_utils
from server.core.constants import *
from server.util.gemini_utils import create_model_function_call, create_function_response

MODEL = "gemini-2.5-flash"
robot_support_utils_service = RobotSupportUtilsService()

class FunctionCallingHandler:
    def __init__(self, gemini: Gemini):
        self.gemini = gemini
        self.lms_service = lms_service
        self.telegram_service = telegram_service

    def response(self, function_name: str, history: List[Content]):
        answer = self.gemini.generate_main_content(history)
        print(f'answer for {function_name} generated!')
        self.telegram_service.send_message(answer.text)

    def handler(self, function_name: str, args: dict, history: List[Content]):
        N = settings.MAX_LENGTH_HISTORY
        history = history[-N:]
        print('function: ', function_name)
        print('args: ', args)
        if function_name == GET_ALL_LESSON:
            api_response = self.lms_service.get_courses(100, 0)
            courses = [
                {
                    'id': course['id'],
                    'title': course['title'],
                    'description': course['description'],
                    'tags': course['tags']
                }
                for course in api_response
            ]
            # save history chat
            history.extend([
                create_model_function_call(GET_ALL_LESSON, args),
                create_function_response(GET_ALL_LESSON,
                                         response={
                                             'description': 'Đây là thông tin toàn bộ khóa học hiện có của '
                                                            'hệ thống với id, tên khóa, mô tả tương ứng.',
                                             'courses': courses
                                         })
            ])
        elif function_name == GET_STUDENT_OVERALL:
            # save history
            history.extend([
                create_model_function_call(GET_STUDENT_OVERALL, args),
                create_function_response(GET_STUDENT_OVERALL,
                                         response={
                                             'description': 'Đây là thông tin kết quả tổng quát của học sinh',
                                             'overall': self.lms_service.get_student_stats()
                                         })
            ])
        elif function_name == GET_ENROLLED_COURSES:
            # save history
            history.extend([
                create_model_function_call(GET_ENROLLED_COURSES, args),
                create_function_response(GET_ENROLLED_COURSES,
                                         response={
                                             'description': 'Đây là danh sách khóa học mà học sinh đã tham gia',
                                             'courses': self.lms_service.get_student_enrolled_course()
                                         })
            ])
        elif function_name == GET_DETAIL_LESSON:
            course_id = args['course_id'] if args['course_id'] else '68f506fdad0f33dd7afa284a'
            # save history
            history.extend([
                create_model_function_call(GET_DETAIL_LESSON, args),
                create_function_response(GET_DETAIL_LESSON,
                                         response={'course_detail': self.lms_service.get_course_detail(course_id)})
            ])
        elif function_name == GET_STUDENT_CLASSROOM:
            # save history
            history.extend([
                create_model_function_call(GET_STUDENT_CLASSROOM, args),
                create_function_response(GET_STUDENT_CLASSROOM,
                                         response={
                                             'description': 'Đây là thông tin lớp học của học sinh',
                                             'class_room': self.lms_service.get_student_classroom()
                                         })
            ])
        elif function_name == GET_LEARN_SCHEDULE:
            # save history
            history.extend([
                create_model_function_call(GET_LEARN_SCHEDULE, args),
                create_function_response(GET_LEARN_SCHEDULE,
                                         response={
                                             'description': 'Đây là thông tin lịch học của học sinh',
                                             'schedules': self.lms_service.get_due_schedule()
                                         })
            ])
        elif function_name == GET_CLASSROOM_ASSIGNMENT:
            classroom_response = self.lms_service.get_student_classroom()
            classroom_id = classroom_response[0].get('classroom_id')
            # save history
            history.extend([
                create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                create_function_response(GET_CLASSROOM_ASSIGNMENT,
                                         response={
                                             'description': 'Đây là thông tin bài tập về nhà của học sinh',
                                             'assignments': self.lms_service.get_classroom_assignment()
                                         })
            ])
        elif function_name == CREAT_LESSON_SCHEDULE:
            history.extend([
                create_model_function_call(CREAT_LESSON_SCHEDULE, args),
                create_function_response(CREAT_LESSON_SCHEDULE,
                                         response={
                                             'description': 'Đây là kết quả tạo lịch học cho học sinh',
                                             'schedules': self.lms_service.create_learning_schedule(
                                                 args['course_id'],
                                                 args['lesson_id'],
                                                 args['day_of_week'],
                                                 args['time_hhmm']
                                             )
                                         })
            ])
        elif function_name == TAKE_PICTURE_FROM_WEBCAM:
            telegram_utils.send_telegram_message('Phụ huynh vui lòng đợi trong giây lát')
            r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
            r.publish(settings.REDIS_SUBSCRIBE_CHANNEL, 'take_picture')
        elif function_name == TAKE_VIDEO_FROM_WEBCAM:
            telegram_utils.send_telegram_message('Phụ huynh vui lòng đợi trong giây lát')
            r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
            r.publish(settings.REDIS_SUBSCRIBE_CHANNEL, 'take_video')

        if function_name != TAKE_PICTURE_FROM_WEBCAM or function_name != TAKE_VIDEO_FROM_WEBCAM:
            self.response(function_name, history)
