# models/user_favorite_league.py
from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from database.database import Base
# Import User and League if not implicitly available via Base
from models.user import User
from models.league import League

# Assuming Base is correctly imported from database.database
from database.database import Base


class UserFavoriteLeague(Base):
    __tablename__ = "favorite_user_league"

    # Map Python attribute names (snake_case) to DB column names (if different)
    # Use primary_key=True for composite primary key components
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, name="id_user")
    league_id = Column(Integer, ForeignKey("leagues.id"), primary_key=True, name="id_league")

    # --- Relationships ---

    # Relationship back to User
    user = relationship("User", back_populates="favorite_league_associations")

    # Relationship back to League
    # Note: You need to add the corresponding relationship to the League model
    # e.g., in League: user_favorite_associations = relationship("UserFavoriteLeague", back_populates="league")
    #                 favorited_by_users = association_proxy("user_favorite_associations", "user")
    league = relationship("League", back_populates="user_favorite_associations") # Add back_populates="user_favorite_associations" to League

    # Explicitly define the composite primary key constraint (good practice)
    # SQLAlchemy might infer it from primary_key=True on columns, but explicit is safer.
    # __table_args__ = (
    #     PrimaryKeyConstraint('id_user', 'id_league'),
    # )
    # No need for __table_args__ if primary_key=True is set correctly on the columns

    def __repr__(self):
        return f"<UserFavoriteLeague(user_id={self.user_id}, league_id={self.league_id})>"