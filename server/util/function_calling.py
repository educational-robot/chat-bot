from typing import List

import requests
from google.genai import Client, types
from google.genai.types import Content

from server.core.config import settings
from server.service.robot_support_utils_service import RobotSupportUtilsService
from server.util import telegram_utils
from server.core.constants import *

MODEL = "gemini-2.5-flash"
robot_support_utils_service = RobotSupportUtilsService()

def call(function_name: str, args: dict, client: Client, history: List[Content]):
    print('function: ', function_name)
    print('args: ', args)
    if function_name == GET_ALL_LESSON:
        limit = 100
        offset = 0
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/search/courses",
            params={"limit": limit, "offset": offset}
        )
        courses = [
            {'id': course['id'], 'title': course['title'], 'description': course['description'], 'tags': course['tags']}
            for course in api_response.json()
        ]
        # save history chat
        history.append(
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_ALL_LESSON, args=args)]))
        history.append(types.Content(role="function",
                                     parts=[types.Part.from_function_response(
                                         name=GET_ALL_LESSON,
                                         response={
                                             'description': 'Đây là thông tin toàn bộ khóa học hiện có của hệ thống với id, tên khóa, mô tả tương ứng.',
                                             'courses': courses
                                         }
                                     )]))

        answer = client.models.generate_content(
            model=MODEL,
            contents=history,
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_STUDENT_OVERALL:
        student = settings.STUDENT_NAME
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/stats/student",
            params={"student_name": student}
        )
        # save history
        history.extend(
            [types.Content(role="model", parts=[types.Part.from_function_call(name=GET_STUDENT_OVERALL, args=args)]),
             types.Content(role="function", parts=[types.Part.from_function_response(
                 name=GET_ALL_LESSON, response={
                     'description': 'Đây là thông tin kết quả tổng quát của học sinh',
                     'overall': api_response.json()
                 }
             )])]
        )

        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_ENROLLED_COURSES:
        student = settings.STUDENT_NAME
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/courses",
            params={"student_name": student}
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_ENROLLED_COURSES, args=args)]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_ENROLLED_COURSES, response={
                    'description': 'Đây là danh sách khóa học mà học sinh đã tham gia',
                    'courses': api_response.json()
                }
            )]),
        ])
        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_DETAIL_LESSON:
        course_id = args['course_id'] if args['course_id'] else '68f506fdad0f33dd7afa284a'
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/courses/{course_id}/lessons/public",
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_DETAIL_LESSON, args=args)]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_ALL_LESSON, response={'course_detail': api_response.json()}
            )]),
        ])

        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_STUDENT_CLASSROOM:
        student = settings.STUDENT_NAME
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/student/classrooms",
            params={"student_name": student}
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_STUDENT_CLASSROOM, args=args)]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_STUDENT_CLASSROOM, response={
                    'description': 'Đây là thông tin lớp học của học sinh',
                    'class_room': api_response.json()
                }
            )]),
        ])
        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_LEARN_SCHEDULE:
        student = settings.STUDENT_NAME
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/schedules/due",
            params={"student_name": student}
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_LEARN_SCHEDULE, args=args)]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_LEARN_SCHEDULE, response={
                    'description': 'Đây là thông tin lịch học của học sinh',
                    'schedules': api_response.json()
                }
            )]),
        ])
        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_CLASSROOM_ASSIGNMENT:
        student = settings.STUDENT_NAME
        classroom_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/student/classrooms",
            params={"student_name": student}
        ).json()
        print('classroom_response:', classroom_response)
        classroom_id = classroom_response[0].get('classroom_id')
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/assignments/classrooms/{classroom_id}/list",
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_CLASSROOM_ASSIGNMENT, args=args)]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_CLASSROOM_ASSIGNMENT, response={
                    'description': 'Đây là thông tin bài tập về nhà của học sinh',
                    'assignments': api_response.json()
                }
            )]),
        ])
        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == CREAT_LESSON_SCHEDULE:
        student = settings.STUDENT_NAME
        api_response = requests.post(
            url=settings.LMS_BASE_URL + f"/public/schedules",
            json={
                "student_name": student,
                "course_id": args['course_id'],
                "lesson_id": args['lesson_id'],
                "day_of_week": args['day_of_week'],
                "time_hhmm": args['time_hhmm'],
            }
        )
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=CREAT_LESSON_SCHEDULE, args=args)]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=CREAT_LESSON_SCHEDULE, response={
                    'description': 'Đây là kết quả tạo lịch học cho học sinh',
                    'schedules': api_response.json()
                }
            )]),
        ])
        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == TAKE_PICTURE_FROM_WEBCAM:
        image_bytes = robot_support_utils_service.take_picture()
        if image_bytes:
            telegram_utils.send_photo_message(image_bytes, 'Đây là ảnh chụp từ webcam')
    elif function_name == TAKE_VIDEO_FROM_WEBCAM:
        image_bytes = robot_support_utils_service.take_video()
        if image_bytes:
            telegram_utils.send_video_message(image_bytes, 'Đây là video từ webcam')
