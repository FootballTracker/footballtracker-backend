import unittest
import requests
import os

BASE_URL = "http://localhost:8000/user"
TEST_IMAGE_PATH = "test_image.jpg"

class TestUserImageRoutes(unittest.TestCase):

    def setUp(self):
        # Create a small dummy image file for upload testing
        with open(TEST_IMAGE_PATH, "wb") as f:
            f.write(os.urandom(1024))  # 1KB dummy image

        self.test_user_id = 99999

    def tearDown(self):
        # Clean up dummy image file
        if os.path.exists(TEST_IMAGE_PATH):
            os.remove(TEST_IMAGE_PATH)

    def test_post_user_image(self):
        print("\nTesting POST /user/image ...")

        with open(TEST_IMAGE_PATH, "rb") as image_file:
            files = {'image': ('test.jpg', image_file, 'image/jpeg')}
            data = {'user_id': self.test_user_id}

            res = requests.post(f"{BASE_URL}/image", files=files, data=data)

        print("➡️ Status:", res.status_code)
        self.assertEqual(res.status_code, 200)

        response = res.json()
        self.assertEqual(response["filename"], str(self.test_user_id))
        self.assertEqual(response["content_type"], "jpeg")
        self.assertIn("message", response)

    def test_get_user_image(self):
        print("\nTesting GET /user/{user_id}/image ...")

        res = requests.get(f"{BASE_URL}/{self.test_user_id}/image")
        print("➡️ Status:", res.status_code)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"].startswith("image/"), True)

    def test_delete_user_image(self):
        print("\nTesting DELETE /user/image ...")

        res = requests.delete(f"{BASE_URL}/image", params={"user_id": self.test_user_id})
        print("➡️ Status:", res.status_code)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Imagem removida com sucesso")

        # Check if the image is actually removed
        follow_up = requests.get(f"{BASE_URL}/{self.test_user_id}/{self.test_user_id}.jpeg")
        self.assertEqual(follow_up.status_code, 404)

if __name__ == "__main__":
    unittest.main()
