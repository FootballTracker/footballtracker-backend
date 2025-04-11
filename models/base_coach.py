from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, Date
from database.database import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Coach(Base):
    __tablename__ = "base_coaches"

    api_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    age = Column(SmallInteger)
    birth_date = Column(Date)
    birth_place = Column(String)
    birth_country_id = Column(Integer, ForeignKey("countries.id"))
    nationality_id = Column(Integer, ForeignKey("countries.id"))
    height = Column(String(10))
    weight = Column(String(10))
    photo_url = Column(String(255))
    last_updated = Column(DateTime)

    birth_country = relationship(
        "Country", foreign_keys=[birth_country_id], back_populates="birth_coaches"
    )
    nationality = relationship(
        "Country", foreign_keys=[nationality_id], back_populates="national_coaches"
    )
    lineups = relationship("FixtureLineup", back_populates="coach")
