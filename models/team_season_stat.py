from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    DateTime,
    SmallInteger,
    JSON,
)
from sqlalchemy.orm import relationship
from database.database import Base


class TeamSeasonStat(Base):
    __tablename__ = "team_season_stats"

    id = Column(Integer, primary_key=True, index=True)

    league_team_id = Column(
        Integer, ForeignKey("league_teams.id"), nullable=False, index=True, unique=True
    )

    form = Column(String(100), comment="Ex: WDWLDWLDLDW...")

    # Fixtures
    fixtures_played = Column(SmallInteger)
    fixtures_wins = Column(SmallInteger)
    fixtures_draws = Column(SmallInteger)
    fixtures_loses = Column(SmallInteger)

    # Biggest
    biggest_streak_wins = Column(SmallInteger)
    biggest_streak_draws = Column(SmallInteger)
    biggest_streak_loses = Column(SmallInteger)
    biggest_win = Column(String(25))
    biggest_loss = Column(String(25))

    # Clean Sheets & Failed to Score
    clean_sheets = Column(SmallInteger)
    failed_to_score = Column(SmallInteger)

    # Penalties
    penalty_scored = Column(SmallInteger)
    penalty_missed = Column(SmallInteger)
    penalty_total = Column(SmallInteger)

    # Datos complexos como JSON
    lineups = Column(JSON, comment="Lista de escalações e quantas vezes foi usada")
    cards_by_minute = Column(JSON, comment="Objeto de cartões por intervalo de minutos")

    last_updated = Column(DateTime)

    league_team = relationship("LeagueTeam", back_populates="season_stats")
