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
from models.base_player import BasePlayer


class FixturePlayerStat(Base):
    __tablename__ = "fixture_player_stats"

    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(
        Integer, ForeignKey("fixtures.api_id"), nullable=False, index=True
    )
    league_team_id = Column(
        Integer, ForeignKey("league_teams.id"), nullable=False, index=True
    )
    base_player_api_id = Column(
        Integer, ForeignKey("base_players.api_id"), nullable=False, index=True
    )
    jersey_number = Column(SmallInteger)
    is_starter = Column(Boolean)
    game_minute = Column(SmallInteger)
    game_number = Column(SmallInteger)
    position = Column(String(50))
    rating = Column(DECIMAL(4, 2))
    game_captain = Column(Boolean)
    game_substitute = Column(Boolean)
    offsides = Column(SmallInteger)
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
    dribbles_past = Column(SmallInteger)
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

    fixture = relationship("Fixture", back_populates="player_stats")
    league_team = relationship("LeagueTeam", back_populates="fixture_player_stats")
    player = relationship("BasePlayer", back_populates="fixture_player_stats")

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "league_team_id",
            "base_player_api_id",
            name="unique_fixture_player",
        ),
    )
