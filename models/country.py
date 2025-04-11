from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database.database import Base
from models.base_team import BaseTeam
from models.base_coach import Coach


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    flag_url = Column(String)
    last_updated = Column(DateTime)

    base_teams = relationship("BaseTeam", back_populates="country")
    birth_players = relationship(
        "BasePlayer",
        foreign_keys="[BasePlayer.birth_country_id]",
        back_populates="birth_country",
    )
    national_players = relationship(
        "BasePlayer",
        foreign_keys="[BasePlayer.nationality_id]",
        back_populates="nationality",
    )
    leagues = relationship("League", back_populates="country")
    birth_coaches = relationship(
        "Coach",
        foreign_keys="[Coach.birth_country_id]",
        back_populates="birth_country",
    )
    national_coaches = relationship(
        "Coach",
        foreign_keys="[Coach.nationality_id]",
        back_populates="nationality",
    )
    venues = relationship("Venue", back_populates="country")
