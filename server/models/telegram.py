from pydantic import BaseModel, Field
from typing import Optional

class AcceptedGiftTypes(BaseModel):
    unlimited_gifts: bool
    limited_gifts: bool
    unique_gifts: bool
    premium_subscription: bool

class Chat(BaseModel):
    id: int
    title: Optional[str] = None
    type: str
    all_members_are_administrators: Optional[bool] = None
    accepted_gift_types: Optional[AcceptedGiftTypes] = None

class FromUser(BaseModel):
    id: int
    is_bot: bool
    first_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None

class Message(BaseModel):
    message_id: int
    from_user: FromUser = Field(alias="from")
    chat: Chat
    date: int
    text: Optional[str] = None

class TelegramUpdate(BaseModel):
    update_id: int
    message: Message
