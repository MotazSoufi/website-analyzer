import requests
from datetime import datetime

def find_wayback_snapshot(url, max_age_days=365):
    """Find a recent archived copy of the page. Returns None if there isn't a usable one."""

    snapshot = None
    for attempt in range(2):
        response = requests.get(
            "https://archive.org/wayback/available",
            params={"url": url},
            timeout=10,
        )
        response.raise_for_status()
        snapshot = response.json().get("archived_snapshots", {}).get("closest")
        if snapshot:
            break

    if not snapshot or not snapshot.get("available") or snapshot.get("status") != "200":
        return None

    timestamp = snapshot["timestamp"]
    date = datetime.strptime(timestamp[:8], "%Y%m%d")
    if (datetime.now() - date).days > max_age_days:
        return None

    snapshot_url = snapshot["url"].replace(f"/web/{timestamp}/", f"/web/{timestamp}if_/")
    snapshot_url = snapshot_url.replace("http://", "https://", 1)

    return {"url": snapshot_url, "date": date.strftime("%Y-%m-%d")}

if __name__ == "__main__":
    print(find_wayback_snapshot("adidas.com"))