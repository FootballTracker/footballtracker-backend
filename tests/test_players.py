import unittest
import requests
import json

BASE_URL = "http://localhost:8000"

class TestPlayerProfileEndpoint(unittest.TestCase):

    def test_get_player_profile(self):
        print("\nTesting GET /players/{player_id} ...")
        player_id = 10180 
        
        
        res = requests.get(f"{BASE_URL}/players/{player_id}")
        
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", json.dumps(res.json(), indent=4))
        
        self.assertEqual(res.status_code, 200)

        data = res.json()

        # Top-level keys
        for key in [
            "name", "firstname", "lastname", "birth_date", "birth_place",
            "height", "weight", "injured", "photo_url", "birth_country",
            "nationality", "teams"
        ]:
            self.assertIn(key, data)

        # Country Info
        if data["birth_country"]:
            for key in ["name", "flag_url"]:
                self.assertIn(key, data["birth_country"])

        if data["nationality"]:
            for key in ["name", "flag_url"]:
                self.assertIn(key, data["nationality"])

        # Teams and competitions
        self.assertIsInstance(data["teams"], list)
        for team_info in data["teams"]:
            self.assertIn("team", team_info)
            self.assertIn("competitions", team_info)
            self.assertIsInstance(team_info["competitions"], list)
            self.assertIn("name", team_info["team"])


if __name__ == "__main__":
    unittest.main()
