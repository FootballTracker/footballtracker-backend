import json
import os
import requests
from config import API_HOST, HEADERS
from database.database import async_session_factory
from datetime import datetime, timezone
from models.league import League
from models.base_team import BaseTeam
from models.league_classification import LeagueClassification
from sqlalchemy.future import select
from typing import Optional
from sqlalchemy.exc import IntegrityError


async def fetch_league_classification_and_save_db(params: Optional[dict] = None):
    url = f"https://{API_HOST}/standings"

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        print(data)

        if not isinstance(data.get("response"), list):
            print(
                "Formato JSON inesperado: 'response' não encontrado ou não é uma lista"
            )
            return

        async with async_session_factory() as session:
            for league_classification_data in data["response"]:
                league_info = league_classification_data.get("league")
                if not league_info:
                    print(
                        f"Campos ausentes em league_classification_data: {league_classification_data}"
                    )
                    continue

                api_league_id = league_info.get("id")
                season = league_info.get("season")

                query = select(League).where(
                    League.api_id == api_league_id, League.season == season
                )
                result = await session.execute(query)
                league = result.scalar_one_or_none()

                if not league:
                    print(
                        f"Liga com api_id={api_league_id} e season={season} não encontrada na tabela League."
                    )
                    continue

                league_id_from_db = league.id

                standings = league_info.get("standings")
                if not standings:
                    print(f"Campos ausentes em league_info: {league_info}")
                    continue

                for standing in standings:
                    for team in standing:
                        rank = team.get("rank")
                        team_info = team.get("team", {})
                        id_team = team_info.get("id")

                        if not id_team:
                            print(f"ID do time ausente para ranking {rank}")
                            continue

                        query = select(BaseTeam).where(BaseTeam.api_id == id_team)
                        result = await session.execute(query)
                        base_team = result.scalar_one_or_none()

                        if not base_team:
                            print(
                                f"Time com ID {id_team} não encontrado na tabela BaseTeam."
                            )
                            continue

                        all_stats = team.get("all", {})
                        home_stats = team.get("home", {})
                        away_stats = team.get("away", {})

                        db_classification_league = LeagueClassification(
                            league_id=league_id_from_db,
                            base_team_api_id=id_team,
                            rank=rank,
                            points=team.get("points"),
                            goals_difference=team.get("goalsDiff"),
                            group_name=team.get("group"),
                            form=team.get("form"),
                            status=team.get("status"),
                            description=team.get("description"),
                            all_played=all_stats.get("played"),
                            all_win=all_stats.get("win"),
                            all_draw=all_stats.get("draw"),
                            all_lose=all_stats.get("lose"),
                            all_goals_for=all_stats.get("goals", {}).get("for"),
                            all_goals_against=all_stats.get("goals", {}).get("against"),
                            home_played=home_stats.get("played"),
                            home_win=home_stats.get("win"),
                            home_draw=home_stats.get("draw"),
                            home_lose=home_stats.get("lose"),
                            home_goals_for=home_stats.get("goals", {}).get("for"),
                            home_goals_against=home_stats.get("goals", {}).get(
                                "against"
                            ),
                            away_played=away_stats.get("played"),
                            away_win=away_stats.get("win"),
                            away_draw=away_stats.get("draw"),
                            away_lose=away_stats.get("lose"),
                            away_goals_for=away_stats.get("goals", {}).get("for"),
                            away_goals_against=away_stats.get("goals", {}).get(
                                "against"
                            ),
                            last_updated=datetime.now(timezone.utc).replace(
                                tzinfo=None
                            ),
                        )
                        session.add(db_classification_league)
                        print(
                            f"Classificação da liga {league_id_from_db} para o time {id_team} salva com sucesso."
                        )

            await session.commit()
            print("Classificação das ligas salva com sucesso no banco de dados.")

    except requests.RequestException as e:
        print(f"Erro ao fazer requisição HTTP: {e}")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
    except IntegrityError as e:
        print(f"Erro de integridade no banco de dados: {e}")
        await session.rollback()
    except Exception as e:
        print(f"Erro inesperado: {e}")
