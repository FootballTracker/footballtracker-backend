# models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
from sqlalchemy.ext.associationproxy import association_proxy
# Import BaseTeam if not already implicitly available via Base
from models.base_team import BaseTeam
# Import League if not already implicitly available via Base
from models.league import League

# Assuming Base is correctly imported from database.database
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
    favorite_team_api_id = Column(Integer, ForeignKey("base_teams.api_id"), name="favorite_team", nullable=True)

    # --- Relationships ---

    # Relationship to the favorite BaseTeam
    # Note: You might want to add a back_populates to BaseTeam
    # e.g., in BaseTeam: users_favorited = relationship("User", back_populates="favorite_team")
    favorite_team = relationship("BaseTeam", foreign_keys=[favorite_team_api_id]) # Add back_populates="users_favorited" if added to BaseTeam

    # Relationship to the association object (UserFavoriteLeague)
    # cascade="all, delete-orphan" means if a User is deleted, their entries
    # in the favorite_user_league table are also deleted.
    favorite_league_associations = relationship(
        "UserFavoriteLeague",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin" # Optional: Use selectin loading for efficiency
    )

    # Use association_proxy to easily access the favorite Leagues directly
    # This provides a list-like view of the 'league' attribute from each
    # associated UserFavoriteLeague object.
    favorite_leagues = association_proxy(
        "favorite_league_associations",  # The relationship attribute name above
        "league"                         # The attribute name on UserFavoriteLeague pointing to League
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"