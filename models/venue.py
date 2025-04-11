from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


class Venue(Base):
    __tablename__ = "venues"

    api_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    address = Column(String(255))
    city = Column(String(100))
    capacity = Column(Integer)
    surface = Column(String(50))
    image_url = Column(String(255))
    last_updated = Column(DateTime)

    fixtures = relationship("Fixture", back_populates="venue")
    league_teams = relationship("LeagueTeam", back_populates="venue")
    country = relationship("Country", back_populates="venues")
