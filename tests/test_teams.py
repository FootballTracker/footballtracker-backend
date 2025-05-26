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

if __name__ == "__main__":
    unittest.main()