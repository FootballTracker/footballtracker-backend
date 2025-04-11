from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    SmallInteger,
    String,
    DateTime,
    Boolean,
    DECIMAL,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database.database import Base


class PlayerSeasonStat(Base):
    __tablename__ = "players_season_stats"

    id = Column(Integer, primary_key=True, index=True)
    base_player_api_id = Column(
        Integer, ForeignKey("base_players.api_id"), nullable=False, index=True
    )
    league_team_id = Column(
        Integer, ForeignKey("league_teams.id"), nullable=False, index=True
    )
    appearances = Column(SmallInteger)
    lineups = Column(SmallInteger)
    minutes = Column(SmallInteger)
    position = Column(String(50))
    rating = Column(DECIMAL(3, 2))
    captain = Column(Boolean)
    substitute_in = Column(SmallInteger)
    substitutes_out = Column(SmallInteger)
    substitutes_bench = Column(SmallInteger)
    shots_total = Column(SmallInteger)
    shots_on = Column(SmallInteger)
    goals = Column(SmallInteger)
    goals_conceded = Column(SmallInteger)
    assists = Column(SmallInteger)
    goals_saves = Column(SmallInteger)
    passes_total = Column(SmallInteger)
    passes_key = Column(SmallInteger)
    passes_accuracy = Column(String(10))
    tackles_total = Column(SmallInteger)
    tackles_blocks = Column(SmallInteger)
    tackles_interceptions = Column(SmallInteger)
    duels_total = Column(SmallInteger)
    duels_won = Column(SmallInteger)
    dribbles_attempts = Column(SmallInteger)
    dribbles_success = Column(SmallInteger)
    dribbles_completed = Column(SmallInteger)
    fouls_drawn = Column(SmallInteger)
    fouls_committed = Column(SmallInteger)
    cards_yellow = Column(SmallInteger)
    cards_red = Column(SmallInteger)
    penalty_won = Column(SmallInteger)
    penalty_commited = Column(SmallInteger)
    penalty_scored = Column(SmallInteger)
    penalty_missed = Column(SmallInteger)
    penalty_saved = Column(SmallInteger)
    last_updated = Column(DateTime)

    player = relationship("BasePlayer", back_populates="player_season_stats")
    league_team = relationship("LeagueTeam", back_populates="player_season_stats")

    __table_args__ = (
        UniqueConstraint(
            "base_player_api_id", "league_team_id", name="unique_player_season"
        ),
    )
