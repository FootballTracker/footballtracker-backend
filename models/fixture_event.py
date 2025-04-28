from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


class FixtureEvent(Base):
    __tablename__ = "fixture_events"

    id = Column(Integer, primary_key=True, index=True)
    fixture_api_id = Column(Integer, ForeignKey("fixtures.api_id"), nullable=False)
    team_api_id = Column(Integer, ForeignKey("base_teams.api_id"), nullable=False)
    player_api_id = Column(Integer, ForeignKey("base_players.api_id"), nullable=True)
    assist_player_api_id = Column(
        Integer, ForeignKey("base_players.api_id"), nullable=True
    )

    time_elapsed = Column(Integer, nullable=False)
    time_extra = Column(Integer, nullable=True)

    type = Column(String(50), nullable=False)
    detail = Column(String(100), nullable=False)
    comments = Column(String, nullable=True)

    last_updated = Column(DateTime, nullable=False)

    fixture = relationship("Fixture", back_populates="events")
    team = relationship("BaseTeam", foreign_keys=[team_api_id])
    player = relationship("BasePlayer", foreign_keys=[player_api_id])
    assist = relationship("BasePlayer", foreign_keys=[assist_player_api_id])
