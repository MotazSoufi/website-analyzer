from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

def find_logo(html, base_url):
    """Try to find the logo's image link."""
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        clues = " ".join([
            img.get("src", ""),
            img.get("alt", ""),
            img.get("id", ""),
            " ".join(img.get("class", [])),
        ]).lower()
        
        # this is for checking if the href starts with data:
        src = img.get("src", "")
        if "logo" in clues and src and not src.startswith("data:"):
            return urljoin(base_url, src)

    icons = soup.find_all("link", rel=True)
    for preferred in ["apple-touch-icon", "icon"]:
        for link in icons:
            rel = " ".join(link["rel"]).lower()
            href = link.get("href", "")
            if preferred in rel and href and not href.startswith("data:"):
                return urljoin(base_url, href)

    return urljoin(base_url, "/favicon.ico")


def find_languages(html):
    """Find which languages the website supports."""
    soup = BeautifulSoup(html, "html.parser")
    languages = set()

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        languages.add(html_tag["lang"])

    for link in soup.find_all("link", hreflang=True):
        if link["hreflang"] != "x-default":
            languages.add(link["hreflang"])

    return sorted(languages)


SOCIAL_PLATFORMS = {
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "x.com": "x",
    "twitter.com": "x",
    "linkedin.com": "linkedin",
    "tiktok.com": "tiktok",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "snapchat.com": "snapchat",
    "pinterest.com": "pinterest",
    "threads.net": "threads",
    "threads.com": "threads",
    "wa.me": "whatsapp",
}

SHARE_WORDS = ["share", "sharer", "intent", "dialog"]

def unwrap_archive_link(link):
    """'https://web.archive.org/web/2026.../https://instagram/com/x' → 'https://instagram.com/x'"""

    if "web.archive.org/web/" in link:
        after = link.split("web.archive.org/web/", 1)[1]
        parts = after.split("/", 1)
        if len(parts) == 2:
            return parts[1]
    return link

def find_social_links(html, base_url):
    """Find the brand's social media accounts linked on the page."""
    soup = BeautifulSoup(html, "html.parser")
    socials = {}

    for a in soup.find_all("a", href=True):
        link = unwrap_archive_link(urljoin(base_url, a["href"]))

        if any(word in link.lower() for word in SHARE_WORDS):
            continue
        
        host = urlparse(link).netloc.lower().removeprefix("www.")

        for domain, platform in SOCIAL_PLATFORMS.items():
            if host == domain or host.endswith("." + domain):
                if platform not in socials:
                    socials[platform] = link

    return socials

def platform_for_link(link):
    """'https://www.instagram.com/hm/' to 'instagram'. Returns None if it's not a social site."""
    host = urlparse(link).netloc.lower().removeprefix("www.")
    for domain, platform in SOCIAL_PLATFORMS.items():
        if host == domain or host.endswith("." + domain):
            return platform
    return None

def clean_social_links(links):
    """Keep only real social media links from the AI's answer, one per platform."""
    cleaned = {}
    if not isinstance(links, dict):
        return cleaned

    for link in links.values():
        if not isinstance(link, str) or not link.startswith("http"):
            continue
        if any(word in link.lower() for word in SHARE_WORDS):
            continue
        platform = platform_for_link(link)
        if platform and platform not in cleaned:
            cleaned[platform] = link
        
    return cleaned

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\+\d[\d\s\-()]{7,}\d")
IMAGE_ENDINGS = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")

SKIP_EMAIL_WORDS = ["noreply", "no-reply", "donotreply", "privacy", "dpo@", "legal@", "abuse@", "example.com"]

def find_emails_and_phones(html, text, base_url=""):
    """Find email addresses and phone numbers on a page."""
    soup = BeautifulSoup(html, "html.parser")
    emails = set()
    phones = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            emails.add(href[7:].split("?")[0])
        elif href.lower().startswith("tel:"):
            phones.add(href[4:].strip())

    for email in EMAIL_PATTERN.findall(text):
        if not email.lower().endswith(IMAGE_ENDINGS):
            emails.add(email)
    for phone in PHONE_PATTERN.findall(text):
        phones.add(phone.strip())

    emails = [e for e in emails if not any(word in e.lower() for word in SKIP_EMAIL_WORDS)]
    phones = [p for p in phones if len(re.sub(r"\D", "", p)) >= 7]
    brand = urlparse(base_url).netloc.removeprefix("www.").split(".")[0] if base_url else ""
    emails = sorted(emails, key=lambda e: (brand not in e.split("@")[-1].lower(), e))

    return emails[:5], sorted(phones)[:5]

BRANCH_WORDS = ["store-locator", "stores", "locations", "branches", "find-us", "find a store", "our stores"]
CONTACT_WORDS = ["contact"]

def find_contact_page(html, base_url):
    """Find a link to the brand's branches page, or else its contact page."""
    soup = BeautifulSoup(html, "html.parser")
    base_host = urlparse(base_url).netloc
    contact_link = None

    for a in soup.find_all("a", href=True):
        link = urljoin(base_url, a["href"])
        if urlparse(link).netloc != base_host:
            continue

        clues = (a.get_text(" ", strip=True) + " " + a["href"]).lower()
        if any(word in clues for word in BRANCH_WORDS):
            return link
        if contact_link is None and any(word in clues for word in CONTACT_WORDS):
            contact_link = link
    
    return contact_link