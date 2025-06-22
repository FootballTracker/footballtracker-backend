import unittest
import requests
import json

BASE_URL = "http://localhost:8000"

class TestFixturesEndpoint(unittest.TestCase):

    def test_get_match_statistics(self):
        print("\nTesting GET /match_statistics/{fixture_id} ...")
        fixture_id = 1005650
        
        res = requests.get(f"{BASE_URL}/match_statistics/{fixture_id}")
        
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))
        
        self.assertEqual(res.status_code, 200)

        data = res.json()

        # Check top-level keys in response
        self.assertIn("information", data)
        self.assertIn("statistics", data)

        info = data["information"]
        stats = data["statistics"]

        # Check information fields
        for key in ["referee", "stadium", "city", "status", "date", "league"]:
            self.assertIn(key, info)

        league = info["league"]
        for key in ["name", "logo_url", "season", "round", "country"]:
            self.assertIn(key, league)

        country = league["country"]
        if country:
            for key in ["name", "flag_url"]:
                self.assertIn(key, country)

        # statistics should have keys: home_team and away_team
        self.assertIn("home_team", stats)
        self.assertIn("away_team", stats)

        for side in ["home_team", "away_team"]:
            team_stats = stats[side]
            self.assertIn("name", team_stats)
            self.assertIn("logo_url", team_stats)
            self.assertIn("stats", team_stats)

            expected_stats_keys = [
                "shots_on_goal", "shots_off_goal", "total_shots", "blocked_shots",
                "shots_insidebox", "shots_outsidebox", "fouls", "corner_kicks",
                "offsides", "ball_possession", "yellow_cards", "red_cards",
                "goalkeeper_saves", "total_passes", "passes_accurate",
                "passes_percentage", "expected_goals"
            ]
            for stat_key in expected_stats_keys:
                self.assertIn(stat_key, team_stats["stats"])

    def test_get_get_player_match_statistics(self):
        fixture_id = 1005650
        base_player_id = 80296
        
        print(f"\nTesting GET /get_player_match_statistics/{fixture_id}/player/{base_player_id} ...")
        res = requests.get(f"{BASE_URL}/get_player_match_statistics/{fixture_id}/player/{base_player_id}")
        
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))
        
        self.assertEqual(res.status_code, 200)
        
        data = res.json()

        # Check home_team and away_team in response
        self.assertIn("home_team", data)
        self.assertIn("away_team", data)
        self.assertIn("player_stats", data)

        # Check home_team fields
        for key in ["name", "logo_url", "score"]:
            self.assertIn(key, data["home_team"])

        # Check away_team fields
        for key in ["name", "logo_url", "score"]:
            self.assertIn(key, data["away_team"])

        # Check keys in each player stat
        expected_player_stat_keys = {
            "fixture_id", "name", "player_url", "team_logo",
            "jersey_number", "is_starter", "game_minute", "game_number",
            "position", "game_captain", "game_substitute", "offsides",
            "shots_total", "shots_on", "goals", "goals_conceded", "assists",
            "goals_saves", "passes_total", "passes_key", "passes_accuracy",
            "tackles_total", "tackles_blocks", "tackles_interceptions",
            "duels_total", "duels_won", "dribbles_attempts", "dribbles_success",
            "fouls_drawn", "fouls_committed", "cards_yellow", "cards_red",
            "penalty_won", "penalty_commited", "penalty_scored", "penalty_missed",
            "penalty_saved", "dribbles_past", "rating", "grid",
        }

        for key in expected_player_stat_keys:
            self.assertIn(key, data["player_stats"])


if __name__ == "__main__":
    unittest.main()
