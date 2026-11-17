from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    sex: bool = False
    date_of_birth: date
    first_name: str = Field(min_length=1, max_length=32)
    last_name: str = Field(min_length=1, max_length=32)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    goal: int = Field(default=0, ge=0, le=3)
    first_name: str = Field(default="", max_length=32)
    last_name: str = Field(default="", max_length=32)
    description: str = ""
    city: str | None = None
    height: int | None = None
    weight: int | None = None
    leading: int = Field(default=0, ge=0, le=11)
    where_leading: int = Field(default=0, ge=0, le=2)
    bouldering: int = Field(default=0, ge=0, le=11)
    where_bouldering: int = Field(default=0, ge=0, le=2)
    speed: bool = False
    alpinism: bool = False
    belay: int = Field(default=0, ge=0, le=2)
    belay_description: str = ""

class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    goal: int
    first_name: str
    last_name: str
    description: str
    city: str | None
    height: int | None
    weight: int | None
    avatar: str | None

class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    chat_id: int
    sender_id: int
    text: str
    is_read: bool
    created_at: datetime
