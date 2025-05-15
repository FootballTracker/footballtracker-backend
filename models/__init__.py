# models/__init__.py

# Este arquivo importa todos os modelos para que o SQLAlchemy/Alembic os descubra.

from .country import Country  # Referenciado por BaseTeam, BasePlayer, League, Venue

from .base_team import BaseTeam  # Referenciado por User, LeagueTeam
from .base_player import BasePlayer  # Referenciado por FixtureEvent, PlayerSeasonStat
from .venue import Venue  # Referenciado por Fixture, LeagueTeam
from .league import (
    League,
)  # Referenciado por UserFavoriteLeague, LeagueTeam, Fixture, LeagueClassification

from .user import User  # Referenciado por UserFavoriteLeague
from .user_favorite_league import (
    UserFavoriteLeague,
)  # Referenciado por User, League (importante vir antes de League aqui!)

from .league_classification import LeagueClassification  # Referencia League
from .league_team import LeagueTeam  # Referencia League, BaseTeam, Venue
from .fixture import Fixture  # Referencia League, LeagueTeam (duas vezes), Venue

from .fixture_event import (
    FixtureEvent,
)  # Referencia Fixture, BaseTeam, BasePlayer (duas vezes)
from .fixture_lineup import FixtureLineup  # Referencia Fixture
from .fixture_player_stat import FixturePlayerStat  # Referencia Fixture
from .fixture_statistic import FixtureStatistic  # Referencia Fixture

from .player_season_stat import PlayerSeasonStat  # Referencia BasePlayer, League

__all__ = [
    "Country",
    "BaseTeam",
    "BasePlayer",
    "Venue",
    "League",
    "User",
    "UserFavoriteLeague",
    "LeagueClassification",
    "LeagueTeam",
    "Fixture",
    "FixtureEvent",
    "FixtureLineup",
    "FixturePlayerStat",
    "FixtureStatistic",
    "PlayerSeasonStat",
    "UserFavoritePlayer",
]
