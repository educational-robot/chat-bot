from contextlib import asynccontextmanager
from typing import List

from starlette.datastructures import State

from fastapi import FastAPI

from server.core.gemini import GeminiModel
from server.routers import users, hooks
from starlette.middleware.cors import CORSMiddleware

from server.service.learning_notification_service import LearningNotificationService

BASE_URL = "/api/v1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("On Startup")
    with open("server/res/system_instructions_promt.txt", "r", encoding="utf-8") as f:
        app.state.text_data = f.read()

    app.state.gemini_model = GeminiModel(app.state.text_data)

    # Start scan schedules of student for schedule notifications
    learning_notification_service = LearningNotificationService()
    learning_notification_service.scan_schedule()
    learning_notification_service.schedule_daily_scan()

    yield  # App chạy tại đây

    # --- Shutdown ---
    print("🛑 App shutting down...")

app = FastAPI(lifespan=lifespan)
app.state = State()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(users.router, prefix=BASE_URL)
app.include_router(hooks.router, prefix=BASE_URL)