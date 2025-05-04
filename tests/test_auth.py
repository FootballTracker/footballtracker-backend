import unittest
import requests

BASE_URL = "http://localhost:8000/auth"

signup_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
}

signin_email = {
    "username": "test@example.com",
    "password": "securepassword"
}

signin_username = {
    "username": "testuser",
    "password": "securepassword"
}

signin_both = {
    "username": "testuser",
    "password": "securepassword"
}

signin_wrong_password = {
    "username": "test@example.com",
    "password": "wrongpassword"
}


class TestAuthEndpoints(unittest.TestCase):

    def test_signup(self):
        print("\nTesting initial signup...")
        res = requests.post(f"{BASE_URL}/signup", json=signup_data)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        if res.status_code == 400:
            self.assertEqual(res.json(), {"detail": "Username or email already exists"})
        else:
            self.assertEqual(res.status_code, 200)

    def test_signup_duplicate(self):
        print("\nTesting duplicate signup...")
        res = requests.post(f"{BASE_URL}/signup", json=signup_data)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {"detail": "Username or email already exists"})

    def test_signin_with_email(self):
        print("\nTesting signin with email only...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_email)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Welcome back, testuser!")

    def test_signin_with_username(self):
        print("\nTesting signin with username only...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_username)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Welcome back, testuser!")

    def test_signin_with_both(self):
        print("\nTesting signin with both email and username...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_both)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Welcome back, testuser!")

    def test_signin_wrong_password(self):
        print("\nTesting signin with wrong password...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_wrong_password)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "Invalid email or password")


if __name__ == "__main__":
    unittest.main()