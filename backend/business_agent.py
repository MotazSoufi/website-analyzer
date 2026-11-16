import json
from utils import ask_haiku

SYSTEM_PROMPT = """You are a business analyst. You will get the text and meta tags from a company's homepage. 
Fill in this JSON using ONLY what the content shows. If you can't tell, write "unknown". 

{
    "brand_name": "",
    "market": "",
    "products": [],
    "services": [],
    "size": "",
    "size_reason": ""
}

Rules:
- market: the industry in a few words, e.g. "clothing", "bakery", "software"
- size: one of "startup", "small business", "mid-size company", "large corporation", "unknown"
- size_reason: one short sentence explaining your guess
Return ONLY the JSON. No extra text."""

def run_business_agent(text, meta, feedback=None):
    """Send the page content to Haiku and get business info back."""
    page_info = f"META TAGS:\n{json.dumps(meta)}\n\nPAGE TEXT:\n{text[:15000]}"
    if feedback:
        page_info += f"\n\nFEEDBACK ON YOUR LAST ANSWER: {feedback} Fix these problems and return the full JSON again."
    return ask_haiku(SYSTEM_PROMPT, page_info, max_tokens=2500)

if __name__ == "__main__":
    from scraper import scrape_website, get_meta_tags

    data = scrape_website("https://nike.com")
    meta = get_meta_tags(data["html"])
    result = run_business_agent(data["text"], meta)
    print(json.dumps(result, indent=2))
