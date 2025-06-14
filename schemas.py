from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    favorite_team: int | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    favorite_team: int | None = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str