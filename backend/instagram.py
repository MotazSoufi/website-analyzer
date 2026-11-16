import os
from urllib.parse import urlparse
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv(override=True)
client = ApifyClient(os.getenv("APIFY_TOKEN"))

ACTOR_ID = "apify/instagram-profile-scraper"
NOT_PROFILES = ["p", "reel", "reels", "explore", "stories", "tv"]

def get_instagram_username(instagram_url):
    """Turn 'https://instagram.com/nike/' into 'nike'."""

    parts = [p for p in urlparse(instagram_url).path.split("/") if p]
    if not parts or parts[0] in NOT_PROFILES:
        return None
    return parts[0]

def get_instagram_data(instagram_url, max_posts=5):
    """Get profile info and the latest posts using Apify."""
    username = get_instagram_username(instagram_url)
    if not username:
        return None

    run = client.actor(ACTOR_ID).call(run_input={"usernames": [username]})
    if not run:
        return None

    items = list(client.dataset(run.default_dataset_id).iterate_items())
    if not items:
        return None
    profile = items[0]

    posts = []
    for post in profile.get("latestPosts", [])[:max_posts]:
        posts.append({
            "caption": (post.get("caption") or "")[:300],
            "date": (post.get("timestamp") or "")[:10],
            "likes": post.get("likesCount"),
            "comments": post.get("commentsCount"),
            "url": post.get("url"),
        })

    return {
        "username": profile.get("username", username),
        "full_name": profile.get("fullName"),
        "profile_url": f"https://www.instagram.com/{username}/",
        "followers": profile.get("followersCount"),
        "following": profile.get("followsCount"),
        "post_count": profile.get("postsCount"),
        "bio": profile.get("biography"),
        "is_verified": profile.get("verified"),
        "is_private": profile.get("private"),
        "latest_posts": posts,
    }

if __name__ == "__main__":
    import json
    result = get_instagram_data("https://www.instagram.com/nike/")
    print(json.dumps(result, indent=2, ensure_ascii=False))