from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, SmallInteger
from sqlalchemy.orm import relationship
from database.database import Base
from models.fixture_lineup import FixtureLineup
from models.fixture_player_stat import FixturePlayerStat
from models.venue import Venue
from models.fixture_statistic import FixtureStatistic


class Fixture(Base):
    __tablename__ = "fixtures"

    api_id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    season = Column(SmallInteger)
    date = Column(DateTime, name="match_DATE")
    status = Column(String(50))
    status_short = Column(String(50))
    venue_id = Column(Integer, ForeignKey("venues.api_id"))
    referee = Column(String)
    home_team_id = Column(
        Integer,
        ForeignKey("league_teams.id"),
        nullable=False,
        index=True,
    )
    away_team_id = Column(
        Integer,
        ForeignKey("league_teams.id"),
        nullable=False,
        index=True,
    )
    home_team_score_goals = Column(SmallInteger)
    away_team_score_goals = Column(SmallInteger)
    elapsed = Column(SmallInteger)
    timezone = Column(String(50))
    round = Column(String(50), nullable=False)
    last_updated = Column(DateTime)

    league = relationship("League", back_populates="fixtures")
    home_team = relationship(
        "LeagueTeam", back_populates="fixtures_home", foreign_keys=[home_team_id]
    )
    away_team = relationship(
        "LeagueTeam", back_populates="fixtures_away", foreign_keys=[away_team_id]
    )
    lineups = relationship("FixtureLineup", back_populates="fixture")
    player_stats = relationship("FixturePlayerStat", back_populates="fixture")
    venue = relationship("Venue", back_populates="fixtures")
    statistics = relationship("FixtureStatistic", back_populates="fixture")
    events = relationship("FixtureEvent", back_populates="fixture")
