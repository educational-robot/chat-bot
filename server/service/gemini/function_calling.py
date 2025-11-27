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
        print(f'[DEBUG] FunctionCallingHandler.handler - Called with function: {function_name}')
        print(f'[DEBUG] FunctionCallingHandler.handler - Args type: {type(args)}, Args: {args}')
        print(f'[DEBUG] FunctionCallingHandler.handler - History length before trim: {len(history)}')
        
        N = settings.MAX_LENGTH_HISTORY
        history = history[-N:]
        print(f'[DEBUG] FunctionCallingHandler.handler - History length after trim: {len(history)}')
        print(f'[DEBUG] FunctionCallingHandler.handler - Processing function: {function_name}')
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
            print(f'[DEBUG] GET_LEARN_SCHEDULE - Starting...')
            print(f'[DEBUG] GET_LEARN_SCHEDULE - Args received: {args}')
            
            try:
                print(f'[DEBUG] GET_LEARN_SCHEDULE - Calling get_due_schedule()...')
                schedules = self.lms_service.get_due_schedule()
                print(f'[DEBUG] GET_LEARN_SCHEDULE - get_due_schedule() returned: {schedules}')
                print(f'[DEBUG] GET_LEARN_SCHEDULE - Type: {type(schedules)}')
                
                if schedules is None:
                    print(f'[WARNING] GET_LEARN_SCHEDULE - get_due_schedule() returned None')
                    response_data = {
                        'description': 'Không tìm thấy lịch học nào cho học sinh',
                        'schedules': [],
                        'message': 'Không có lịch học sắp tới'
                    }
                elif isinstance(schedules, list):
                    print(f'[DEBUG] GET_LEARN_SCHEDULE - Found {len(schedules)} schedules')
                    response_data = {
                        'description': 'Đây là thông tin lịch học của học sinh',
                        'schedules': schedules
                    }
                else:
                    print(f'[WARNING] GET_LEARN_SCHEDULE - Unexpected type returned: {type(schedules)}')
                    response_data = {
                        'description': 'Đây là thông tin lịch học của học sinh',
                        'schedules': schedules if schedules else []
                    }
                
                history.extend([
                    create_model_function_call(GET_LEARN_SCHEDULE, args),
                    create_function_response(GET_LEARN_SCHEDULE, response=response_data)
                ])
                print(f'[DEBUG] GET_LEARN_SCHEDULE - Successfully added to history')
                
            except Exception as e:
                print(f'[ERROR] GET_LEARN_SCHEDULE - Error: {type(e).__name__}: {e}')
                import traceback
                print(f'[ERROR] GET_LEARN_SCHEDULE - Traceback: {traceback.format_exc()}')
                error_response = {
                    'description': f'Đã xảy ra lỗi khi lấy lịch học: {str(e)}',
                    'schedules': [],
                    'error': str(e)
                }
                history.extend([
                    create_model_function_call(GET_LEARN_SCHEDULE, args),
                    create_function_response(GET_LEARN_SCHEDULE, response=error_response)
                ])
        elif function_name == GET_CLASSROOM_ASSIGNMENT:
            print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Starting...')
            print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Args received: {args}')
            
            try:
                print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Step 1: Getting student classroom...')
                classroom_response = self.lms_service.get_student_classroom()
                print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - classroom_response: {classroom_response}')
                print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - classroom_response type: {type(classroom_response)}')
                
                if not classroom_response:
                    print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - classroom_response is empty or None')
                    error_response = {
                        'description': 'Không tìm thấy thông tin lớp học của học sinh',
                        'assignments': [],
                        'error': 'No classroom found'
                    }
                    history.extend([
                        create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                        create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                    ])
                elif not isinstance(classroom_response, list) or len(classroom_response) == 0:
                    print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - classroom_response is not a list or is empty')
                    print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - Type: {type(classroom_response)}, Length: {len(classroom_response) if isinstance(classroom_response, list) else "N/A"}')
                    error_response = {
                        'description': 'Không tìm thấy thông tin lớp học của học sinh',
                        'assignments': [],
                        'error': 'Invalid classroom response format'
                    }
                    history.extend([
                        create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                        create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                    ])
                else:
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Step 2: Extracting classroom_id...')
                    first_classroom = classroom_response[0]
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - first_classroom: {first_classroom}')
                    classroom_id = first_classroom.get('classroom_id') if isinstance(first_classroom, dict) else None
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - classroom_id: {classroom_id}')
                    
                    if not classroom_id:
                        print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - classroom_id is None or empty')
                        print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - first_classroom keys: {first_classroom.keys() if isinstance(first_classroom, dict) else "N/A"}')
                        error_response = {
                            'description': 'Không tìm thấy ID lớp học',
                            'assignments': [],
                            'error': 'classroom_id not found in response'
                        }
                        history.extend([
                            create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                            create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                        ])
                    else:
                        print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Step 3: Getting assignments for classroom_id: {classroom_id}...')
                        assignments = self.lms_service.get_classroom_assignment(classroom_id)
                        print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - assignments response: {assignments}')
                        print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - assignments type: {type(assignments)}')
                        
                        if isinstance(assignments, list):
                            print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Found {len(assignments)} assignments')
                        elif isinstance(assignments, dict) and 'error' in assignments:
                            print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - API returned error: {assignments}')
                        
                        response_data = {
                            'description': 'Đây là thông tin bài tập về nhà của học sinh',
                            'assignments': assignments if assignments else []
                        }
                        
                        history.extend([
                            create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                            create_function_response(GET_CLASSROOM_ASSIGNMENT, response=response_data)
                        ])
                        print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Successfully added to history')
                        
            except IndexError as e:
                print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - IndexError: {e}')
                print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - classroom_response might be empty')
                error_response = {
                    'description': 'Không tìm thấy thông tin lớp học của học sinh',
                    'assignments': [],
                    'error': f'IndexError: {str(e)}'
                }
                history.extend([
                    create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                    create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                ])
            except KeyError as e:
                print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - KeyError: {e}')
                error_response = {
                    'description': f'Lỗi khi lấy thông tin lớp học: thiếu key {str(e)}',
                    'assignments': [],
                    'error': f'KeyError: {str(e)}'
                }
                history.extend([
                    create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                    create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                ])
            except Exception as e:
                print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - Unexpected error: {type(e).__name__}: {e}')
                import traceback
                print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - Traceback: {traceback.format_exc()}')
                error_response = {
                    'description': f'Đã xảy ra lỗi khi lấy bài tập về nhà: {str(e)}',
                    'assignments': [],
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                history.extend([
                    create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                    create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                ])
        elif function_name == CREAT_LESSON_SCHEDULE:
            print(f'[DEBUG] CREAT_LESSON_SCHEDULE - Starting...')
            print(f'[DEBUG] CREAT_LESSON_SCHEDULE - Args received: {args}')
            
            # Validate args
            required_args = ['course_id', 'lesson_id', 'day_of_week', 'time_hhmm']
            missing_args = [arg for arg in required_args if arg not in args or args[arg] is None]
            if missing_args:
                print(f'[ERROR] CREAT_LESSON_SCHEDULE - Missing required args: {missing_args}')
                error_response = {
                    'description': f'Thiếu thông tin bắt buộc: {", ".join(missing_args)}',
                    'error': 'Missing required arguments',
                    'missing_args': missing_args
                }
                history.extend([
                    create_model_function_call(CREAT_LESSON_SCHEDULE, args),
                    create_function_response(CREAT_LESSON_SCHEDULE, response=error_response)
                ])
            else:
                try:
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - Calling LMS API...')
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - course_id: {args["course_id"]}')
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - lesson_id: {args["lesson_id"]}')
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - day_of_week: {args["day_of_week"]} (type: {type(args["day_of_week"])})')
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - time_hhmm: {args["time_hhmm"]}')
                    
                    # Convert day_of_week to int if needed
                    day_of_week = args['day_of_week']
                    if isinstance(day_of_week, str):
                        try:
                            day_of_week = int(day_of_week)
                            print(f'[DEBUG] CREAT_LESSON_SCHEDULE - Converted day_of_week from string to int: {day_of_week}')
                        except ValueError:
                            print(f'[ERROR] CREAT_LESSON_SCHEDULE - Cannot convert day_of_week to int: {day_of_week}')
                            raise ValueError(f"day_of_week must be a number, got: {day_of_week}")
                    
                    schedule_result = self.lms_service.create_learning_schedule(
                        args['course_id'],
                        args['lesson_id'],
                        day_of_week,
                        args['time_hhmm']
                    )
                    
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - LMS API response: {schedule_result}')
                    
                    history.extend([
                        create_model_function_call(CREAT_LESSON_SCHEDULE, args),
                        create_function_response(CREAT_LESSON_SCHEDULE,
                                                 response={
                                                     'description': 'Đây là kết quả tạo lịch học cho học sinh',
                                                     'schedules': schedule_result
                                                 })
                    ])
                    print(f'[DEBUG] CREAT_LESSON_SCHEDULE - Successfully added to history')
                except KeyError as e:
                    print(f'[ERROR] CREAT_LESSON_SCHEDULE - KeyError: {e}')
                    error_response = {
                        'description': f'Lỗi: Thiếu thông tin {str(e)}',
                        'error': str(e)
                    }
                    history.extend([
                        create_model_function_call(CREAT_LESSON_SCHEDULE, args),
                        create_function_response(CREAT_LESSON_SCHEDULE, response=error_response)
                    ])
                except ValueError as e:
                    print(f'[ERROR] CREAT_LESSON_SCHEDULE - ValueError: {e}')
                    error_response = {
                        'description': f'Lỗi định dạng dữ liệu: {str(e)}',
                        'error': str(e)
                    }
                    history.extend([
                        create_model_function_call(CREAT_LESSON_SCHEDULE, args),
                        create_function_response(CREAT_LESSON_SCHEDULE, response=error_response)
                    ])
                except Exception as e:
                    print(f'[ERROR] CREAT_LESSON_SCHEDULE - Unexpected error: {type(e).__name__}: {e}')
                    import traceback
                    print(f'[ERROR] CREAT_LESSON_SCHEDULE - Traceback: {traceback.format_exc()}')
                    error_response = {
                        'description': f'Đã xảy ra lỗi khi tạo lịch học: {str(e)}',
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    history.extend([
                        create_model_function_call(CREAT_LESSON_SCHEDULE, args),
                        create_function_response(CREAT_LESSON_SCHEDULE, response=error_response)
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
