from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    SmallInteger,
    String,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database.database import Base


class FixtureStatistic(Base):
    __tablename__ = "fixture_statistics"

    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(
        Integer, ForeignKey("fixtures.api_id"), nullable=False, index=True
    )
    league_team_id = Column(
        Integer,
        ForeignKey("league_teams.id"),
        nullable=False,
        index=True,
    )

    shots_on_goal = Column(SmallInteger)
    shots_off_goal = Column(SmallInteger)
    total_shots = Column(SmallInteger)
    blocked_shots = Column(SmallInteger)
    shots_insidebox = Column(SmallInteger)
    shots_outsidebox = Column(SmallInteger)
    fouls = Column(SmallInteger)
    corner_kicks = Column(SmallInteger)
    offsides = Column(SmallInteger)
    ball_possession = Column(String(10))
    yellow_cards = Column(SmallInteger)
    red_cards = Column(SmallInteger)
    goalkeeper_saves = Column(SmallInteger)
    total_passes = Column(SmallInteger)
    passes_accurate = Column(SmallInteger)
    passes_percentage = Column(String(10))
    last_updated = Column(DateTime)

    fixture = relationship("Fixture", back_populates="statistics")
    league_team = relationship("LeagueTeam", back_populates="fixture_statistics")

    __table_args__ = (
        UniqueConstraint("fixture_id", "league_team_id", name="unique_fixture_team"),
    )
