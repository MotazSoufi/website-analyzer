import json
from scraper import scrape_website, get_meta_tags, SiteBlockedError
from extractors import find_logo, find_social_links, clean_social_links, find_emails_and_phones, find_contact_page
from business_agent import run_business_agent
from visual_agent import run_visual_agent
from location_agent import run_location_agent
from competitor_agent import run_competitor_agent
from research_agent import run_research_agent, find_socials_with_search
from contact_agent import run_contact_agent
from utils import ask_haiku
import time
from concurrent.futures import ThreadPoolExecutor
import os
from validators import check_business, check_visual, check_location, check_competitors, check_research, check_contact
from youtube import get_youtube_data
from wayback import find_wayback_snapshot
from urllib.parse import urlparse
from instagram import get_instagram_data
from tech_stack import detect_tech_stack

SUMMARY_PROMPT = """You are a brand analyst. You will get a JSON report about a company's website. 
Write a short summary and return it in this JSON: 
{"summary": ""}

Rules: 
- 2 to 3 sentences, plain and factual
- Only use facts from the report. Skip anything marked "unknown".
Return ONLY the JSON. No extra text."""

def safe_run(func, *args):
    """Run an agent. If it crashes, return a 'failed' marker instead of crashing everything."""
    try:
        return func(*args)
    except Exception as e:
        print(f"{func.__name__} failed: {e}")
        return {"failed": True}

MAX_ATTEMPTS = 2

def run_with_checks(name, agent_func, checker, *args):
    """Run a sub-agent, check its answer, and send it back with feedback if needed."""
    feedback = None
    result = {"failed": True}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = agent_func(*args, feedback=feedback)
        except Exception as e:
            print(f"[{name}] attempt {attempt} crashed: {e}")
            feedback = f"Your last answer caused an error: {e}. Return ONLY valid, complete JSON in the exact format."
            result = {"failed": True}
            continue

        problems = checker(result)
        if not problems:
            print(f"[{name}] passed on attempt {attempt}")
            return result

        print(f"[{name}] attempt {attempt} problems: {problems}")
        feedback = " ".join(problems)

    return result

def find_contact_details(data):
    """Find the branches/contact page, scrape it, and extract branches, emails and phones."""
    contact_url = find_contact_page(data["html"], data["url"])
    if not contact_url:
        print("No branches or contact page found.")
        return {"contact_page": None, "branches": [], "headquarters": "unknown", "emails": [], "phones": []}

    print(f"Scraping contact page: {contact_url}")
    page = scrape_website(contact_url, timeout=15000, load_timeout=4000)
    os.remove(page["screenshot"])

    result = run_with_checks("contact", run_contact_agent, check_contact, page["text"])
    emails, phones = find_emails_and_phones(page["html"], page["text"], data["url"])

    return {
        "contact_page": contact_url,
        "branches": result.get("branches", []),
        "headquarters": result.get("headquarters", "unknown"),
        "emails": emails,
        "phones": phones,
    }

