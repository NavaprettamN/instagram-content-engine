import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class PublishingAgent:
    def __init__(self, config):
        # ponytail: Meta creds read lazily — generate.yml only uses upload_image_to_hosting
        # and shouldn't fail (or carry the 60-day Meta token) just to host images on imgbb.
        self.access_token = os.environ.get("META_ACCESS_TOKEN")
        self.ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
        # lazy like the Meta creds — the clip/reel path hosts video on Supabase
        # and never touches imgbb, so don't hard-require it just to construct.
        self.imgbb_api_key = os.environ.get("IMGBB_API_KEY")
        # Instagram API with Instagram Login (IGAA token) — no Facebook Page needed.
        self.base_url = "https://graph.instagram.com/v21.0"

    def upload_image_to_hosting(self, image_path):
        """Return a public URL for the image — uploads local files to imgbb, passes URLs through."""
        if str(image_path).startswith("http"):
            return image_path  # already hosted (e.g. from a previous Actions run)
        if not self.imgbb_api_key:
            raise RuntimeError("IMGBB_API_KEY must be set to host images.")
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": self.imgbb_api_key},
                files={"image": f},
            )
        resp.raise_for_status()
        return resp.json()["data"]["url"]

    def upload_video_to_hosting(self, video_path):
        """Public URL for a reel MP4 — uploads local files to Supabase Storage, passes URLs through."""
        if str(video_path).startswith("http"):
            return video_path
        from agents._db import upload_video
        return upload_video(video_path)

    def _require_meta(self):
        if not self.access_token or not self.ig_user_id:
            raise RuntimeError("META_ACCESS_TOKEN and INSTAGRAM_USER_ID must be set to publish.")

    def publish_single_image(self, image_path, caption):
        self._require_meta()
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
        self._require_meta()
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
        self._require_meta()
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
