import json
from playwright.sync_api import sync_playwright

scraped_data = []  # list to hold all scraped info

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Go to homepage
    page.goto("https://www.eand.com.eg/StaticFiles/portal2/etisalat/index_en.html", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Get all links from homepage
    links = page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
    visited = set()

    for link in links:
        if link.startswith("https://www.eand.com.eg") and link not in visited:
            try:
                print(f"Scraping: {link}")
                page.goto(link, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                text = page.inner_text("body")

                # Save to our scraped_data list
                scraped_data.append({
                    "url": link,
                    "content": text.strip()
                })

                visited.add(link)

            except Exception as e:
                print(f"❌ Failed to load {link}: {e}")

    browser.close()

# Write results to JSON
with open("etisalat_scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(scraped_data, f, ensure_ascii=False, indent=2)

print("Done! Scraped content saved to 'etisalat_scraped_data.json'")
