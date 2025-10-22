from fastapi import APIRouter
from ..models.user import User

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/info")
def get_user_info():
    return {
        "data": User("Teacher", True, True, True)
    }