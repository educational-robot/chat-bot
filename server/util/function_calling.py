from typing import List

import requests
from google.genai import Client, types
from google.genai.types import Content

from server.core.config import settings
from server.util import telegram_utils

MODEL = "gemini-2.5-flash"
# function list
GET_ALL_LESSON = 'get_all_lesson'
GET_STUDENT_OVERALL = 'get_student_overall'
GET_ENROLLED_COURSES = 'get_enrolled_courses'
GET_DETAIL_LESSON = "get_lesson_content"

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
        history.append(types.Content(role="model", parts=[types.Part.from_function_call(name=GET_ALL_LESSON, args={})]))
        history.append(types.Content(role="function", parts=[types.Part.from_function_response(
                    name=GET_ALL_LESSON, response={'courses': courses}
                )]))

        answer = client.models.generate_content(
            model=MODEL,
            contents=history,
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_STUDENT_OVERALL:
        student = 'Alice Johnson'
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/stats/student",
            params={"student_name": student}
        )
        # save history
        history.extend(
            [types.Content(role="model", parts=[types.Part.from_function_call(name=GET_ALL_LESSON, args={})]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_ALL_LESSON, response={'overall': api_response.json()}
            )])]
        )

        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_ENROLLED_COURSES:
        student = 'Alice Johnson'
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/courses",
            params={"student_name": student}
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_ALL_LESSON, args={})]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_ALL_LESSON, response={'courses': api_response.json()}
            )]),
        ])
        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)
    elif function_name == GET_DETAIL_LESSON:
        course_id = '68f506fdad0f33dd7afa2849'
        api_response = requests.get(
            url=settings.LMS_BASE_URL + f"/public/courses/{course_id}/lessons/public",
        )
        # save history
        history.extend([
            types.Content(role="model", parts=[types.Part.from_function_call(name=GET_ALL_LESSON, args={})]),
            types.Content(role="function", parts=[types.Part.from_function_response(
                name=GET_ALL_LESSON, response={'course_detail': api_response.json()}
            )]),
        ])

        answer = client.models.generate_content(
            model=MODEL,
            contents=history
        )
        telegram_utils.send_telegram_message(answer.text)