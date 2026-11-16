import re

ALLOWED_SIZES = ["startup", "small business", "mid-size company", "large corporation", "unknown"]
HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

def check_business(result):
    problems = []
    if not result.get("brand_name"):
        problems.append('brand_name is empty. Write the name, or "unknown".')
    if str(result.get("size", "")).lower() not in ALLOWED_SIZES:
        problems.append(f"size must be one of: {', '.join(ALLOWED_SIZES)}.")
    if not isinstance(result.get("products"), list):
        problems.append("products must be a list.")
    if not isinstance(result.get("services"), list):
        problems.append("services must be a list.")
    return problems

def check_visual(result):
    problems = []
    colors = result.get("brand_colors")
    if not isinstance(colors, list) or not colors:
        problems.append("brand_colors must be a list of 2 to 5 hex codes.")
    else:
        bad = [c for c in colors if not HEX_PATTERN.match(str(c))]
        if bad:
            problems.append(f'These colors are not 6-digit hex codes like "#1ASB3C": {bad}.')
    if not result.get("theme"):
        problems.append('theme is empty. Describe the style, or write "unknown".')
    return problems

def check_location(result):
    problems = []
    if not result.get("region"):
        problems.append('region is empty. Write the region, or "unknown".')
    if not isinstance(result.get("countries"), list):
        problems.append("countries must be a list.")
    languages = result.get("languages")
    if not isinstance(languages, list):
        problems.append("languages must be a list.")
    elif any(len(str(lang)) <= 3 for lang in languages):
        problems.append('Use full language names like "English", not codes like "en".')
    return problems

def check_competitors(result):
    problems = []
    competitors = result.get("competitors")

    if not isinstance(competitors, list) or not competitors:
        problems.append("competitors must be a list with at least 3 companies.")
        return problems

    for c in competitors:
        if not isinstance(c, dict) or not c.get("name"):
            problems.append("Every competitor needs a name.")
            break
    
    for c in competitors:
        if isinstance(c, dict) and not c.get("reason"):
            problems.append("Every competitor needs a short reason.")
            break

    return problems

def check_research(result):
    problems = check_business(result) + check_location(result)

    if str(result.get("brand_name", "")).lower() == "unknown":
        problems.append("brand_name is unknown. Search for the company that owns this website domain and give its name.")
    if str(result.get("market", "")).lower() == "unknown" and not result.get("products"):
        problems.append("market and products are both missing. Search for what this company sells.")

    colors = result.get("brand_colors") or []
    bad = [c for c in colors if not HEX_PATTERN.match(str(c))]
    if bad:
        problems.append(f'These colors not 6-digit hex codes like "#1A2B3C": {bad}.')
    if not isinstance(result.get("social_links", {}), dict):
        problems.append('social_links must be an object like {"instagram": "https://..."}, or {} if none were found.')
    if not result.get("sources"):
        problems.append("You did not use any search results. Search the web for this company before answering.")

    return problems

def check_contact(result):
    problems = []
    branches = result.get("branches")

    if not isinstance(branches, list):
        problems.append("branches must be a list, or [] if there are none.")
        return problems

    for b in branches:
        if not isinstance(b, dict) or not (b.get("city") or b.get("address")):
            problems.append("Every branch needs at least a city or an address.")
            break

    return problems