import json
import base64
from utils import ask_haiku

SYSTEM_PROMPT = """You are a brand designer. You will get a screenshot of a company's homepage. 
Fill in this JSON. If you can't tell, write "unknown".

{
    "brand_colors": [],
    "theme": "",
    "logo_description": ""
}

Rules:
- brand_colors: 2 to 5 main brand colors as hex codes, e.g. "#1A2B3C". Ignore plain white/black backgrounds unless they are clearly part of the brand.
- theme: 3 to 6 words describing the style, e.g. "modern, minimal, luxury".
- logo_description: a short description of the logo you see (text, shape, colors).
Return ONLY the JSON. No extra text."""

def run_visual_agent(screenshot_path, theme_color=None, feedback=None):
    """Send the screenshot to Haiku and get visual brand info back."""

    with open(screenshot_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    if theme_color:
        hint = f"The site's theme-color meta tag is: {theme_color}"
    else:
        hint = "The site has no theme-color meta tag."

    content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
        {"type": "text", "text": hint},
    ]

    if feedback:
        content.append({"type": "text", "text": f"FEEDBACK ON YOUR LAST ANSWER: {feedback} Fix these problems and return the full JSON again."})

    return ask_haiku(SYSTEM_PROMPT, content)

if __name__ == "__main__":
    from scraper import scrape_website, get_meta_tags

    data = scrape_website("https://nike.com")
    meta = get_meta_tags(data["html"])
    result = run_visual_agent(data["screenshot"], meta.get("theme-color"))
    print(json.dumps(result, indent=2))