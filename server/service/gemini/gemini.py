from datetime import timezone, timedelta, datetime

from server.util.timezone_utils import get_vietnam_timezone, get_vietnam_now
from typing import List

from google import genai
from google.genai import types

from server.core.config import settings
from server.core.constants import *


class Gemini:
    def __init__(self, system_instructions_prompt: str):
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
                        description="Gọi hàm này CHỈ KHI phụ huynh lần đầu yêu cầu xem kết quả học tập hoặc thông tin lớp học. Hàm này trả về danh sách các lớp học mà học sinh đang tham gia. QUAN TRỌNG: Nếu đã gọi hàm này trước đó và phụ huynh đã chọn lớp học cụ thể (ví dụ: 'lớp 8a1'), KHÔNG GỌI LẠI hàm này, mà hãy gọi get_classroom_assignment với classroom_id từ lịch sử chat.",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=GET_LEARN_SCHEDULE,
                        description="Gọi hàm này nếu phụ Huynh muốn biết thông tin lịch học của con",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=GET_CLASSROOM_ASSIGNMENT,
                        description="Gọi hàm này NGAY LẬP TỨC khi: (1) Phụ huynh đã chọn lớp học cụ thể sau khi đã gọi get_student_classroom (ví dụ: phụ huynh nói 'lớp 8a1', 'cho tôi xem kết quả học tập của lớp 8a1'), HOẶC (2) Phụ huynh trực tiếp yêu cầu xem bài tập. Hàm này tự động lấy classroom_id từ lịch sử chat (từ kết quả get_student_classroom) và trả về danh sách bài tập. QUAN TRỌNG: Nếu trong lịch sử chat đã có kết quả get_student_classroom và phụ huynh đề cập đến tên lớp, hãy match tên lớp với classroom_id trong history và gọi hàm này ngay.",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=GET_ASSIGNMENT_SUBMISSION,
                        description="GỌI HÀM NÀY NGAY LẬP TỨC - KHÔNG HỎI LẠI - khi phụ huynh: (1) Đề cập đến tên bài tập (ví dụ: 'Trắc nghiệm Tiếng Anh 8 Unit 1', 'toán 11', 'bài tập toán 11'), (2) Đề cập đến số thứ tự bài tập (ví dụ: 'bài tập số 1', 'bài 1', 'số 1'), (3) Nói 'đúng' sau khi đã được hỏi về bài tập, (4) Bất kỳ câu nào có từ khóa liên quan đến bài tập. QUAN TRỌNG TUYỆT ĐỐI: KHÔNG BAO GIỜ hỏi lại 'Anh/chị muốn xem kết quả của bài tập nào?', KHÔNG BAO GIỜ lặp lại danh sách bài tập. PHẢI tự động gọi hàm này ngay khi phụ huynh chọn bài tập. Hàm này tự động match bài tập theo tên hoặc số thứ tự từ lịch sử chat.",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=[],
                            properties={
                                "assignment_id": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="ID của bài tập (optional). Có thể để trống hoặc không truyền, hàm sẽ tự động match theo tên bài tập hoặc số thứ tự từ lịch sử chat."
                                ),
                            },
                        ),
                    ),
                    types.FunctionDeclaration(
                        name=CREAT_LESSON_SCHEDULE,
                        description="Gọi hàm này nếu phụ huynh muốn tạo thời gian biểu hoặc lịch học cho con. Thứ tự ngày trong tuần (day_of_week) 0 -> 6, tương ứng giá trị như sau Chủ nhật=0 đến thứ Hai=1 cho đến thứ Bảy=6",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["course_id", "lesson_id", "day_of_week", "time_hhmm"],
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
                                    description="Thứ tự ngày trong tuần 0 -> 6, tương ứng giá trị như sau Chủ nhật=0 đến thứ Hai=1 cho đến thứ Bảy=6"
                                ),
                                "time_hhmm": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="Thời gian cụ thể để lập lịch trong cho bài học cho học sinh, tham số trả về là định dạng hh:mm"
                                ),
                            },
                        ),
                    ),
                    types.FunctionDeclaration(
                        name=TAKE_PICTURE_FROM_WEBCAM,
                        description="Gọi hàm này nếu phụ Huynh muốn chụp ảnh từ webcam từ robot mà học sinh đang học",
                        parameters=genai.types.Schema(),
                    ),
                    types.FunctionDeclaration(
                        name=TAKE_VIDEO_FROM_WEBCAM,
                        description="Gọi hàm này nếu phụ Huynh muốn quay hình hoặc xem một đoạn ghi hình từ webcam từ robot mà học sinh đang học",
                        parameters=genai.types.Schema(),
                    ),
                ])
        ]
        self.system_instructions_prompt = system_instructions_prompt

    def generate_main_content(self, history: List[types.Content]):
        # enhance system prompt with current time (múi giờ Việt Nam)
        now = get_vietnam_now().strftime("%Y-%m-%d %H:%M:%S")
        print('now (VN timezone):', now)
        main_generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            tools=self.tools,
            system_instruction=[
                types.Part.from_text(text=f'{self.system_instructions_prompt} '
                                          f'Thời gian hiện tại (GMT+7): {now}'),
            ],
        )

        return self.client.models.generate_content(
                model=self.model,
                contents=history,
                config=main_generate_content_config,
        )

    def generate_simple_message(self, contents: List[types.Content]):
        return self.client.models.generate_content(
            model=self.model,
            contents=contents
        )