# To run this code you need to install the following dependencies:
# pip install google-genai
from google.genai import types

def create_user_content(user_input: str) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=user_input),
        ],
    )

def create_model_content(model_input: str) -> types.Content:
    return types.Content(
        role="model",
        parts=[
            types.Part.from_text(text=model_input),
        ]
    )

def create_model_function_call(function_name: str, args: dict):
    return types.Content(
        role="model",
        parts=[types.Part.from_function_call(name=function_name, args=args)]
    )

def create_function_response(function_name: str, response: dict):
    return types.Content(
        role="function",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response=response
            )]
    )