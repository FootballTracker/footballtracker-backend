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

    user_favorite_associations = relationship(
        "UserFavoriteLeague",
        back_populates="league",
        lazy="selectin" # Optional: Use selectin loading for efficiency
        )
    
    favorited_by_users = association_proxy(
        "user_favorite_associations", # Relationship attribute name above
        "user"                        # Attribute name on UserFavoriteLeague pointing to User
    )

    __table_args__ = (
        UniqueConstraint("api_id", "season", name="unique_league_season"),
    )




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