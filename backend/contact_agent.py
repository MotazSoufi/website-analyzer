import json
from utils import ask_haiku

SYSTEM_PROMPT = """You extract a company's branches and locations from the text of its contact or store locator page. 
Return this JSON:

{
    "headquarters": "",
    "branches": [
        {"name": "", "city": "", "country": "", "address": "", "phone": ""}
    ]
}

Rules: 
- headquarters: the main office address if the page states it, otherwise "unknown" 
- branches: physical locations listed on the page (stores, offices, clinics, restaurants). 
- Use "" for any branch detail the page doesn't give. 
- If the page lists no branches, return an empty list. 
- Only use what the page says. Never invent locations. 
Return ONLY the JSON. No extra text."""

def run_contact_agent(page_text, feedback=None):
    """Read a contact/locations page and pull out the branches."""
    content = f"PAGE TEXT:\n{page_text[:15000]}"
    if feedback:
        content += f"\n\nFEEDBACK ON YOUR LAST ANSWER: {feedback} Fix these problems and return the full JSON again."
    return ask_haiku(SYSTEM_PROMPT, content, max_tokens=4000)