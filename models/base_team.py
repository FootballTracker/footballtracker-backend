from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    SmallInteger,
)
from sqlalchemy.orm import relationship
from database.database import Base
from models.league_team import LeagueTeam
from models.fixture_event import FixtureEvent


class BaseTeam(Base):
    __tablename__ = "base_teams"

    api_id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    name = Column(String, nullable=False, index=True)
    code = Column(String(10))
    founded = Column(SmallInteger)
    national = Column(Boolean)
    logo_url = Column(String(255))
    last_updated = Column(DateTime)

    league_teams = relationship("LeagueTeam", back_populates="team")
    league_standings = relationship("LeagueClassification", back_populates="team")
    country = relationship("Country", back_populates="base_teams")
    fixture_events = relationship(
        "FixtureEvent", back_populates="team", foreign_keys=[FixtureEvent.team_api_id]
    )
