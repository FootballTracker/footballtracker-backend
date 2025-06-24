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

class Token(BaseModel):
    access_token: str
    token_type: str

class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    new_password: Optional[str] = None
    current_password: str

class UserDelete(BaseModel):
    password: str