from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
from models.user import User


class UserFavoritePlayer(Base):
    __tablename__ = "favorite_user_player"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, name="id_user")
    player_api_id = Column(
        Integer,
        ForeignKey("base_players.api_id"),
        primary_key=True,
        name="id_api_player",
    )

    user = relationship("User", back_populates="favorite_player_associations")
    player = relationship("BasePlayer", back_populates="user_favorited_associations")

    def __repr__(self):
        return f"<UserFavoritePlayer(user_id={self.user_id}, player_api_id={self.player_api_id})>"
