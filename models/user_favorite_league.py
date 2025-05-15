from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
from models.user import User


class UserFavoriteLeague(Base):
    __tablename__ = "favorite_user_league"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, name="id_user")
    api_league_id = Column(Integer, primary_key=True, name="id_api_league")

    user = relationship("User", back_populates="favorite_league_associations")

    def __repr__(self):
        return f"<UserFavoriteLeague(user_id={self.user_id}, api_league_id={self.api_league_id})>"
