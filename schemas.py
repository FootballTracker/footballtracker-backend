from pydantic import BaseModel, EmailStr
from typing import Optional, Union, List, Literal
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
    id: int | None
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

class MatchInfo(BaseModel):
    referee: str
    venue: str
    city: str
    status: str
    matchTime: str
    league: str
    leagueLogo: str
    country: str
    countryFlag: str
    season: int
    round: int

class MatchTeamStatistic(BaseModel):
    shotsOnGoal: int
    shotsOffGoal: int
    shotsInsidebox: int
    shotsOutsidebox: int
    totalShots: int
    blockedShots: int
    fouls: int
    cornerKicks: int
    offsides: int
    ballPossession: str
    yellowCards: int
    redCards: int
    goalkeeperSaves: int
    totalPasses: int
    passesAccurate: int
    passesPercentage: str

class MatchTeamsStatistics(BaseModel):
    home_team: MatchTeamStatistic
    away_team: MatchTeamStatistic

class FullMatchResponse(BaseModel):
    match: MatchResponse
    info: MatchInfo
    statistics: MatchTeamsStatistics | None

class EventPlayer(BaseModel):
    id: int
    name: str

class EventAssist(BaseModel):
    id: int | None
    name: str | None

class MatchEvent(BaseModel):
    player: EventPlayer
    assist: EventAssist
    type: Literal['Goal', 'Card', 'Subst', 'Var']
    detail: str
    comments: str | None

class MatchMinuteEvent(BaseModel):
    time: int
    scoreboard: str | None
    home_team: List[MatchEvent]
    away_team: List[MatchEvent]