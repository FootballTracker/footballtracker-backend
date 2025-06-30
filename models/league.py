from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database.database import Base
from sqlalchemy.ext.associationproxy import association_proxy
from models.league_classification import LeagueClassification
from models.fixture import Fixture


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    api_id = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    type = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    logo_url = Column(String)
    last_updated = Column(DateTime)

    teams = relationship("LeagueTeam", back_populates="league")
    standings = relationship("LeagueClassification", back_populates="league")
    fixtures = relationship("Fixture", back_populates="league")
    country = relationship("Country", back_populates="leagues")

    __table_args__ = (
        UniqueConstraint("api_id", "season", name="unique_league_season"),
    )
