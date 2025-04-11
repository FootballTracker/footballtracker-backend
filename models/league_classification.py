from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    SmallInteger,
    String,
    DateTime,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import relationship
from database.database import Base


class LeagueClassification(Base):
    __tablename__ = "league_classification"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    base_team_api_id = Column(
        Integer,
        ForeignKey("base_teams.api_id"),
        nullable=False,
        index=True,
    )
    rank = Column(SmallInteger)
    points = Column(SmallInteger)
    goals_difference = Column(SmallInteger)
    group_name = Column(String(255))
    form = Column(String(50))
    status = Column(String(50))
    description = Column(Text)
    all_played = Column(SmallInteger)
    all_win = Column(SmallInteger)
    all_draw = Column(SmallInteger)
    all_lose = Column(SmallInteger)
    all_goals_for = Column(SmallInteger)
    all_goals_against = Column(SmallInteger)
    home_played = Column(SmallInteger)
    home_win = Column(SmallInteger)
    home_draw = Column(SmallInteger)
    home_lose = Column(SmallInteger)
    home_goals_for = Column(SmallInteger)
    home_goals_against = Column(SmallInteger)
    away_played = Column(SmallInteger)
    away_win = Column(SmallInteger)
    away_draw = Column(SmallInteger)
    away_lose = Column(SmallInteger)
    away_goals_for = Column(SmallInteger)
    away_goals_against = Column(SmallInteger)
    last_updated = Column(DateTime)

    league = relationship("League", back_populates="standings")
    team = relationship("BaseTeam", back_populates="league_standings")

    __table_args__ = (
        UniqueConstraint(
            "league_id", "base_team_api_id", name="unique_league_classification"
        ),
    )
