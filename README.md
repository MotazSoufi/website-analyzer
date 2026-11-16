# Website Analyzer

A web app that takes a company's website link and creates a brand report using a main AI agent and several sub agents.

Brand report includes
- Brand name, logo, brand colors.
- Market, products, services, and company size.
- Region, countries, and languages.
- Contact details, headquarters, and branches.
- Tech stack (e.g. Shopify, NextJS, Google Analytics).
- Social links. Instagram stats, and latest Youtube videos.
- A short summary.

Sub-agents:
- Business agent
- Visual agent
- Location agent
- Contact agent
- Competitor Agent

APIs used:
- Anthropic Claude API for AI agents and web search.
- Youtube Data API v3 for channel stats and latest videos.
- Wayback Machine API for archived snapshots of blocked sites.
- Brandfetch Logo API for backup logos.
- Apify for instagram profile and latest posts.