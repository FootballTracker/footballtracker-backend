from sqlalchemy import (
    Column,
    Integer,
    String,
    SmallInteger,
    Date,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from database.database import Base
from models.player_season_stat import PlayerSeasonStat


class BasePlayer(Base):
    __tablename__ = "base_players"

    api_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    firstname = Column(String(255), nullable=False)
    lastname = Column(String(255))
    age = Column(SmallInteger)
    birth_date = Column(Date)
    birth_place = Column(String(255))
    birth_country_id = Column(Integer, ForeignKey("countries.id"))
    nationality_id = Column(Integer, ForeignKey("countries.id"))
    height = Column(String(10))
    weight = Column(String(10))
    injured = Column(Boolean)
    photo_url = Column(String(255))
    last_updated = Column(DateTime)

    birth_country = relationship(
        "Country", foreign_keys=[birth_country_id], back_populates="birth_players"
    )
    nationality = relationship(
        "Country", foreign_keys=[nationality_id], back_populates="national_players"
    )
    player_season_stats = relationship("PlayerSeasonStat", back_populates="player")
    fixture_player_stats = relationship("FixturePlayerStat", back_populates="player")
