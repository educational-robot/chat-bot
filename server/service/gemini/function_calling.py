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
            print(f'[DEBUG] GET_STUDENT_CLASSROOM - Starting...')
            print(f'[DEBUG] GET_STUDENT_CLASSROOM - Args received: {args}')
            
            try:
                classroom_response = self.lms_service.get_student_classroom()
                print(f'[DEBUG] GET_STUDENT_CLASSROOM - API response: {classroom_response}')
                
                # Lấy lớp đầu tiên (học sinh thường chỉ có 1 lớp)
                first_classroom = None
                if isinstance(classroom_response, list) and len(classroom_response) > 0:
                    first_classroom = classroom_response[0]
                    print(f'[DEBUG] GET_STUDENT_CLASSROOM - Using first classroom: {first_classroom}')
                    
                    # Tự động gọi get_classroom_assignment với lớp đầu tiên
                    classroom_id = first_classroom.get('classroom_id') if isinstance(first_classroom, dict) else None
                    if classroom_id:
                        print(f'[DEBUG] GET_STUDENT_CLASSROOM - Auto-calling get_classroom_assignment with classroom_id: {classroom_id}')
                        assignments_response = self.lms_service.get_classroom_assignment(classroom_id)
                        print(f'[DEBUG] GET_STUDENT_CLASSROOM - Assignments response: {assignments_response}')
                        
                        response_data = {
                            'description': f'Đây là thông tin lớp học và danh sách bài tập của học sinh. Học sinh đang học lớp {first_classroom.get("classroom_name", "")}.',
                            'class_room': classroom_response,
                            'selected_classroom': first_classroom,
                            'assignments': assignments_response
                        }
                    else:
                        response_data = {
                            'description': 'Đây là thông tin lớp học của học sinh.',
                            'class_room': classroom_response,
                            'selected_classroom': first_classroom
                        }
                else:
                    response_data = {
                        'description': 'Học sinh chưa tham gia lớp học nào.',
                        'class_room': [],
                        'assignments': []
                    }
                
                history.extend([
                    create_model_function_call(GET_STUDENT_CLASSROOM, args),
                    create_function_response(GET_STUDENT_CLASSROOM, response=response_data)
                ])
                print(f'[DEBUG] GET_STUDENT_CLASSROOM - Successfully added to history')
                
            except Exception as e:
                print(f'[ERROR] GET_STUDENT_CLASSROOM - Error: {type(e).__name__}: {e}')
                import traceback
                print(f'[ERROR] GET_STUDENT_CLASSROOM - Traceback: {traceback.format_exc()}')
                error_response = {
                    'description': f'Đã xảy ra lỗi khi lấy thông tin lớp học: {str(e)}',
                    'class_room': [],
                    'error': str(e)
                }
                history.extend([
                    create_model_function_call(GET_STUDENT_CLASSROOM, args),
                    create_function_response(GET_STUDENT_CLASSROOM, response=error_response)
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
                # Lấy classroom_id từ history hoặc từ args
                classroom_id = None
                
                # Kiểm tra xem có trong history không (từ GET_STUDENT_CLASSROOM)
                for content in reversed(history[-10:]):  # Check last 10 items
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'function_response') and part.function_response:
                                func_response = part.function_response
                                if hasattr(func_response, 'response') and isinstance(func_response.response, dict):
                                    response_data = func_response.response
                                    # Check if this is from GET_STUDENT_CLASSROOM
                                    if 'selected_classroom' in response_data:
                                        selected = response_data['selected_classroom']
                                        if isinstance(selected, dict) and 'classroom_id' in selected:
                                            classroom_id = selected['classroom_id']
                                            print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Found classroom_id from history: {classroom_id}')
                                            break
                                    elif 'class_room' in response_data:
                                        classrooms = response_data['class_room']
                                        if isinstance(classrooms, list) and len(classrooms) > 0:
                                            first_class = classrooms[0]
                                            if isinstance(first_class, dict) and 'classroom_id' in first_class:
                                                classroom_id = first_class['classroom_id']
                                                print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Found classroom_id from class_room: {classroom_id}')
                                                break
                
                # Nếu không tìm thấy trong history, lấy từ API
                if not classroom_id:
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Step 1: Getting student classroom...')
                    classroom_response = self.lms_service.get_student_classroom()
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - classroom_response: {classroom_response}')
                    
                    if isinstance(classroom_response, list) and len(classroom_response) > 0:
                        first_classroom = classroom_response[0]
                        classroom_id = first_classroom.get('classroom_id') if isinstance(first_classroom, dict) else None
                        print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Using first classroom, classroom_id: {classroom_id}')
                
                if not classroom_id:
                    print(f'[ERROR] GET_CLASSROOM_ASSIGNMENT - Cannot find classroom_id')
                    error_response = {
                        'description': 'Không tìm thấy thông tin lớp học của học sinh',
                        'assignments': [],
                        'error': 'classroom_id not found'
                    }
                    history.extend([
                        create_model_function_call(GET_CLASSROOM_ASSIGNMENT, args),
                        create_function_response(GET_CLASSROOM_ASSIGNMENT, response=error_response)
                    ])
                else:
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - Step 2: Getting assignments for classroom_id: {classroom_id}...')
                    assignments_response = self.lms_service.get_classroom_assignment(classroom_id)
                    print(f'[DEBUG] GET_CLASSROOM_ASSIGNMENT - assignments response: {assignments_response}')
                    
                    # Format response để dễ hiểu
                    assignments_list = []
                    if isinstance(assignments_response, dict):
                        assignments_list = assignments_response.get('assignments', [])
                    elif isinstance(assignments_response, list):
                        assignments_list = assignments_response
                    
                    # Chỉ trả về danh sách bài tập, không phân loại
                    response_data = {
                        'description': f'Đây là danh sách bài tập của học sinh. Tổng cộng có {len(assignments_list)} bài tập.',
                        'assignments': assignments_list
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
        elif function_name == GET_ASSIGNMENT_SUBMISSION:
            print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Starting...')
            print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Args received: {args}')
            
            assignment_id = None
            
            # Nếu có assignment_id trong args, dùng luôn
            if 'assignment_id' in args and args['assignment_id']:
                assignment_id = args['assignment_id']
                print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Using assignment_id from args: {assignment_id}')
            else:
                # Tìm assignment_id từ history dựa trên title/description
                print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Searching for assignment in history...')
                
                # Lấy danh sách assignments từ history
                assignments_list = []
                for content in reversed(history[-20:]):  # Check last 20 items
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'function_response') and part.function_response:
                                func_response = part.function_response
                                if hasattr(func_response, 'response') and isinstance(func_response.response, dict):
                                    response_data = func_response.response
                                    if 'assignments' in response_data:
                                        assignments_list = response_data['assignments']
                                        print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Found assignments list in history: {len(assignments_list)} items')
                                        break
                
                # Match assignment theo title/description từ user input
                # Lấy user message gần nhất để tìm keyword
                user_keywords = []
                for content in reversed(history[-5:]):
                    if hasattr(content, 'role') and content.role == 'user':
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'text'):
                                    user_text = part.text.lower()
                                    # Extract keywords (loại bỏ stop words)
                                    keywords = [w for w in user_text.split() if len(w) > 2 and w not in ['cho', 'tôi', 'xem', 'kết', 'quả', 'bài', 'tập', 'của', 'cháu']]
                                    user_keywords.extend(keywords)
                                    print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - User keywords: {keywords}')
                
                    # Match assignment - cải thiện matching logic
                    if assignments_list and user_keywords:
                        best_match = None
                        best_score = 0
                        
                        # Lấy toàn bộ text từ user message gần nhất
                        user_full_text = ""
                        for content in reversed(history[-5:]):
                            if hasattr(content, 'role') and content.role == 'user':
                                if hasattr(content, 'parts') and content.parts:
                                    for part in content.parts:
                                        if hasattr(part, 'text'):
                                            user_full_text = part.text.lower()
                                            break
                        
                        print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - User full text: {user_full_text}')
                        
                        for idx, assignment in enumerate(assignments_list):
                            if isinstance(assignment, dict):
                                title = assignment.get('title', '').lower()
                                description = assignment.get('description', '').lower() if assignment.get('description') else ''
                                text_to_match = f"{title} {description}"
                                
                                # Tính điểm match
                                score = 0
                                
                                # Match theo số thứ tự (ví dụ: "bài tập số 1", "bài 1")
                                if any(word.isdigit() for word in user_full_text.split()):
                                    numbers = [int(w) for w in user_full_text.split() if w.isdigit()]
                                    if numbers and numbers[0] == idx + 1:
                                        score += 10  # Ưu tiên cao cho số thứ tự
                                
                                # Match theo keywords
                                for keyword in user_keywords:
                                    if keyword in text_to_match:
                                        score += 2
                                    if keyword in title:
                                        score += 3  # Ưu tiên match trong title
                                
                                # Match theo substring (tên bài tập gần đúng)
                                if user_full_text:
                                    # Loại bỏ các từ không quan trọng
                                    important_words = [w for w in user_full_text.split() if len(w) > 3 and w not in ['cho', 'tôi', 'xem', 'kết', 'quả', 'bài', 'tập', 'của', 'cháu', 'muốn']]
                                    for word in important_words:
                                        if word in title or word in description:
                                            score += 5
                                
                                if score > best_score:
                                    best_score = score
                                    best_match = assignment
                    
                    if best_match and best_match.get('id'):
                        assignment_id = best_match['id']
                        print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Matched assignment: {best_match.get("title")} (id: {assignment_id}, score: {best_score})')
            
            if not assignment_id:
                print(f'[ERROR] GET_ASSIGNMENT_SUBMISSION - Cannot find assignment_id')
                error_response = {
                    'description': 'Không tìm thấy bài tập. Vui lòng nêu rõ tên bài tập hoặc số thứ tự bài tập.',
                    'submission': None,
                    'error': 'assignment_id not found'
                }
                history.extend([
                    create_model_function_call(GET_ASSIGNMENT_SUBMISSION, args),
                    create_function_response(GET_ASSIGNMENT_SUBMISSION, response=error_response)
                ])
            else:
                try:
                    submission_result = self.lms_service.get_assignment_submission(assignment_id)
                    print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - API response: {submission_result}')
                    
                    if isinstance(submission_result, dict) and 'error' in submission_result:
                        print(f'[ERROR] GET_ASSIGNMENT_SUBMISSION - API returned error')
                        response_data = {
                            'description': f'Không thể lấy kết quả bài tập: {submission_result.get("message", "Lỗi không xác định")}',
                            'submission': None,
                            'error': submission_result.get('error', 'Unknown error')
                        }
                    else:
                        # Kiểm tra nếu không có submission (chưa hoàn thành)
                        if not submission_result or (isinstance(submission_result, dict) and not submission_result.get('id')):
                            response_data = {
                                'description': 'Bài tập này chưa được hoàn thành.',
                                'submission': None,
                                'status': 'not_completed'
                            }
                            print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Assignment not completed')
                        else:
                            # Format response for better readability
                            response_data = {
                                'description': 'Đây là kết quả học tập của bài tập',
                                'submission': submission_result
                            }
                            print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Successfully retrieved submission')
                    
                    history.extend([
                        create_model_function_call(GET_ASSIGNMENT_SUBMISSION, args),
                        create_function_response(GET_ASSIGNMENT_SUBMISSION, response=response_data)
                    ])
                    print(f'[DEBUG] GET_ASSIGNMENT_SUBMISSION - Successfully added to history')
                    
                except Exception as e:
                    print(f'[ERROR] GET_ASSIGNMENT_SUBMISSION - Unexpected error: {type(e).__name__}: {e}')
                    import traceback
                    print(f'[ERROR] GET_ASSIGNMENT_SUBMISSION - Traceback: {traceback.format_exc()}')
                    error_response = {
                        'description': f'Đã xảy ra lỗi khi lấy kết quả bài tập: {str(e)}',
                        'submission': None,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    history.extend([
                        create_model_function_call(GET_ASSIGNMENT_SUBMISSION, args),
                        create_function_response(GET_ASSIGNMENT_SUBMISSION, response=error_response)
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
