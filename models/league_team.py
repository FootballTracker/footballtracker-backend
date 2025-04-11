from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database.database import Base
from models.league import League


class LeagueTeam(Base):
    __tablename__ = "league_teams"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    base_team_api_id = Column(
        Integer, ForeignKey("base_teams.api_id"), nullable=False, index=True
    )
    venue_id = Column(Integer, ForeignKey("venues.api_id"))
    last_updated = Column(DateTime)

    league = relationship("League", back_populates="teams")
    team = relationship("BaseTeam", back_populates="league_teams")
    venue = relationship("Venue", back_populates="league_teams")
    lineups = relationship("FixtureLineup", back_populates="league_team")
    fixture_statistics = relationship("FixtureStatistic", back_populates="league_team")
    player_season_stats = relationship("PlayerSeasonStat", back_populates="league_team")
    fixture_player_stats = relationship(
        "FixturePlayerStat", back_populates="league_team"
    )
    fixtures_home = relationship(
        "Fixture", back_populates="home_team", foreign_keys="[Fixture.home_team_id]"
    )
    fixtures_away = relationship(
        "Fixture", back_populates="away_team", foreign_keys="[Fixture.away_team_id]"
    )

    __table_args__ = (
        UniqueConstraint("league_id", "base_team_api_id", name="unique_league_team"),
    )
