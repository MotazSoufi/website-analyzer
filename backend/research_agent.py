import json
from urllib.parse import urlparse
from utils import ask_haiku_with_search

SYSTEM_PROMPT = """You are a business researcher. The company's website could not be opened, 
so use web search to research the company behind the given website domain. 
You MUST use the web search tool at least once before answering. Never answer from memory alone.  
Fill in this JSON using ONLY what your search results show. If you can't tell, write "unknown". 

{
    "brand_name": "",
    "market": "",
    "products": [],
    "services": [],
    "size": "",
    "size_reason": "",
    "region": "",
    "countries": [],
    "region_reason": "",
    "languages": [],
    "brand_colors": [],
    "social_links": {},
    "languages_estimated": false,
    "headquarters": "",
}

Rules:
- market: the industry in a few words, e.g. "clothing", "bakery", "software" 
- size: one of "startup", "small business", "mid-size company", "large corporation", "unknown" 
- size_reason: one short sentence explaining your guess 
- region: the main area the company serves, e.g. "UAE", "Middle East", "Europe", "Global" 
- countries: specific countries where the company clearly operates 
- region_reason: one short sentence on the clues you used 
- languages: ALWAYS a list, even for one language, e.g. ["English"] or ["English", "Arabic"] 
- If search results don't say which languages the brand's website or marketing uses, 
estimate the main ones from the countries it operates in, and set "languages_estimated" 
to true. Otherwise set it to false. 
- brand_colors: the brand's official colors as 6-digit hex codes like "#1A2B3C", ONLY 
if a search result states them (e.g. brand guidelines). Otherwise return an empty list. Never guess. 
- Make one separate search just for the colors, e.g. "H&M brand colors hex code". 
- social_links: the brands's OFFICIAL accounts found in your search results, as {"platform": "full URL"}, 
e.g. {"instagram": "https://www.instagram.com/hm/"}. Use platforms like instagram, facebook, x, linkedin, tiktok, youtube. 
Only include accounts clearly run by the brand itself, not fan pages or resellers. If none are found, return {}. 
- headquarters: the company's head office city and country, e.g. "Herzogenaurach, Germany", or "unknown". 
After searching, return ONLY the JSON. No extra text."""

def run_research_agent(url, feedback=None):
    """Research a brand on the web when its website blocks us."""

    domain = urlparse(url).netloc.removeprefix("www.") or url

    content = f"COMPANY WEBSITE: {domain}"
    if feedback:
        content += f"\n\nFEEDBACK ON YOUR LAST ANSWER: {feedback} Fix these problems and return the full JSON again."
    return ask_haiku_with_search(SYSTEM_PROMPT, content, max_searches=5)

SOCIALS_PROMPT = """You find the official social media accounts of a brand. 
Use web search, then return this JSON: 
{"social_links": {}}

Rules: 
- Format: {"platform": "full URL"}, e.g. {"instagram": "https://www.instagram.com/gucci/"} 
- Platforms: instagram, facebook, x, linkedin, tiktok, youtube 
- Only accounts clearly run by the brand itself, not fan pages or resellers. 
- Use short search queries, e.g. "Gucci official instagram". 
- If none are found, return {"social_links": {}}.
Return ONLY the JSON. No extra text."""

def find_socials_with_search(brand_name, url):
    """Quick search for a brand's official social accounts."""
    domain = urlparse(url).netloc.removeprefix("www.") or url
    content = f"BRAND: {brand_name}\nWEBSITE: {domain}"
    result = ask_haiku_with_search(SOCIALS_PROMPT, content, max_searches=2)
    return result.get("social_links", {})


if __name__ == "__main__":
    result = run_research_agent("https://www.adidas.com")
    print(json.dumps(result, indent=2, ensure_ascii=False))