# To run this code you need to install the following dependencies:
# pip install google-genai
from typing import List

from google.genai import types
from google.genai.types import Content

from server.core import context_store
from server.core.gemini import GeminiModel
from server.util import telegram_utils, function_calling
from server.util.redis_manager import *

RESPONSE_MSG_ERROR = 'Xin chào hiện tại tôi đang gặp một chút sự cố, phụ huynh vui lòng thử lại'

default_gemini_model = GeminiModel('')

def generate(user_input: str, gemini_model: GeminiModel):
    print('History length: ', len(context_store.GLOBAL_CHAT_HISTORY))

    model = "gemini-2.5-flash"
    if user_input:
        user_content = types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_input),
            ],
        )
        context_store.GLOBAL_CHAT_HISTORY.append(user_content)

        res = gemini_model.client.models.generate_content(
                model=model,
                contents=context_store.GLOBAL_CHAT_HISTORY,
                config=gemini_model.generate_content_config,
        )
        if res.function_calls:
            print('function call number: ', len(res.function_calls))
            function_calling.call(res.function_calls[0].name, res.function_calls[0].args, gemini_model.client,
                                  context_store.GLOBAL_CHAT_HISTORY)
        elif res.text:
            try:
                telegram_utils.send_telegram_message(res.text)
                context_store.GLOBAL_CHAT_HISTORY.append(
                    types.Content(
                        role="model",
                        parts=[
                            types.Part.from_text(text=res.text),
                        ]
                ))
            except Exception as e:
                print(e)
                telegram_utils.send_telegram_message(RESPONSE_MSG_ERROR)

        put_chat_history(history=context_store.GLOBAL_CHAT_HISTORY)

def generate_single_message(contents: List[Content]) -> str:
    res = default_gemini_model.client.models.generate_content(
        model=default_gemini_model.model,
        contents=contents
    )
    if res.text:
        return res.text
    return ''