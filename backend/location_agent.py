import json
from utils import ask_haiku
from extractors import find_languages

SYSTEM_PROMPT = """you are a market researcher. You will get a company's homepage URL, the languages found in its code, its meta tags, and its page text. 
Fill in this JSON. If you can't tell, write "unknown". 

{
    "region": "",
    "countries": [],
    "region_reason": "",
    "languages": []
}

Rules:
- region: the main area the company serves, e.g. "UAE", "Middle East", "Europe", "Global".
- countries: up to 10 main countries. If the company operates in many countries, set region to "Global" and list only the 10 most important. 
- region_reason: one short sentence on the clues you used (domain, currency, phone number, addresses).
- languages: full language names, e.g. ["English", "Arabic"]. Include the languages found in the code, plus any others the page clearly offers.
Return ONLY the JSON. No extra text."""

def run_location_agent(url, html, text, meta, feedback=None):
    """Work out the company's region and languages."""
    code_languages = find_languages(html)

    content = (
        f"URL: {url}\n\n"
        f"LANGUAGES FOUND IN CODE: {code_languages}\n\n"
        f"META TAGS:\n{json.dumps(meta)}\n\n"
        f"PAGE TEXT:\n{text[:15000]}"
    )
    if feedback:
        content += f"\n\nFEEDBACK ON YOUR LAST ANSWER: {feedback} Fix these problems and return the full JSON again."
    return ask_haiku(SYSTEM_PROMPT, content)

if __name__ == "__main__":
    from scraper import scrape_website, get_meta_tags

    data = scrape_website("https://example.com")
    meta = get_meta_tags(data["html"])
    result = run_location_agent(data["url"], data["html"], data["text"], meta)
    print(json.dumps(result, indent=2,ensure_ascii=False))