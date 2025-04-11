from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database.database import Base
from models.base_coach import Coach


class FixtureLineup(Base):
    __tablename__ = "fixture_lineups"

    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(
        Integer,
        ForeignKey("fixtures.api_id"),
        nullable=False,
        index=True,
    )
    league_team_id = Column(
        Integer,
        ForeignKey("league_teams.id"),
        nullable=False,
        index=True,
    )
    coach_api_id = Column(Integer, ForeignKey("base_coaches.api_id"))
    formation = Column(String(10))
    last_updated = Column(DateTime)
    fixture = relationship("Fixture", back_populates="lineups")
    league_team = relationship("LeagueTeam", back_populates="lineups")
    coach = relationship("Coach", back_populates="lineups")

    __table_args__ = (
        UniqueConstraint(
            "fixture_id", "league_team_id", name="unique_fixture_league_team"
        ),
    )
