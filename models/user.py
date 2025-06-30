# models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
from sqlalchemy.ext.associationproxy import association_proxy
from models.base_team import BaseTeam
from models.league import League
from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    # Store hashed passwords, never plain text
    password = Column(String(255), nullable=False)
    # Explicitly name the foreign key column if it differs from convention
    # or just for clarity. Matches your SQL schema.
    favorite_team_api_id = Column(
        Integer, ForeignKey("base_teams.api_id"), name="favorite_team", nullable=True
    )

    # --- Relationships ---

    # Relationship to the favorite BaseTeam
    # Note: You might want to add a back_populates to BaseTeam
    # e.g., in BaseTeam: users_favorited = relationship("User", back_populates="favorite_team")
    favorite_team = relationship(
        "BaseTeam", foreign_keys=[favorite_team_api_id]
    )  # Add back_populates="users_favorited" if added to BaseTeam

    favorite_player_associations = relationship(
        "UserFavoritePlayer",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    favorite_players = association_proxy("favorite_player_associations", "player")
    favorite_league_associations = relationship(
        "UserFavoriteLeague",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
