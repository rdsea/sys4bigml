import argparse
import asyncio
import logging
import os
import random
import time

import aiohttp
from aiohttp.client_exceptions import ClientError

username = "0"
# password = "password"
group_id = "0"
credentials = f"{username}:{group_id}"
# encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {}


async def send_request(url, jpeg_images_list, requesting_interval, device_id):
    while True:
        try:
            random_image = random.choice(jpeg_images_list)
            image_path = os.path.join(ds_path, random_image)

            # Extract the synset_id from the file name
            root, _ = os.path.splitext(image_path)
            _, synset_id = os.path.basename(root).rsplit("_", 1)

            # Open the image file as binary
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()

            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file",
                    img_data,
                    filename="random_image.jpeg",
                    content_type="image/jpeg",
                )

                # form_data.add_field("device_id", device_id)
                # headers = {"Host": "object-classification.test.com"}
                print(f"Sending request at {start_time}")
                headers = {
                    "Timestamp": str(start_time),
                }
                async with session.post(
                    url, data=form_data, headers=headers, timeout=300
                ) as response:
                    json_response = await response.json(content_type=None)
                    if response.status == 200:
                        print(
                            json_response, synset_id, (time.time() - start_time) * 1000
                        )
                    else:
                        print(
                            f"Request failed with status {response.status}\n {json_response}"
                        )

        except ClientError as e:
            logging.error(f"HTTP Request failed: {e}")
        except Exception as e:
            logging.exception(f"Unexpected error: {e}")

        await asyncio.sleep(requesting_interval)


async def main():
    parser = argparse.ArgumentParser(
        description="Argument for choosing model to request"
    )
    parser.add_argument(
        "--ds_path",
        type=str,
        help="Test dataset path",
        default="./image/",
    )
    parser.add_argument(
        "--rate", type=int, help="Number of requests per second", default=1
    )
    parser.add_argument(
        "--device_id", type=str, help="Specify device ID", default="aaltosea_cam_01"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Request URL",
        default="http://localhost:5010/preprocessing",
        # default="http://192.168.49.2/preprocessing-gateway",  # with istio working
        # default="http://localhost:5010/preprocessing",  # with istio working
    )

    args = parser.parse_args()
    global ds_path
    ds_path = args.ds_path
    req_rate = args.rate
    url = args.url

    files = os.listdir(ds_path)
    jpeg_images_list = [file for file in files if file.lower().endswith(".jpeg")]
    requesting_interval = 1.0 / req_rate
    device_id = "drone_1"
    await send_request(url, jpeg_images_list, requesting_interval, device_id)


if __name__ == "__main__":
    asyncio.run(main())
