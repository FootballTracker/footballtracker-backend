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
        self.assertEqual(res.json()["username"], "testuser")

    def test_signin_with_username(self):
        print("\nTesting signin with username only...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_username)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["username"], "testuser")

    def test_signin_with_both(self):
        print("\nTesting signin with both email and username...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_both)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["username"], "testuser")

    def test_signin_wrong_password(self):
        print("\nTesting signin with wrong password...")
        res = requests.post(f"{BASE_URL}/signin", json=signin_wrong_password)
        print("➡️ Status:", res.status_code)
        print("➡️ Response:", res.json())
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "Invalid email or password")


# This test will create a user, try to update and than delete the user
class TestUserUpdateFlow(unittest.TestCase):

    def setUp(self):
        self.original_user = {
            "username": "updateuser",
            "email": "update@example.com",
            "password": "originalpass"
        }
        # Register the user
        res = requests.post(f"{BASE_URL}/signup", json=self.original_user)
        if res.status_code == 200:
            self.user_id = res.json()["id"]
        else:
            # Assume user already exists, log in to get user_id
            signin_res = requests.post(f"{BASE_URL}/signin", json={
                "username": self.original_user["email"],
                "password": self.original_user["password"]
            })
            self.user_id = signin_res.json()["id"]

    def test_update_username(self):
        print("\n➡️ Updating username...")
        new_username = "updatedusername"

        res = requests.put(f"{BASE_URL}/update_user", params={
            "user_id": self.user_id,
            "password": self.original_user["password"],
            "username": new_username
        })
        self.assertEqual(res.status_code, 200)
        print(res.json())
        self.assertEqual(res.json()["message"], "User updated successfully.")

        # Verify login still works with new username
        login_res = requests.post(f"{BASE_URL}/signin", json={
            "username": new_username,
            "password": self.original_user["password"]
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()["username"], new_username)

        # Save for tearDown cleanup
        self.original_user["username"] = new_username

    def test_update_email(self):
        print("\n➡️ Updating email...")
        new_email = "newemail@example.com"

        res = requests.put(f"{BASE_URL}/update_user", params={
            "user_id": self.user_id,
            "password": self.original_user["password"],
            "email": new_email
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "User updated successfully.")

        # Verify login with new email
        login_res = requests.post(f"{BASE_URL}/signin", json={
            "username": new_email,
            "password": self.original_user["password"]
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()["email"], new_email)

        # Save for tearDown cleanup
        self.original_user["email"] = new_email

    def test_update_password(self):
        print("\n➡️ Updating password...")
        new_password = "newsecurepassword"

        res = requests.put(f"{BASE_URL}/update_user", params={
            "user_id": self.user_id,
            "password": self.original_user["password"],
            "new_password": new_password
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "User updated successfully.")

        # Verify login with new password
        login_res = requests.post(f"{BASE_URL}/signin", json={
            "username": self.original_user["email"],
            "password": new_password
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()["email"], self.original_user["email"])

        # Save for tearDown cleanup
        self.original_user["password"] = new_password

    def tearDown(self):
        print("\n➡️ Cleaning up: deleting user...")
        res = requests.post(f"{BASE_URL}/user_delete", json={
            "user_id": self.user_id,
            "password": self.original_user["password"]
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("deleted successfully", res.json()["message"])



if __name__ == "__main__":
    unittest.main()