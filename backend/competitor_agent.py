import json
from utils import ask_haiku_with_search

SYSTEM_PROMPT = """You are a market researcher. You will get information about a brand. 
Use web search to find its 1 to 3 main competitors: global brands that sell similar products to a similar audience. 

Return this JSON:
{
    "competitors": [
        {"name": "", "website": "", "reason": ""}
    ]
}

Rules:
- Only include real companies you found in your search results.
- website: the competitor's official homepage, or "unknown"
- reason: one short sentence on why it competes with the brand
- Do not include the brand itself.
- Use short, simple search queries of 2 to 6 words, e.g. "H&M competitors fast fashion". 
After searching, return ONLY the JSON. No extra text."""

def run_competitor_agent(brand_name, market, products, region, feedback=None):
    """Search the web for the brand's main competitors."""
    content = (
        f"BRAND: {brand_name}\n"
        f"MARKET: {market}\n"
        f"PRODUCTS: {products}\n"
        f"REGION: {region}"
    )
    if feedback:
        content += f"\n\nFEEDBACK ON YOUR LAST ANSWER: {feedback} Fix these problems and return the full JSON again."

    return ask_haiku_with_search(SYSTEM_PROMPT, content)

if __name__ == "__main__":
    result = run_competitor_agent(
        brand_name="Nike",
        market="sportswear",
        products=["running shoes", "sports clothing"],
        region="Global",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))