from pydantic import BaseModel, EmailStr
from typing import Optional, Union, List, Literal, Dict
from datetime import datetime

# User

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

class UserUpdate(BaseModel):
    id: int
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]
    old_password: Optional[str]

class UserFavoriteLeagueData(BaseModel):
    user_id: int
    api_league_id: int

class UserFavoriteTeamData(BaseModel):
    user_id: int
    team_id: int

class UserFavoritePlayerData(BaseModel):
    user_id: int
    player_id: int


# League

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

# Team

class TeamInfo(BaseModel):
    id: int | None
    score: int
    logo: str | None 
    name: str

class TeamLeagues(BaseModel):
    api_id: str
    name: str
    seasons: List[int]

class TeamLeagueStat(BaseModel):
    name: str
    home: float
    away: float
    total: float

class TeamLeagueGeneralStats(BaseModel):
    mostWinsSeq: int
    mostDrawsSeq: int
    mostLosesSeq: int
    biggestWinHome: str
    biggestWinAway: str
    biggestLoseHome: str
    biggestLoseAway: str
    mostGoalsForHome: int
    mostGoalsForAway: int
    mostGoalsAgainstHome: int
    mostGoalsAgainstAway: int
    penaltyGoals: int
    penaltyMisses: int

class TeamLeagueFormations(BaseModel):
    formation: str
    times: int

class TeamLeagueStatistics(BaseModel):
    infos: List[TeamLeagueStat]
    form: str
    statistics: TeamLeagueGeneralStats | None
    formations: List[TeamLeagueFormations]

# Players schemas

class PlayerResponse(BaseModel):
    id: int
    name: str
    is_favorite: bool
    photo: str

class CountryInfo(BaseModel):
    name: str
    flag_url: Optional[str] = None

class PlayerTeamInfo(BaseModel):
    id: int
    name: str
    logo: str | None

class CompetitionInfo(BaseModel):
    id: int
    name: str
    logo: str

class TeamParticipation(BaseModel):
    team: PlayerTeamInfo
    competitions: List[CompetitionInfo]

class PlayerProfileResponse(BaseModel):
    id: int
    name: str
    firstname: Optional[str]
    lastname: Optional[str]
    birth_date: Optional[datetime]
    birth_place: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    injured: Optional[bool]
    photo_url: Optional[str]
    position: str
    birth_country: Optional[CountryInfo]
    nationality: Optional[CountryInfo]
    teams: List[TeamParticipation]
    is_favorite: bool


# Partidas 

class CountrySchema(BaseModel):
    name: str
    flag_url: Optional[str]

class LeagueSchema(BaseModel):
    name: str
    logo_url: Optional[str]
    season: str
    round: str
    country: CountrySchema

class MatchInfoSchema(BaseModel):
    referee: Optional[str]
    stadium: Optional[str]
    city: Optional[str]
    status: Optional[str]
    date: Optional[str]
    league: LeagueSchema

class TeamStatsSchema(BaseModel):
    name: str
    logo_url: Optional[str]
    stats: Dict[str, Optional[int | str | float]]

class MatchStatisticsResponse(BaseModel):
    information: MatchInfoSchema
    statistics: Dict[str, TeamStatsSchema]

class MatchResponse(BaseModel):
    id: int
    home_team: TeamInfo
    away_team: TeamInfo
    date: datetime

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

class Coach(BaseModel):
    id: int
    name: str
    image: str

class LineupPlayer(BaseModel):
    id: int
    name: str
    number: int

class Lineup(BaseModel):
    coach: Coach
    initial: List[List[LineupPlayer]]
    substitutes: List[LineupPlayer]

class FullLineup(BaseModel):
    home: Lineup
    away: Lineup


# Player match stats

class TeamSummarySchema(BaseModel):
    name: str
    logo_url: Optional[str]
    score: int

class PlayerStatSchema(BaseModel):
    name: str
    player_url: Optional[str]
    team_logo: str
    fixture_id: int
    jersey_number: Optional[int]
    is_starter: Optional[bool]
    game_minute: Optional[int]
    game_number: Optional[int]
    position: Optional[str]
    game_captain: Optional[bool]
    game_substitute: Optional[bool]
    offsides: Optional[int]
    shots_total: Optional[int]
    shots_on: Optional[int]
    goals: Optional[int]
    goals_conceded: Optional[int]
    assists: Optional[int]
    goals_saves: Optional[int]
    passes_total: Optional[int]
    passes_key: Optional[int]
    passes_accuracy: Optional[str]
    tackles_total: Optional[int]
    tackles_blocks: Optional[int]
    tackles_interceptions: Optional[int]
    duels_total: Optional[int]
    duels_won: Optional[int]
    dribbles_attempts: Optional[int]
    dribbles_success: Optional[int]
    fouls_drawn: Optional[int]
    fouls_committed: Optional[int]
    cards_yellow: Optional[int]
    cards_red: Optional[int]
    penalty_won: Optional[int]
    penalty_commited: Optional[int]
    penalty_scored: Optional[int]
    penalty_missed: Optional[int]
    penalty_saved: Optional[int]
    dribbles_past: Optional[int]
    rating: Optional[float]
    grid: Optional[str]

class FixturePlayerStatsResponse(BaseModel):
    home_team: TeamSummarySchema
    away_team: TeamSummarySchema
    player_stats: PlayerStatSchema


# Rankings


class Rank(BaseModel):
    id: str  # player id
    name: str
    value: float
    teamId: str


class Rankings(BaseModel):
    goals: List[Rank]
    assists: List[Rank]
    avgScores: List[Rank]