# publishing_agent.py

import requests
import time

class PublishingAgent:
    def __init__(self, config):
        self.access_token = config["meta_access_token"]
        self.ig_user_id = config["instagram_user_id"]
        self.base_url = "https://graph.facebook.com/v19.0"
    
    def upload_image_to_hosting(self, image_path):
        """
        Instagram API requires publicly accessible URLs.
        Options for free image hosting:
        1. Imgur API (free, no auth needed for anonymous uploads)
        2. Cloudinary (free tier: 25GB storage)
        3. Your own server if you have one
        """
        # Using Imgur (free, anonymous upload)
        url = "https://api.imgur.com/3/upload"
        headers = {"Authorization": "Client-ID YOUR_IMGUR_CLIENT_ID"}
        
        with open(image_path, "rb") as img:
            response = requests.post(url, headers=headers, 
                                    files={"image": img})
        
        data = response.json()
        return data["data"]["link"]
    
    def publish_single_image(self, image_path, caption):
        """Publish a single image post"""
        image_url = self.upload_image_to_hosting(image_path)
        
        # Step 1: Create media container
        container_url = f"{self.base_url}/{self.ig_user_id}/media"
        resp = requests.post(container_url, data={
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token
        })
        container_id = resp.json()["id"]
        
        # Step 2: Wait for processing
        time.sleep(5)
        
        # Step 3: Publish
        publish_url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        result = requests.post(publish_url, data={
            "creation_id": container_id,
            "access_token": self.access_token
        })
        
        return result.json()
    
    def publish_carousel(self, image_paths, caption):
        """Publish a carousel post (multiple images)"""
        
        children_ids = []
        
        # Step 1: Create container for each image
        for path in image_paths:
            image_url = self.upload_image_to_hosting(path)
            resp = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                data={
                    "image_url": image_url,
                    "is_carousel_item": True,
                    "access_token": self.access_token
                }
            )
            children_ids.append(resp.json()["id"])
            time.sleep(2)  # Rate limiting
        
        # Step 2: Create carousel container
        carousel_resp = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
                "access_token": self.access_token
            }
        )
        carousel_id = carousel_resp.json()["id"]
        
        # Step 3: Wait and publish
        time.sleep(10)
        result = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media_publish",
            data={
                "creation_id": carousel_id,
                "access_token": self.access_token
            }
        )
        
        return result.json()
    
    def publish_reel(self, video_url, caption, cover_url=None):
        """Publish a reel (video must be hosted at public URL)"""
        
        data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": self.access_token
        }
        if cover_url:
            data["cover_url"] = cover_url
        
        # Create container
        resp = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media",
            data=data
        )
        container_id = resp.json()["id"]
        
        # Wait for video processing (reels take longer)
        for attempt in range(30):
            status = requests.get(
                f"{self.base_url}/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": self.access_token
                }
            ).json()
            
            if status.get("status_code") == "FINISHED":
                break
            time.sleep(10)
        
        # Publish
        result = requests.post(
            f"{self.base_url}/{self.ig_user_id}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": self.access_token
            }
        )
        
        return result.json()