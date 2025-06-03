import unittest
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/"

class TestLeagueEndpoints(unittest.TestCase):

    def test_get_leagues(self):
        print("\nTesting GET /leagues ...")
        res = requests.get(f"{BASE_URL}/leagues?user_id=1")
        print("➡️ Status:", res.status_code)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        print("➡️ Response Keys:", data.keys())
        self.assertIn("favorite_leagues", data)
        self.assertIn("all_leagues", data)

        for key in ["favorite_leagues", "all_leagues"]:
            leagues = data[key]
            self.assertIsInstance(leagues, list)
            for league in leagues:
                self.assertIn("id", league)
                self.assertIn("name", league)
                self.assertIn("season", league)
                self.assertIn("logo_url", league)
                self.assertIn("is_favorite", league)
                self.assertIn("api_id", league)

    def test_get_matches_by_league(self):
        print("\nTesting GET /leagues/matches?id=1&season=2023&round=1 ...")

        params = {
            "id": 1,        
            "season": 2023, 
            "round": 1      
        }
        res = requests.get(f"{BASE_URL}/matches", params=params)
        print("➡️ Status:", res.status_code)
        self.assertEqual(res.status_code, 200)

        matches = res.json()
        self.assertIsInstance(matches, list)

        for match in matches:
            self.assertIn("home_team", match)
            self.assertIn("away_team", match)
            self.assertIn("date", match)

            for team in ["home_team", "away_team"]:
                self.assertIn("name", match[team])
                self.assertIn("score", match[team])
                self.assertIn("logo", match[team])
                self.assertIsInstance(match[team]["name"], str)

            self.assertIsInstance(match["date"], str)


    #TODO: Missing the tests of the routes /league and /favorite_leagues

if __name__ == "__main__":
    unittest.main()