def analyze_from_website(data):
    """NORMAL MODE: analyze the scraped website."""
    meta = get_meta_tags(data["html"])
    logo_url = find_logo(data["html"], data["url"])
    social_links = find_social_links(data["html"], data["url"])
    tech_stack = detect_tech_stack(data["html"])
    home_emails, home_phones = find_emails_and_phones(data["html"], data["text"], data["url"])
    print(f"Tech stack: {tech_stack}")

    print(f"Socials found on page: {social_links}")

    print("2/4 Running all sub-agents at the same time...")
    with ThreadPoolExecutor() as executor:
        business_job = executor.submit(run_with_checks, "business", run_business_agent, check_business, data["text"], meta)
        visual_job = executor.submit(run_with_checks, "visual", run_visual_agent, check_visual, data["screenshot"], meta.get("theme-color"))
        location_job = executor.submit(run_with_checks, "location", run_location_agent, check_location, data["url"], data["html"], data["text"], meta)
        contact_job = executor.submit(safe_run, find_contact_details, data)

        youtube_job = None
        if "youtube" in social_links:
            youtube_job = executor.submit(safe_run, get_youtube_data, social_links["youtube"])

        business = business_job.result()
        visual = visual_job.result()
        location = location_job.result()
        youtube = youtube_job.result() if youtube_job else None
        contact = contact_job.result()
    
    os.remove(data["screenshot"])

    failed_agents = []
    if business.get("failed"):
        failed_agents.append("business")
    if visual.get("failed"):
        failed_agents.append("visual")
    if location.get("failed"):
        failed_agents.append("location")
    if youtube and youtube.get("failed"):
        failed_agents.append("youtube")
    if contact.get("failed"):
        failed_agents.append("contact")

    return {
        "mode": "website",
        "url": data["url"],
        "brand_name": business.get("brand_name"),
        "logo_url": logo_url,
        "logo_description": visual.get("logo_description"),
        "brand_colors": visual.get("brand_colors"),
        "theme": visual.get("theme"),
        "market": business.get("market"),
        "products": business.get("products"),
        "services": business.get("services"),
        "size": business.get("size"),
        "size_reason": business.get("size_reason"),
        "region": location.get("region"),
        "countries": location.get("countries"),
        "region_reason": location.get("region_reason"),
        "languages": location.get("languages"),
        "social_links": social_links,
        "tech_stack": tech_stack,
        "contact_page": contact.get("contact_page"),
        "headquarters": contact.get("headquarters", "unknown"),
        "branches": contact.get("branches", []),
        "emails": list(dict.fromkeys(home_emails + contact.get("emails", [])))[:5],
        "phones": list(dict.fromkeys(home_phones + contact.get("phones", [])))[:5],
        "youtube": youtube,
        "research_sources": [],
        "failed_agents": failed_agents,
    }

def analyze_from_archive(url, reason):
    """ARCHIVE MODE: the live site blocked us, so analyze a Wayback Machine snapshot."""
    print(f"Scraping failed ({reason}). Trying the Wayback Machine...")

    snapshot = safe_run(find_wayback_snapshot, url)
    if not snapshot or snapshot.get("failed"):
        print("No usable snapshot found.")
        return None

    print(f"Found snapshot from {snapshot['date']}. Scraping it...")
    try:
        data = scrape_website(snapshot["url"], timeout=12000, load_timeout=3000)
    except (SiteBlockedError, ValueError) as e:
        print(f"Snapshot couldn't be used: {e}")
        return None

    report = analyze_from_website(data)
    report["mode"] = "archive"
    report["url"] = url
    report["archive_url"] = snapshot["url"]
    report["archive_date"] = snapshot["date"]
    
    return report

def brandfetch_logo_url(url):
    """Build a Brandfetch logo link for React to display. We never download it ourselves."""
    client_id = os.getenv("BRANDFETCH_CLIENT_ID")
    if not client_id:
        return None
    domain = urlparse(url).netloc.removeprefix("www.") or url
    return f"https://cdn.brandfetch.io/{domain}/fallback/lettermark/icon?c={client_id}"

def analyze_from_research(url, reason):
    """FALLBACK MODE: the site blocked us, so research the brand on the web instead."""
    print(f"Switching to web research mode...")
    print("2/4 Researching the brand on the web...")
    research = run_with_checks("research", run_research_agent, check_research, url)

    social_links = clean_social_links(research.get("social_links"))
    print(f"Socials from research: {research.get('social_links')} → after cleaning: {social_links}")
    youtube = None
    if "youtube" in social_links:
        youtube = safe_run(get_youtube_data, social_links["youtube"])

    return {
        "mode": "fallback",
        "fallback_reason": reason,
        "url": url,
        "brand_name": research.get("brand_name"),
        "logo_url": brandfetch_logo_url(url),
        "logo_description": "Logo provided by Brandfetch",
        "brand_colors": research.get("brand_colors", []),
        "theme": None,
        "market": research.get("market"),
        "products": research.get("products"),
        "services": research.get("services"),
        "size": research.get("size"),
        "size_reason": research.get("size_reason"),
        "region": research.get("region"),
        "countries": research.get("countries"),
        "region_reason": research.get("region_reason"),
        "languages": research.get("languages"),
        "languages_estimated": research.get("languages_estimated", False),
        "social_links": social_links,
        "tech_stack": {},
        "contact_page": None,
        "headquarters": research.get("headquarters", "unknown"),
        "branches": [],
        "emails": [],
        "phones": [],
        "youtube": youtube,
        "research_sources": research.get("sources", []),
        "failed_agents": ["research"] if research.get("failed") else [],
    }

