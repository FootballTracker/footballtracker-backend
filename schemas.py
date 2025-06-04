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


class UserLogin(BaseModel):
    user_id: Optional[int] = None
    username: Optional[Union[EmailStr, str]] = None
    password: str

class LeagueResponse(BaseModel):
    id: int
    name: str
    season: int
    logo_url: str
    is_favorite: bool = False
    api_id: int

class SeasonResponse(BaseModel):
    id: int
    season: int

class TeamInfo(BaseModel):
    score: int
    logo: str | None 
    name: str

class MatchResponse(BaseModel):
    id: int
    home_team: TeamInfo
    away_team: TeamInfo
    date: datetime

class UserUpdate(BaseModel):
    id: int
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]
    old_password: Optional[str]

class Standing(BaseModel):
    teamId: int
    teamName: str
    teamLogo: str
    rank: int
    totalGames: int
    victories: int
    draws: int
    loses: int
    goalsFor: int
    goalsAgainst: int
    goalsDiff: int
    points: int