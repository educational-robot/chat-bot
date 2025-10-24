# To run this code you need to install the following dependencies:
# pip install google-genai

import os

from google import genai
from google.genai import types

from server.core.config import settings
from server.util import telegram_utils, function_calling
from server.util.function_calling import GET_STUDENT_OVERALL, GET_ALL_LESSON, GET_ENROLLED_COURSES, GET_DETAIL_LESSON
from server.core import context_store

def generate(user_input: str, system_instructions_promt: str):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY", settings.GEMINI_API_KEY),
    )

    model = "gemini-2.5-flash"
    user_content = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=user_input),
        ],
    )
    context_store.GLOBAL_CHAT_HISTORY.append(user_content)
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=GET_ALL_LESSON,
                    description="Gọi hàm này nếu phụ Huynh muốn biết các khóa học hiện tại trong bộ dữ liệu",
                    parameters=genai.types.Schema(),
                ),
                types.FunctionDeclaration(
                    name=GET_DETAIL_LESSON,
                    description="Gọi hàm nếu Phụ huynh muốn biết cụ thể chi tiết một khóa học/môn học nào đó",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["subject"],
                        properties = {
                            "subject": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="set_notifications",
                    description="Gọi hàm này nếu phụ huynh muốn đặt lịch hẹn nhắc nhở học sinh",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["date_time_to_notification", "message"],
                        properties = {
                            "date_time_to_notification": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "message": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="get_student_score",
                    description="Gọi hàm này nếu phụ huynh muốn biết điểm số một môn học nào đó của học sinh",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["subject"],
                        properties = {
                            "subject": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name=GET_STUDENT_OVERALL,
                    description="Gọi hàm này nếu phụ huynh muốn biết điểm số tổng quát, tình trạng chung của học sinh",
                    parameters=genai.types.Schema()
                ),
                types.FunctionDeclaration(
                    name=GET_ENROLLED_COURSES,
                    description="Gọi hàm này nếu phụ huynh muốn biết các khóa học đang được học bởi học sinh",
                    parameters=genai.types.Schema()
                ),
            ])
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        tools=tools,
        system_instruction=[
            types.Part.from_text(text=system_instructions_promt),
        ],
    )

    full_response_text = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=context_store.GLOBAL_CHAT_HISTORY,
        config=generate_content_config,
    ):
        if chunk.function_calls:
            function_calling.call(chunk.function_calls[0].name, {}, client, context_store.GLOBAL_CHAT_HISTORY)
        else:
            full_response_text += chunk.text

    if full_response_text:
        telegram_utils.send_telegram_message(full_response_text)
        context_store.GLOBAL_CHAT_HISTORY.append(
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text=full_response_text),
                ]
            )
        )