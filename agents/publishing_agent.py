import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class PublishingAgent:
    def __init__(self, config):
        self.access_token = os.environ["META_ACCESS_TOKEN"]
        self.ig_user_id = os.environ["INSTAGRAM_USER_ID"]
        self.imgbb_api_key = os.environ["IMGBB_API_KEY"]
        self.base_url = "https://graph.facebook.com/v19.0"

    def upload_image_to_hosting(self, image_path):
        """Upload a local PNG to imgbb and return its public URL."""
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": self.imgbb_api_key},
                files={"image": f},
            )
        resp.raise_for_status()
        return resp.json()["data"]["url"]

    def publish_single_image(self, image_path, caption):
        image_url = self.upload_image_to_hosting(image_path)

        container = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media",
            data={"image_url": image_url, "caption": caption, "access_token": self.access_token},
        ).json()
        container_id = container["id"]

        time.sleep(5)

        result = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": self.access_token},
        )
        return result.json()

    def publish_carousel(self, image_paths, caption):
        children_ids = []
        for path in image_paths:
            image_url = self.upload_image_to_hosting(path)
            resp = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                data={
                    "image_url": image_url,
                    "is_carousel_item": True,
                    "access_token": self.access_token,
                },
            ).json()
            children_ids.append(resp["id"])
            time.sleep(2)

        carousel = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
                "access_token": self.access_token,
            },
        ).json()
        carousel_id = carousel["id"]

        time.sleep(10)

        result = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media_publish",
            data={"creation_id": carousel_id, "access_token": self.access_token},
        )
        return result.json()

    def publish_reel(self, video_url, caption, cover_url=None):
        data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": self.access_token,
        }
        if cover_url:
            data["cover_url"] = cover_url

        resp = requests.post(f"{self.base_url}/{self.ig_user_id}/media", data=data).json()
        container_id = resp["id"]

        for _ in range(30):
            status = requests.get(
                f"{self.base_url}/{container_id}",
                params={"fields": "status_code", "access_token": self.access_token},
            ).json()
            if status.get("status_code") == "FINISHED":
                break
            time.sleep(10)

        result = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": self.access_token},
        )
        return result.json()
