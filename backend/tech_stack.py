TECH_SIGNATURES = [
    ("Shopify", "Platform", ["cdn.shopify.com", "shopify.theme"]),
    ("WordPress", "Platform", ["wp-content", "wp-includes"]),
    ("WooCommerce", "Platform", ["woocommerce"]),
    ("Wix", "Platform", ["wixstatic.com"]),
    ("Squarespace", "Platform", ["static1.squarespace.com"]),
    ("Webflow", "Platform", ["data-wf-site", "webflow.js"]),
    ("Magento", "Platform", ["mage/cookies", "magento"]),
    ("Salesforce Commerce Cloud", "Platform", ["demandware"]),

    ("Next.js", "Framework", ["/_next/", "__next_data__"]),
    ("Nuxt", "Framework", ["/_nuxt/", "__nuxt"]),
    ("Gatsby", "Framework", ["___gatsby"]),
    ("Angular", "Framework", ["ng-version"]),

    ("Google Analytics", "Analytics", ["google-analytics.com", "googletagmanager.com/gtag"]),
    ("Google Tag Manager", "Analytics", ["googletagmanager.com/gtm.js"]),
    ("Hotjar", "Analytics", ["static.hotjar.com"]),

    ("Meta Pixel", "Marketing", ["connect.facebook.net"]),
    ("TikTok Pixel", "Marketing", ["analytics.tiktok.com"]),
    ("Snapchat Pixel", "Marketing", ["sc-static.net"]),
    ("HubSpot", "Marketing", ["js.hs-scripts.com", "js.hsforms.net"]),
    ("Klaviyo", "Marketing", ["static.klaviyo.com"]),

    ("Intercom", "Support", ["widget.intercom.io"]),
    ("Zendesk", "Support", ["static.zdassets.com"]),

    ("Stripe", "Payments", ["js.stripe.com"]),

    ("Cloudflare", "Infrastructure", ["/cdn-cgi/"]),
    ("Google reCAPTCHA", "Security", ["google.com/recaptcha"]),
    ("jQuery", "Library", ["jquery"]),
]


def detect_tech_stack(html):
    """Return the detected tools grouped by category, e.g. {"Platform": ["Shopify"]}."""
    html_lower = html.lower()
    found = {}

    for name, category, fingerprints in TECH_SIGNATURES:
        if any(fp in html_lower for fp in fingerprints):
            found.setdefault(category, []).append(name)

    return found

if __name__ == "__main__":
    from scraper import scrape_website
    import os

    data = scrape_website("https://www.gymshark.com")
    os.remove(data["screenshot"])
    print(detect_tech_stack(data["html"]))