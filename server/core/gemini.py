from google import genai
from google.genai import types

from server.core.config import settings
from server.core.constants import *


class GeminiModel:
    def __init__(self, system_instructions_promt: str):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )
        self.model = "gemini-2.5-flash"
        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=GET_ALL_LESSON,
                        description="Gọi hàm này nếu phụ Huynh muốn biết các khóa học hiện tại trong bộ dữ liệu, không phản hồi phụ huynh những thông tin như ID quá số",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=GET_DETAIL_LESSON,
                        description="Gọi hàm nếu Phụ huynh muốn biết cụ thể chi tiết một khóa học/môn học nào đó, trả về id khóa học dựa theo dữ liệu danh sách khóa học, không hỏi phụ huynh mã này",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["subject", 'course_id'],
                            properties={
                                "subject": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                ),
                                "course_id": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                ),
                            },
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="set_notifications",
                        description="Gọi hàm này nếu phụ huynh muốn đặt lịch hẹn nhắc nhở học sinh",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["date_time_to_notification", "message"],
                            properties={
                                "date_time_to_notification": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                ),
                                "message": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                ),
                            },
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_student_score",
                        description="Gọi hàm này nếu phụ huynh muốn biết điểm số một môn học nào đó của học sinh, suy luận ra id của khóa học dựa theo lịch sử",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["subject", "course_id"],
                            properties={
                                "subject": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                ),
                                "course_id": genai.types.Schema(
                                    type=genai.types.Type.STRING,
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
                    types.FunctionDeclaration(
                        name=GET_STUDENT_CLASSROOM,
                        description="Gọi hàm này nếu phụ Huynh muốn biết thông tin lớp học của học sinh",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=GET_LEARN_SCHEDULE,
                        description="Gọi hàm này nếu phụ Huynh muốn biết thông tin lịch học của con",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=CREAT_LESSON_SCHEDULE,
                        description="Gọi hàm này nếu phụ huynh muốn tạo thời gian biểu hoặc lịch học cho con",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["course_id", "lesson_id", "day_of_week"],
                            properties={
                                "course_id": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="ID của khóa học, dựa theo lịch sử chat để lấy thông tin"
                                ),
                                "lesson_id": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="ID của bài học trong khóa học, dựa theo lịch sử chat để lấy thông tin"
                                ),
                                "day_of_week": genai.types.Schema(
                                    type=genai.types.Type.NUMBER,
                                    description="Thứ tự ngày trong tuần 0 -> 6, tương ứng từ Chủ nhật đến thứ Hai cho đến thứ Bảy"
                                ),
                                "time_hhmm": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="Thời gian cụ thể để lập lịch trong cho bài học cho học sinh, tham số trả về là định dạng hh:mm"
                                ),
                            },
                        ),
                    ),
                ])
        ]
        self.generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            tools=self.tools,
            system_instruction=[
                types.Part.from_text(text=system_instructions_promt),
            ],
        )