GAP_FIELDS = ["brand_name", "market", "products", "services", "size", "size_reason",
              "region", "countries", "region_reason", "languages"]

def is_missing(value):
    """True if a value is empty or 'unknown'."""
    if isinstance(value, str):
        return value.strip().lower() in ("", "unknown")
    return not value

def needs_research(report):
    """Decide if the report is missing important business info."""
    return (
        is_missing(report.get("market"))
        or (is_missing(report.get("products")) and is_missing(report.get("services")))
        or is_missing(report.get("region"))
    )

def fill_gaps(report, research):
    """Copy research answers ONLY into fields the report is missing."""
    filled = []
    for field in GAP_FIELDS:
        if is_missing(report.get(field)) and not is_missing(research.get(field)):
            report[field] = research[field]
            filled.append(field)
    if "languages" in filled:
        report["languages_estimated"] = research.get("languages_estimated", False)

    report["research_sources"] = research.get("sources", [])
    report["filled_by_research"] = filled
    print(f"Filled from research: {filled}")

def analyze_website(url, on_progress=None):
    """Pick the right mode, then add competitors and a summary."""
    start = time.time()

    def step(message):
        """Print a progress message, and send it to the frontend if someone is listening."""
        print(message)
        if on_progress:
            on_progress(message)

    step("Opening the website...")
    try:
        data = scrape_website(url)
    except SiteBlockedError as e:
        step("The website blocked us. Trying an archived copy...")
        report = analyze_from_archive(url, str(e))
        if report is None:
            step("No usable archive. Researching the brand on the web...")
            report = analyze_from_research(url, str(e))
    else:
        step("Website loaded. Running the AI agents...")
        report = analyze_from_website(data)

    if report["mode"] != "fallback" and needs_research(report):
        step("Some info is missing. Filling gaps with web research...")
        research = run_with_checks("research", run_research_agent, check_research, url)
        if not research.get("failed"):
            fill_gaps(report, research)

    if report["mode"] != "fallback" and not report.get("social_links") and not is_missing(report.get("brand_name")):
        step("Searching for social media accounts...")
        found = safe_run(find_socials_with_search, report["brand_name"], url)
        report["social_links"] = clean_social_links(found)
        print(f"Socials from search: {report['social_links']}")

        if "youtube" in report["social_links"] and not report.get("youtube"):
            report["youtube"] = safe_run(get_youtube_data, report["social_links"]["youtube"])

    report["logo_fallback_url"] = brandfetch_logo_url(url)

    step("Finding competitors and Instagram data...")
    brand_name = report.get("brand_name")
    instagram_link = report.get("social_links", {}).get("instagram")

    with ThreadPoolExecutor() as executor:
        competitors_job = None
        if brand_name and brand_name != "unknown":
            competitors_job = executor.submit(
                run_with_checks, "competitors", run_competitor_agent, check_competitors,
                brand_name, report.get("market"), report.get("products"), report.get("region"),
            )

        instagram_job = None
        if instagram_link:
            instagram_job = executor.submit(safe_run, get_instagram_data, instagram_link)

        competitors = competitors_job.result() if competitors_job else None
        instagram = instagram_job.result() if instagram_job else None

    if competitors and competitors.get("failed"):
        report["failed_agents"].append("competitors")
    if instagram and instagram.get("failed"):
        report["failed_agents"].append("instagram")

    report["competitors"] = competitors.get("competitors", []) if competitors else []
    report["competitor_sources"] = competitors.get("sources", []) if competitors else []
    report["instagram"] = instagram

    step("Writing the summary...")
    summary = safe_run(ask_haiku, SUMMARY_PROMPT, json.dumps(report, ensure_ascii=False))
    report["summary"] = summary.get("summary")

    print(f"Done in {time.time() - start:.1f} seconds ({report['mode']} mode)")
    return report

if __name__ == "__main__":
    report = analyze_website("https://example.com")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)