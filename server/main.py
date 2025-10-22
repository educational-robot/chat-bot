from fastapi import FastAPI
from server.routers import users, hooks
from starlette.middleware.cors import CORSMiddleware

BASE_URL = "/api/v1"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(users.router, prefix=BASE_URL)
app.include_router(hooks.router, prefix=BASE_URL)