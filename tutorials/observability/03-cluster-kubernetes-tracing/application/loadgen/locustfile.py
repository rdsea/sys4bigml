import logging
import os
import random
import time
from pathlib import Path

from locust import HttpUser, between, task

random.seed(12345678)


class ImageUploadUser(HttpUser):
    wait_time = between(1, 1)  # Control pacing between tasks

    script_path = Path(os.path.dirname(os.path.abspath(__file__)))
    ds_path = script_path / "image/"
    device_id = "drone_1"

    def on_start(self):
        try:
            files = os.listdir(self.ds_path)
            self.jpeg_images_list = [
                file for file in files if file.lower().endswith(".jpeg")
            ]
        except Exception as e:
            logging.error(f"Failed to list dataset directory: {e}")
            self.jpeg_images_list = []

    @task
    def upload_image(self):
        if not self.jpeg_images_list:
            logging.warning("No JPEG images found, skipping task.")
            return

        try:
            random_image = random.choice(self.jpeg_images_list)
            image_path = os.path.join(self.ds_path, random_image)

            root, _ = os.path.splitext(image_path)
            _, synset_id = os.path.basename(root).rsplit("_", 1)

            with open(image_path, "rb") as img_file:
                img_data = img_file.read()

            files = {
                "file": ("random_image.jpeg", img_data, "image/jpeg"),
                # "device_id": (None, self.device_id),  # Uncomment if server expects this
            }

            start_time = time.time()
            headers = {
                "Timestamp": str(start_time),
            }
            with self.client.post(
                "/preprocessing", files=files, catch_response=True, headers=headers
            ) as response:
                response_time = (time.time() - start_time) * 1000  # in ms
                if response.status_code == 200:
                    json_response = response.json()
                    print(json_response, synset_id, response_time)
                    response.success()
                else:
                    response.failure(
                        f"Failed with {response.status_code}: {response.text}"
                    )

        except Exception as e:
            logging.exception(f"Exception during upload: {e}")
