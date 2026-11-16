import json
import os
import uuid
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from extractors import find_logo, find_languages

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

BLOCKED_WORDS = ["access denied", "captcha", "are you a robot", "verify you are human", "403 forbidden"]

class SiteBlockedError(Exception):
    """The site exists but we couldn't get its real content."""
    pass

os.makedirs("screenshots", exist_ok=True)

def scrape_website(url, timeout=20000, load_timeout=8000):
    """Open the website and collect its raw data."""

    screenshot_path = f"screenshots/{uuid.uuid4().hex}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1366, "height": 768},
            user_agent=USER_AGENT,
            locale="en-US",
        )

        try:
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            except PlaywrightTimeout:
                raise SiteBlockedError("The website took too long to respond.")
            except Exception as e:
                error = str(e)
                print(f"Page load error: {error.splitlines()[0]}")

                if "ERR_NAME_NOT_RESOLVED" in error or "ERR_INVALID_URL" in error:
                    raise ValueError("Could not open the website. Check that the link is correct.")
                
                raise SiteBlockedError("This website refused the connection.")
                
            if response and response.status >= 400:
                raise SiteBlockedError(f"The website blocked our scraper or returned an error (code {response.status}).")

            try:
                page.wait_for_load_state("load", timeout=load_timeout)
            except PlaywrightTimeout:
                pass
            page.wait_for_timeout(1500)

            page.screenshot(path=screenshot_path)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

            data = {
                "url": page.url,
                "title": page.title(),
                "html": page.content(),
                "text": page.inner_text("body"),
                "screenshot": screenshot_path,
                "status": response.status if response else None,
            }
            

        finally:
            browser.close()
    
    text = data["text"].strip()
    if not text:
        raise SiteBlockedError("The website has no readable text.")
    if len(text) < 1500 and any (word in text.lower() for word in BLOCKED_WORDS):
        raise SiteBlockedError("The website blocked our scraper.")

    return data

def get_meta_tags(html):
    """Find all <meta> tags and return them as a dictionary."""
    soup = BeautifulSoup(html, "html.parser")
    meta = {}

    for tag in soup.find_all("meta"):
        key = tag.get("name") or tag.get("property")
        value = tag.get("content")
        if key and value:
            meta[key] = value
    return meta

if __name__ == "__main__":
    data = scrape_website("https://nike.com")
    data["meta"] = get_meta_tags(data["html"])
    data["logo"] = find_logo(data["html"], data["url"])
    data["languages"] = find_languages(data["html"])
    data["theme_color"] = data["meta"].get("theme-color")

    print("Logo:", data["logo"])
    print("Languages:", data["languages"])
    print("Theme color:", data["theme_color"])

    print("Title:", data["title"])
    print("Meta tags:", data["meta"])
    print("Text preview:", data["text"][:300])

    to_save = {k: v for k, v in data.items() if k != "html"}
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)
