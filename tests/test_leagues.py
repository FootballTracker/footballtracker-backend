import unittest
import requests
import json

BASE_URL = "http://localhost:8000"

class TestLeagueEndpoints(unittest.TestCase):

    def test_get_leagues(self):
        print("\nTesting GET /leagues ...")
        res = requests.get(f"{BASE_URL}/leagues", params={"user_id": 1})
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("favorite_leagues", data)
        self.assertIn("all_leagues", data)

        for key in ["favorite_leagues", "all_leagues"]:
            self.assertIsInstance(data[key], list)
            for league in data[key]:
                self.assertIn("id", league)
                self.assertIn("name", league)
                self.assertIn("season", league)
                self.assertIn("logo_url", league)
                self.assertIn("is_favorite", league)
                self.assertIn("api_id", league)

    def test_get_matches_by_league(self):
        print("\nTesting GET /matches ...")
        params = {
            "id": 1,
            "season": 2023,
            "round": 1
        }
        res = requests.get(f"{BASE_URL}/matches", params=params)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))
        self.assertEqual(res.status_code, 200)

        matches = res.json()
        self.assertIsInstance(matches, list)
        for match in matches:
            self.assertIn("home_team", match)
            self.assertIn("away_team", match)
            self.assertIn("date", match)

    def test_get_favorite_leagues(self):
        print("\nTesting GET /favorite_leagues ...")
        res = requests.get(f"{BASE_URL}/favorite_leagues", params={"user_id": 1})
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))
        self.assertEqual(res.status_code, 200)

        favorite_leagues = res.json()
        self.assertIsInstance(favorite_leagues, list)
        for league in favorite_leagues:
            self.assertIn("id", league)
            self.assertIn("name", league)
            self.assertIn("season", league)
            self.assertIn("logo_url", league)
            self.assertIn("is_favorite", league)
            self.assertTrue(league["is_favorite"])
            self.assertIn("api_id", league)

    def test_get_league_by_id(self):
        print("\nTesting GET /league ...")
        params = {
            "league_id": 1,
            "user_id": 1
        }
        res = requests.get(f"{BASE_URL}/league", params=params)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))

        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("league", data)
        self.assertIn("seasons", data)

        league = data["league"]
        seasons = data["seasons"]

        self.assertIsInstance(league, dict)
        for key in ["id", "name", "season", "logo_url", "is_favorite", "api_id"]:
            self.assertIn(key, league)

        self.assertIsInstance(seasons, list)
        for season in seasons:
            self.assertIn("id", season)
            self.assertIn("season", season)

    def test_get_league_classification(self):
        print("\nTesting GET /league/{league_id}/classification ...")
        league_id = 1  # Use an ID that exists in your database with classification data
        res = requests.get(f"{BASE_URL}/league/{league_id}/classification")
        print("➡️ Status:", res.status_code)

        self.assertEqual(res.status_code, 200)

        standings = res.json()
        print("➡️ Response:", json.dumps(standings, indent=4))
        self.assertIsInstance(standings, list)

        if standings:  # Only validate fields if the list is not empty
            for standing in standings:
                for key in [
                    "teamId", "teamName", "teamLogo", "rank",
                    "totalGames", "victories", "draws", "loses",
                    "goalsFor", "goalsAgainst", "goalsDiff", "points"
                ]:
                    self.assertIn(key, standing)

                self.assertIsInstance(standing["teamId"], int)
                self.assertIsInstance(standing["teamName"], str)
                self.assertIsInstance(standing["teamLogo"], str)
                self.assertIsInstance(standing["rank"], int)
                self.assertIsInstance(standing["totalGames"], int)
                self.assertIsInstance(standing["victories"], int)
                self.assertIsInstance(standing["draws"], int)
                self.assertIsInstance(standing["loses"], int)
                self.assertIsInstance(standing["goalsFor"], int)
                self.assertIsInstance(standing["goalsAgainst"], int)
                self.assertIsInstance(standing["goalsDiff"], int)
                self.assertIsInstance(standing["points"], int)

if __name__ == "__main__":
    unittest.main()
