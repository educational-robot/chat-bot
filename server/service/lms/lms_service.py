from typing import List

import requests
from pydantic import TypeAdapter

from server.core.config import settings
from server.dto.courses import Lesson
from server.dto.schedule import Schedule


class LmsService:
    def __init__(self):
        self.base_url = settings.LMS_BASE_URL
        self.student_name = settings.STUDENT_NAME

    def create_learning_schedule(self, course_id: str, lesson_id: str, day_of_week: int, time_hhmm: str):
        print(f'[DEBUG] LmsService.create_learning_schedule - Starting API call...')
        print(f'[DEBUG] LmsService.create_learning_schedule - base_url: {self.base_url}')
        print(f'[DEBUG] LmsService.create_learning_schedule - student_name: {self.student_name}')
        print(f'[DEBUG] LmsService.create_learning_schedule - course_id: {course_id} (type: {type(course_id)})')
        print(f'[DEBUG] LmsService.create_learning_schedule - lesson_id: {lesson_id} (type: {type(lesson_id)})')
        print(f'[DEBUG] LmsService.create_learning_schedule - day_of_week: {day_of_week} (type: {type(day_of_week)})')
        print(f'[DEBUG] LmsService.create_learning_schedule - time_hhmm: {time_hhmm} (type: {type(time_hhmm)})')
        
        request_payload = {
            "student_name": self.student_name,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "day_of_week": day_of_week,
            "time_hhmm": time_hhmm,
        }
        print(f'[DEBUG] LmsService.create_learning_schedule - Request payload: {request_payload}')
        
        url = self.base_url + f"/public/schedules"
        print(f'[DEBUG] LmsService.create_learning_schedule - Full URL: {url}')
        
        try:
            response = requests.post(
                url=url,
                json=request_payload,
                timeout=30  # Add timeout
            )
            
            print(f'[DEBUG] LmsService.create_learning_schedule - Response status code: {response.status_code}')
            print(f'[DEBUG] LmsService.create_learning_schedule - Response headers: {dict(response.headers)}')
            
            try:
                response_json = response.json()
                print(f'[DEBUG] LmsService.create_learning_schedule - Response body: {response_json}')
            except Exception as json_error:
                print(f'[ERROR] LmsService.create_learning_schedule - Cannot parse JSON response: {json_error}')
                print(f'[ERROR] LmsService.create_learning_schedule - Response text: {response.text[:500]}')
                response_json = {"error": "Invalid JSON response", "status_code": response.status_code, "text": response.text[:200]}
            
            if response.status_code >= 400:
                print(f'[ERROR] LmsService.create_learning_schedule - API returned error status: {response.status_code}')
                print(f'[ERROR] LmsService.create_learning_schedule - Error response: {response_json}')
                # Still return the response so function_calling can handle it
                return response_json
            
            print(f'[DEBUG] LmsService.create_learning_schedule - Success!')
            return response_json
            
        except requests.exceptions.Timeout:
            print(f'[ERROR] LmsService.create_learning_schedule - Request timeout')
            return {"error": "Request timeout", "message": "LMS API không phản hồi trong thời gian cho phép"}
        except requests.exceptions.ConnectionError as e:
            print(f'[ERROR] LmsService.create_learning_schedule - Connection error: {e}')
            return {"error": "Connection error", "message": f"Không thể kết nối đến LMS API: {str(e)}"}
        except requests.exceptions.RequestException as e:
            print(f'[ERROR] LmsService.create_learning_schedule - Request exception: {e}')
            return {"error": "Request failed", "message": f"Lỗi khi gọi LMS API: {str(e)}"}
        except Exception as e:
            print(f'[ERROR] LmsService.create_learning_schedule - Unexpected error: {type(e).__name__}: {e}')
            import traceback
            print(f'[ERROR] LmsService.create_learning_schedule - Traceback: {traceback.format_exc()}')
            return {"error": "Unexpected error", "message": f"Lỗi không xác định: {str(e)}"}

    def get_classroom_assignment(self, classroom_id: str):
        print(f'[DEBUG] LmsService.get_classroom_assignment - Starting...')
        print(f'[DEBUG] LmsService.get_classroom_assignment - classroom_id: {classroom_id} (type: {type(classroom_id)})')
        print(f'[DEBUG] LmsService.get_classroom_assignment - base_url: {self.base_url}')
        
        url = self.base_url + f"/assignments/classrooms/{classroom_id}/list"
        print(f'[DEBUG] LmsService.get_classroom_assignment - Full URL: {url}')
        
        try:
            response = requests.get(
                url=url,
                timeout=30
            )
            
            print(f'[DEBUG] LmsService.get_classroom_assignment - Response status code: {response.status_code}')
            print(f'[DEBUG] LmsService.get_classroom_assignment - Response headers: {dict(response.headers)}')
            
            try:
                response_json = response.json()
                print(f'[DEBUG] LmsService.get_classroom_assignment - Response body: {response_json}')
            except Exception as json_error:
                print(f'[ERROR] LmsService.get_classroom_assignment - Cannot parse JSON response: {json_error}')
                print(f'[ERROR] LmsService.get_classroom_assignment - Response text: {response.text[:500]}')
                return {"error": "Invalid JSON response", "status_code": response.status_code, "text": response.text[:200]}
            
            if response.status_code >= 400:
                print(f'[ERROR] LmsService.get_classroom_assignment - API returned error status: {response.status_code}')
                print(f'[ERROR] LmsService.get_classroom_assignment - Error response: {response_json}')
                return response_json
            
            print(f'[DEBUG] LmsService.get_classroom_assignment - Success!')
            return response_json
            
        except requests.exceptions.Timeout:
            print(f'[ERROR] LmsService.get_classroom_assignment - Request timeout')
            return {"error": "Request timeout", "message": "LMS API không phản hồi trong thời gian cho phép"}
        except requests.exceptions.ConnectionError as e:
            print(f'[ERROR] LmsService.get_classroom_assignment - Connection error: {e}')
            return {"error": "Connection error", "message": f"Không thể kết nối đến LMS API: {str(e)}"}
        except requests.exceptions.RequestException as e:
            print(f'[ERROR] LmsService.get_classroom_assignment - Request exception: {e}')
            return {"error": "Request failed", "message": f"Lỗi khi gọi LMS API: {str(e)}"}
        except Exception as e:
            print(f'[ERROR] LmsService.get_classroom_assignment - Unexpected error: {type(e).__name__}: {e}')
            import traceback
            print(f'[ERROR] LmsService.get_classroom_assignment - Traceback: {traceback.format_exc()}')
            return {"error": "Unexpected error", "message": f"Lỗi không xác định: {str(e)}"}

    def get_student_classroom(self):
        print(f'[DEBUG] LmsService.get_student_classroom - Starting...')
        print(f'[DEBUG] LmsService.get_student_classroom - student_name: {self.student_name}')
        print(f'[DEBUG] LmsService.get_student_classroom - base_url: {self.base_url}')
        
        url = self.base_url + f"/public/student/classrooms"
        params = {"student_name": self.student_name}
        print(f'[DEBUG] LmsService.get_student_classroom - Full URL: {url}')
        print(f'[DEBUG] LmsService.get_student_classroom - Params: {params}')
        
        try:
            response = requests.get(
                url=url,
                params=params,
                timeout=30
            )
            
            print(f'[DEBUG] LmsService.get_student_classroom - Response status code: {response.status_code}')
            print(f'[DEBUG] LmsService.get_student_classroom - Response headers: {dict(response.headers)}')
            
            try:
                response_json = response.json()
                print(f'[DEBUG] LmsService.get_student_classroom - Response body: {response_json}')
                print(f'[DEBUG] LmsService.get_student_classroom - Response type: {type(response_json)}')
                if isinstance(response_json, list):
                    print(f'[DEBUG] LmsService.get_student_classroom - Response list length: {len(response_json)}')
            except Exception as json_error:
                print(f'[ERROR] LmsService.get_student_classroom - Cannot parse JSON response: {json_error}')
                print(f'[ERROR] LmsService.get_student_classroom - Response text: {response.text[:500]}')
                return {"error": "Invalid JSON response", "status_code": response.status_code, "text": response.text[:200]}
            
            if response.status_code >= 400:
                print(f'[ERROR] LmsService.get_student_classroom - API returned error status: {response.status_code}')
                print(f'[ERROR] LmsService.get_student_classroom - Error response: {response_json}')
                return response_json
            
            print(f'[DEBUG] LmsService.get_student_classroom - Success!')
            return response_json
            
        except requests.exceptions.Timeout:
            print(f'[ERROR] LmsService.get_student_classroom - Request timeout')
            return {"error": "Request timeout", "message": "LMS API không phản hồi trong thời gian cho phép"}
        except requests.exceptions.ConnectionError as e:
            print(f'[ERROR] LmsService.get_student_classroom - Connection error: {e}')
            return {"error": "Connection error", "message": f"Không thể kết nối đến LMS API: {str(e)}"}
        except requests.exceptions.RequestException as e:
            print(f'[ERROR] LmsService.get_student_classroom - Request exception: {e}')
            return {"error": "Request failed", "message": f"Lỗi khi gọi LMS API: {str(e)}"}
        except Exception as e:
            print(f'[ERROR] LmsService.get_student_classroom - Unexpected error: {type(e).__name__}: {e}')
            import traceback
            print(f'[ERROR] LmsService.get_student_classroom - Traceback: {traceback.format_exc()}')
            return {"error": "Unexpected error", "message": f"Lỗi không xác định: {str(e)}"}

    def get_course_detail(self, course_id: str):
        response = requests.get(
            url=self.base_url + f"/public/courses/{course_id}/lessons/public",
        )
        return response.json()

    def get_student_enrolled_course(self):
        response = requests.get(
            url=self.base_url + f"/public/courses",
            params={"student_name": self.student_name}
        )
        return response.json()

    def get_student_stats(self):
        response = requests.get(
            url=self.base_url + f"/public/stats/student",
            params={"student_name": self.student_name}
        )
        return response.json()

    def get_courses(self, limit: int = 100, offset: int = 0):
        response = requests.get(
            url=self.base_url + f"/public/search/courses",
            params={"limit": limit, "offset": offset}
        )
        return response.json()

    def get_detail_lesson(self, lesson_id: str) -> Lesson | None:
        response = requests.get(
            url=self.base_url + f"/public/lessons/{lesson_id}/public"
        )
        if response.status_code == 200:
            lesson = Lesson.model_validate(response.json())
            return lesson
        return None

    def get_due_schedule(self) -> List[Schedule] | None:
        print(f'[DEBUG] LmsService.get_due_schedule - Starting...')
        print(f'[DEBUG] LmsService.get_due_schedule - student_name: {self.student_name}')
        print(f'[DEBUG] LmsService.get_due_schedule - base_url: {self.base_url}')
        
        url = self.base_url + f"/public/schedules/due"
        params = {"student_name": self.student_name}
        print(f'[DEBUG] LmsService.get_due_schedule - Full URL: {url}')
        print(f'[DEBUG] LmsService.get_due_schedule - Params: {params}')
        
        try:
            response = requests.get(
                url=url,
                params=params,
                timeout=30
            )
            
            print(f'[DEBUG] LmsService.get_due_schedule - Response status code: {response.status_code}')
            print(f'[DEBUG] LmsService.get_due_schedule - Response headers: {dict(response.headers)}')
            
            if response.status_code >= 400:
                print(f'[ERROR] LmsService.get_due_schedule - API returned error status: {response.status_code}')
                try:
                    error_json = response.json()
                    print(f'[ERROR] LmsService.get_due_schedule - Error response: {error_json}')
                except:
                    print(f'[ERROR] LmsService.get_due_schedule - Error response text: {response.text[:500]}')
                return None
            
            try:
                response_json = response.json()
                print(f'[DEBUG] LmsService.get_due_schedule - Response body: {response_json}')
                print(f'[DEBUG] LmsService.get_due_schedule - Response type: {type(response_json)}')
            except Exception as json_error:
                print(f'[ERROR] LmsService.get_due_schedule - Cannot parse JSON response: {json_error}')
                print(f'[ERROR] LmsService.get_due_schedule - Response text: {response.text[:500]}')
                return None
            
            adapter = TypeAdapter(list[Schedule])
            try:
                schedules = adapter.validate_python(response_json)
                print(f'[DEBUG] LmsService.get_due_schedule - Parsed schedules: {len(schedules)} items')
                
                filtered_schedules = [item for item in schedules if item.lesson_id is not None]
                print(f'[DEBUG] LmsService.get_due_schedule - Filtered schedules (with lesson_id): {len(filtered_schedules)} items')
                
                return filtered_schedules
            except Exception as e:
                print(f'[ERROR] LmsService.get_due_schedule - Cannot validate/parse schedules: {e}')
                import traceback
                print(f'[ERROR] LmsService.get_due_schedule - Traceback: {traceback.format_exc()}')
                return None
                
        except requests.exceptions.Timeout:
            print(f'[ERROR] LmsService.get_due_schedule - Request timeout')
            return None
        except requests.exceptions.ConnectionError as e:
            print(f'[ERROR] LmsService.get_due_schedule - Connection error: {e}')
            return None
        except requests.exceptions.RequestException as e:
            print(f'[ERROR] LmsService.get_due_schedule - Request exception: {e}')
            return None
        except Exception as e:
            print(f'[ERROR] LmsService.get_due_schedule - Unexpected error: {type(e).__name__}: {e}')
            import traceback
            print(f'[ERROR] LmsService.get_due_schedule - Traceback: {traceback.format_exc()}')
            return None

# === export ===
lms_service = LmsService()