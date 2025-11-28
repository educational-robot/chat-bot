from typing import List

from google.genai import types

from server.core import context_store
from server.core.config import settings
from server.service.gemini.function_calling import FunctionCallingHandler
from server.service.gemini.gemini import Gemini
from server.service.telegram.telegram_service import telegram_service
from server.util import gemini_utils
from server.util.redis_manager import redis_manager


class GeminiService:
    gemini: Gemini

    def __init__(self):
        system_instructions_prompt = ''
        with open(settings.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            system_instructions_prompt = f.read()

        self.gemini = Gemini(system_instructions_prompt)
        self.function_calling_handler = FunctionCallingHandler(self.gemini)
        self.telegram_service = telegram_service
        self.redis_manager = redis_manager

    def generate_simple_message(self, contents: List[types.Content]):
        result = self.gemini.generate_simple_message(contents)
        if result.text:
            return result.text
        return ''

    def handle_user_message(self, user_input: str):
        print("Received user message: " + user_input)
        print('History length: ', len(context_store.GLOBAL_CHAT_HISTORY))

        if user_input:
            user_content = gemini_utils.create_user_content(user_input)
            context_store.GLOBAL_CHAT_HISTORY.append(user_content)
            
            # Kiểm tra xem có assignments trong history không và user có đang chọn bài tập không
            should_auto_call_submission = self._should_auto_call_assignment_submission(user_input)
            
            if should_auto_call_submission:
                print(f'[DEBUG] GeminiService - Auto-detected assignment selection, forcing get_assignment_submission call')
                # Tự động gọi get_assignment_submission với args rỗng (sẽ tự match)
                from server.core.constants import GET_ASSIGNMENT_SUBMISSION
                self.function_calling_handler.handler(
                    GET_ASSIGNMENT_SUBMISSION,
                    {},
                    context_store.GLOBAL_CHAT_HISTORY
                )
                print(f'[DEBUG] GeminiService - Auto-called get_assignment_submission completed')
            else:
                result = self.gemini.generate_main_content(context_store.GLOBAL_CHAT_HISTORY)

                if result.function_calls:
                    print(f'[DEBUG] GeminiService - Function call detected, number: {len(result.function_calls)}')
                    for idx, func_call in enumerate(result.function_calls):
                        print(f'[DEBUG] GeminiService - Function call #{idx+1}: name={func_call.name}, args={func_call.args}')
                    
                    first_func_call = result.function_calls[0]
                    print(f'[DEBUG] GeminiService - Processing function: {first_func_call.name}')
                    print(f'[DEBUG] GeminiService - Function args: {first_func_call.args}')
                    
                    self.function_calling_handler.handler(
                        first_func_call.name, 
                        first_func_call.args,
                        context_store.GLOBAL_CHAT_HISTORY
                    )
                    print(f'[DEBUG] GeminiService - Function handler completed for: {first_func_call.name}')
                elif result.text:
                    try:
                        self.telegram_service.send_message(result.text)
                        context_store.GLOBAL_CHAT_HISTORY.append(gemini_utils.create_model_content(result.text))
                    except Exception as e:
                        print(e)
                        self.telegram_service.send_error_message()

        self.redis_manager.put_chat_history(history=context_store.GLOBAL_CHAT_HISTORY)
    
    def _should_auto_call_assignment_submission(self, user_input: str) -> bool:
        """Kiểm tra xem có nên tự động gọi get_assignment_submission không"""
        user_lower = user_input.lower().strip()
        
        # Kiểm tra xem có assignments trong history không
        has_assignments = False
        for content in reversed(context_store.GLOBAL_CHAT_HISTORY[-20:]):
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'function_response') and part.function_response:
                        func_response = part.function_response
                        if hasattr(func_response, 'response') and isinstance(func_response.response, dict):
                            response_data = func_response.response
                            if 'assignments' in response_data and response_data.get('assignments'):
                                has_assignments = True
                                break
        
        if not has_assignments:
            return False
        
        # Các trigger words cho thấy user đang chọn bài tập
        assignment_triggers = [
            'bài tập số',
            'bài số',
            'số',
            'kết quả của bài',
            'kết quả bài',
            'xem kết quả',
            'cho tôi xem',
            'đúng',
            'toán',
            'tiếng anh',
            'trắc nghiệm',
            'bài tập',
        ]
        
        # Kiểm tra xem user input có chứa trigger words không
        # Và không phải là câu hỏi ban đầu về kết quả học tập
        is_initial_request = any(word in user_lower for word in ['muốn xem kết quả', 'kết quả học tập', 'bài tập nào'])
        
        if is_initial_request:
            return False
        
        # Nếu có assignments và user đề cập đến bài tập cụ thể
        has_trigger = any(trigger in user_lower for trigger in assignment_triggers)
        
        # Kiểm tra xem có phải là số thứ tự không (ví dụ: "số 1", "số 2")
        import re
        has_number = bool(re.search(r'số\s*\d+|bài\s*\d+|bài tập\s*\d+', user_lower))
        
        # Kiểm tra xem có tên bài tập không (toán, tiếng anh, trắc nghiệm)
        has_assignment_name = any(word in user_lower for word in ['toán', 'tiếng anh', 'trắc nghiệm', 'bài tập tiếng anh', 'bài tập toán'])
        
        result = has_assignments and (has_trigger or has_number or has_assignment_name or user_lower == 'đúng')
        
        print(f'[DEBUG] GeminiService._should_auto_call_assignment_submission - user_input: {user_input}, has_assignments: {has_assignments}, has_trigger: {has_trigger}, has_number: {has_number}, has_assignment_name: {has_assignment_name}, result: {result}')
        
        return result

# === export ===
gemini_service = GeminiService()