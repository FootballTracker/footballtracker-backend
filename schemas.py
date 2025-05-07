from pydantic import BaseModel, EmailStr
from typing import Optional, Union
from datetime import datetime

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
    user_id: Optional[int] = None
    username: Optional[Union[EmailStr, str]] = None
    password: str

class LeagueResponse(BaseModel):
    id: int
    name: str
    country_id: int
    season: int
    start_date: datetime
    end_date: datetime
    logo_url: str
    last_updated: datetime


class TeamInfo(BaseModel):
    score: int
    logo: str | None 
    name: str

class MatchResponse(BaseModel):
    home_team: TeamInfo
    away_team: TeamInfo
    timestamp_match: datetime