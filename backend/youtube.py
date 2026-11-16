import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv(override=True)
API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

def call_youtube(endpoint, params):
    """Send one request to the YouTube API and return the JSON answer."""

    params["key"] = API_KEY
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def get_channel_id(youtube_url):
    """Turn a YouTube link into a channel ID (e.g. 'UCxxxx')"""
    
    path = urlparse(youtube_url).path
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None

    if parts[0] == "channel" and len(parts) > 1:
        return parts[1]
    if parts[0].startswith("@"):
        params = {"forHandle": parts[0]}
    elif parts[0] == "user" and len(parts) > 1:
        params = {"forUsername": parts[1]}
    else:
        name = parts[1] if parts[0] == "c" and len(parts) > 1 else parts[0]
        params = {"forHandle": "@" + name}

    data = call_youtube("channels", {"part": "id", **params})
    items = data.get("items", [])
    return items[0]["id"] if items else None

def get_youtube_data(youtube_url, max_videos=5):
    """Get channel info and the latest videos."""
    channel_id = get_channel_id(youtube_url)
    if not channel_id:
        return None

    data = call_youtube("channels", {"part": "snippet,statistics,contentDetails", "id": channel_id})
    if not data.get("items"):
        return None
    channel = data["items"][0]

    uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    data = call_youtube("playlistItems", {"part": "snippet", "playlistId": uploads_id, "maxResults": max_videos})

    videos = []
    for item in data.get("items", []):
        s = item["snippet"]
        videos.append({
            "title": s["title"],
            "published": s["publishedAt"][:10],
            "url": f"https://www.youtube.com/watch?v={s['resourceId']['videoId']}",
            "thumbnail": s["thumbnails"].get("medium", {}).get("url"),
        })

    return {
        "channel_name": channel["snippet"]["title"],
        "channel_url": f"https://www.youtube.com/channel/{channel_id}",
        "subscribers": channel["statistics"].get("subscriberCount"),
        "video_count": channel["statistics"].get("videoCount"),
        "latest_videos": videos,
    }

if __name__ == "__main__":
    import json
    result = get_youtube_data("https://www.youtube.com/@GoogleDevelopers")
    print(json.dumps(result, indent=2, ensure_ascii=False))