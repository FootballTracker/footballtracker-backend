import unittest
import requests
import json
BASE_URL = "http://localhost:8000/"

class TesteTeamsEndpoints(unittest.TestCase):

    def teste_teams(self):

        print("\nTesting GET /teams ...")
        res = requests.get(f"{BASE_URL}/teams/118")
        print("➡️ Status:", res.status_code)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        print(f"Reponse - {json.dumps(data, indent=4)}")

    def teste_mock_teams(self):

        print("\nTesting GET /teams ...")
        res = requests.get(f"{BASE_URL}/teams-mock")
        print("➡️ Status:", res.status_code)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        print(f"Reponse - {json.dumps(data, indent=4)}")

    def test_get_team_details(self):
        print("\nTesting GET /teams/{team_id} ...")
        team_id = 118  # Ensure this ID exists in your test database
        res = requests.get(f"{BASE_URL}/teams/{team_id}")
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())

        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Top-level keys
        self.assertIn("team", data)
        self.assertIn("team_venue", data)
        self.assertIn("leagues", data)
        self.assertIn("last_matches", data)
        self.assertIn("players", data)

        # Team info
        team = data["team"]
        for key in ["id", "name", "logo", "founded", "code", "country", "country_flag"]:
            self.assertIn(key, team)

        # Team venue (nullable)
        if data["team_venue"]:
            venue = data["team_venue"]
            for key in ["address", "name", "city", "capacity", "surface", "image_url"]:
                self.assertIn(key, venue)

        # Leagues
        leagues = data["leagues"]
        self.assertIsInstance(leagues, list)
        for league in leagues:
            for key in ["id", "name", "season", "logo_url"]:
                self.assertIn(key, league)

        # Last matches
        matches = data["last_matches"]
        self.assertIsInstance(matches, list)
        for match in matches:
            for key in ["id", "date", "home_team", "away_team"]:
                self.assertIn(key, match)
            for side in ["home_team", "away_team"]:
                if match[side]:
                    for t_key in ["name", "logo", "score"]:
                        self.assertIn(t_key, match[side])

        # Players (nullable or object)
        players = data["players"]
        if isinstance(players, dict):
            for key in ["coach", "coach_imagem", "goalkeeper", "defensor", "mid_field", "attacker"]:
                self.assertIn(key, players)
                self.assertIsInstance(players[key], list) if key not in ["coach", "coach_imagem"] else None
                for player_list in ["goalkeeper", "defensor", "mid_field", "attacker"]:
                    for player in players.get(player_list, []):
                        self.assertIn("id", player)
                        self.assertIn("player", player)
                        self.assertIn("playerImage", player)
        else:
            # If no players returned, it should be an empty list
            self.assertEqual(players, [])


if __name__ == "__main__":
    unittest.main()