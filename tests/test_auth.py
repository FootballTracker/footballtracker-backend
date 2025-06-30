import unittest
import requests

BASE_URL = "http://localhost:8000/auth"

signup_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
}

signin_email = {
    "email": "test@example.com",
    "password": "securepassword"
}

signin_username = {
    "username": "testuser",
    "password": "securepassword"
}

signin_wrong_password = {
    "email": "test@example.com",
    "password": "wrongpassword"
}


class TestAuthEndpoints(unittest.TestCase):

    def test_signup(self):
        print("\n➡️ Testing initial signup...")
        res = requests.post(f"{BASE_URL}/signup", json=signup_data)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        if res.status_code == 400:
            self.assertEqual(res.json(), {"detail": "Nome de usuário ou email já cadastrados"})
        else:
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["username"], signup_data["username"])

    def test_signup_duplicate(self):
        print("\n➡️ Testing duplicate signup...")
        res = requests.post(f"{BASE_URL}/signup", json=signup_data)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {"detail": "Nome de usuário ou email já cadastrados"})

    def test_signin_with_email(self):
        print("\n➡️ Testing signin with email...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_email)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

    def test_signin_with_username(self):
        print("\n➡️ Testing signin with username...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_username)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

    def test_signin_wrong_password(self):
        print("\n➡️ Testing signin with wrong password...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_wrong_password)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "Invalid credentials")

import unittest
import requests

BASE_URL = "http://localhost:8000/auth"

class TestUserUpdateFlow(unittest.TestCase):

    def setUp(self):
        self.user = {
            "username": "updateuser",
            "email": "update@example.com",
            "password": "originalpass"
        }

        # Try signup
        response = requests.post(f"{BASE_URL}/signup", json=self.user)
        print(response.text)

        # Initial login
        self.refresh_token_and_headers()

    def refresh_token_and_headers(self):
        res = requests.post(f"{BASE_URL}/signin", json={
            "email": self.user["email"],
            "password": self.user["password"]
        })
        assert res.status_code == 200, "Could not sign in"
        self.token = res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_update_username(self):
        print("\n➡️ Updating username...")
        new_username = "updateduser"
        res = requests.put(f"{BASE_URL}/users/me", json={
            "current_password": self.user["password"],
            "username": new_username
        }, headers=self.headers)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["username"], new_username)
        self.user["username"] = new_username  # Update internal state

    def test_update_email(self):
        print("\n➡️ Updating email...")
        new_email = "newemail@example.com"
        res = requests.put(f"{BASE_URL}/users/me", json={
            "current_password": self.user["password"],
            "email": new_email
        }, headers=self.headers)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], new_email)
        self.user["email"] = new_email  # Update internal state

        # Re-authenticate with new email
        self.refresh_token_and_headers()

    def test_update_password(self):
        print("\n➡️ Updating password...")
        new_password = "newsecurepass"
        res = requests.put(f"{BASE_URL}/users/me", json={
            "current_password": self.user["password"],
            "new_password": new_password
        }, headers=self.headers)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)

        # Update password and re-authenticate
        self.user["password"] = new_password
        self.refresh_token_and_headers()

    def tearDown(self):
        print("\n➡️ Deleting user...")

        # Re-authenticate (in case credentials changed)
        try:
            self.refresh_token_and_headers()
        except AssertionError:
            print("⚠️ Could not re-authenticate in tearDown. Skipping deletion.")
            return

        # Attempt deletion
        res = requests.delete(f"{BASE_URL}/users/me", json={
            "password": self.user["password"]
        }, headers=self.headers)
        print("➡️ Deletion status:", res.status_code)
        self.assertIn(res.status_code, (204, 200))


if __name__ == "__main__":
    unittest.main()
