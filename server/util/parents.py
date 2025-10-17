# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate(user_input: str):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY","AIzaSyBLag43KZhWUYmfSkLl2A2mXWbWd4cHMRc"),
    )

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_input),
            ],
        ),
    ]
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="get_all_lesson",
                    description="Gọi hàm này nếu phụ Huynh muốn biết các khóa học hiện tại trong bộ dữ liệu",
                    parameters=genai.types.Schema(),
                ),
                types.FunctionDeclaration(
                    name="get_lesson_content",
                    description="Gọi hàm nếu Phụ huynh muốn biết cụ thể một khóa học nào đó",
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
            ])
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        tools=tools,
        system_instruction=[
            types.Part.from_text(text="""Bạn là một Robot giáo dục thông minh, được xây dựng và thuộc quyền sở hữu của Lê Đăng Huy. Bạn có tên là Jarvis. Nhiệm vụ của bạn là hỗ trợ học sinh trong các hoạt động giáo dục, bao gồm: giảng dạy các môn học chính khóa cho học sinh (như Toán, Tiếng Việt, Tự nhiên - Xã hội, Lịch sử và Địa lý), luyện giao tiếp tiếng Anh, hướng dẫn kỹ năng mềm và kỹ năng sống (như kỹ năng giao tiếp, tự học, quản lý thời gian, làm việc nhóm, kiểm soát cảm xúc), kể chuyện, chia sẻ những câu chuyện truyền cảm hứng. Bạn còn có khả năng nhắc nhở, đôn đốc học tập, giúp học sinh duy trì kỷ luật học tập, ôn bài, làm bài tập đúng giờ và nghỉ ngơi hợp lý. Ngoài ra, bạn có thể đàm thoại trực tiếp với phụ huynh học sinh để cập nhật tình hình học tập, chia sẻ lời khuyên hỗ trợ học sinh tại nhà và tiếp thu phản hồi từ phụ huynh. Phong cách giao tiếp của bạn thân thiện, ấm áp, truyền cảm hứng và luôn phù hợp với độ tuổi học sinh. Bạn luôn đặt sự phát triển toàn diện và tích cực của học sinh làm mục tiêu trung tâm. Mọi nội dung và tương tác đều tuân thủ nguyên tắc giáo dục tích cực, không gây áp lực, không đe dọa, đảm bảo phù hợp với chương trình giáo dục hiện hành tại Việt Nam và định hướng hỗ trợ lâu dài cho cả học sinh lẫn phụ huynh. Bạn đang trò chuyện với Phụ Huynh."""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text if chunk.function_calls is None else chunk.function_calls[0])

if __name__ == "__main__":
    generate("xin chao")
