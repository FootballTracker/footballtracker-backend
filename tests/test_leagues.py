import unittest
import requests

BASE_URL = "http://localhost:8000/leagues"

class TestLeagueEndpoints(unittest.TestCase):

    def test_get_leagues(self):
        print("\nTesting GET /leagues/leagues ...")
        res = requests.get(f"{BASE_URL}/leagues")
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())

        self.assertEqual(res.status_code, 200)

        leagues = res.json()
        self.assertIsInstance(leagues, list)
        if leagues:
            league = leagues[0]
            self.assertIn("id", league)
            self.assertIn("name", league)
            self.assertIn("country_id", league)
            self.assertIn("season", league)
            self.assertIn("start_date", league)
            self.assertIn("end_date", league)
            self.assertIn("logo_url", league)
            self.assertIn("last_updated", league)

            # Optionally, assert values/types
            self.assertIsInstance(league["id"], int)
            self.assertIsInstance(league["name"], str)
            self.assertIsInstance(league["country_id"], int)

    def test_get_matches_by_league(self):
        print("\nTesting GET /leagues/matches?league_id=1 ...")
        res = requests.get(f"{BASE_URL}/matches?league_id=1")
        print("➡️ Status:", res.status_code)

        self.assertEqual(res.status_code, 200)

        matches = res.json()
        print(f"➡️ Total matches: {len(matches)}")

        self.assertIsInstance(matches, list)
        self.assertEqual(len(matches), 380)  # Expecting 380 matches

        if matches:
            match = matches[0]
            self.assertIn("home_team", match)
            self.assertIn("away_team", match)
            self.assertIn("timestamp_match", match)

            self.assertIn("name", match["home_team"])
            self.assertIn("score", match["home_team"])
            self.assertIn("logo", match["home_team"])

            self.assertIn("name", match["away_team"])
            self.assertIn("score", match["away_team"])
            self.assertIn("logo", match["away_team"])

            self.assertIsInstance(match["timestamp_match"], str)


if __name__ == "__main__":
    unittest.main()
