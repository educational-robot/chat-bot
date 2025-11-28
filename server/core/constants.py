# function list
from enum import Enum

GET_ALL_LESSON = 'get_all_lesson'
GET_STUDENT_OVERALL = 'get_student_overall'
GET_ENROLLED_COURSES = 'get_enrolled_courses'
GET_DETAIL_LESSON = "get_lesson_content"
GET_STUDENT_CLASSROOM = "get_student_classroom"
GET_LEARN_SCHEDULE = "get_lesson_schedule"
GET_CLASSROOM_ASSIGNMENT = "get_classroom_assignment"
GET_ASSIGNMENT_SUBMISSION = "get_assignment_submission"
CREAT_LESSON_SCHEDULE = "create_lesson_schedule"
# additional function
TAKE_PICTURE_FROM_WEBCAM = "TAKE_PICTURE_FROM_WEBCAM"
TAKE_VIDEO_FROM_WEBCAM = "TAKE_VIDEO_FROM_WEBCAM"

class HistoryMode(Enum):
    REDIS = 'redis'
    IN_MEMORY = 'in_memory'