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

# === export ===
gemini_service = GeminiService()