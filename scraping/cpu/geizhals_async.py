import pandas as pd
import re
import json
import time
import asyncio
import random
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
import os
from difflib import SequenceMatcher

INPUT_CSV = "CPU.csv"
OUTPUT_CSV = "CPU_geizhals.csv"
START_ROW = 0
MAX_ROWS = None

def fuzzy_match(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def save_partial_result(output_csv, row_result):
    if not os.path.exists(output_csv):
        pd.DataFrame([row_result]).to_csv(output_csv, index=False)
    else:
        df_existing = pd.read_csv(output_csv)
        df_updated = pd.concat([df_existing, pd.DataFrame([row_result])], ignore_index=True)
        df_updated.to_csv(output_csv, index=False)

async def accept_cookies_if_present(page):
    try:
        return await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=10000)
    except:
        return None

async def get_offers_from_product_page(context, row, search_term, product_url, output_csv, stop_event):
    row_result = row.copy()
    offers = []
    page = await context.new_page()
    try:
        print(f"- VISIT - {search_term} -> {product_url}")
        await page.goto(product_url, timeout=15000, wait_until="domcontentloaded")

        h1 = await page.text_content("h1")
        if h1 and "banned" in h1.lower():
            print(f"- BANNED - {search_term} blocked on product page")
            stop_event.set()
            raise Exception("banned page detected")

        if await accept_cookies_if_present(page):
            await page.click("#onetrust-accept-btn-handler")
            await page.wait_for_timeout(500)

        try:
            await page.wait_for_selector("a.gh_offerlist__offerurl", timeout=5000)
        except:
            print(f"- SKIP - {search_term} no offers found")
            row_result["offers"] = json.dumps([])
            row_result["image"] = ""
            save_partial_result(output_csv, row_result)
            return row_result

        offer_tags = await page.query_selector_all("a.gh_offerlist__offerurl")
        offer_tags = offer_tags[:10]

        for tag in offer_tags:
            try:
                onclick = await tag.get_attribute("onclick") or ""
                href = await tag.get_attribute("href") or "N/A"
                merchant = await tag.get_attribute("data-merchant-name") or "Unknown"

                price_match = re.search(r"price\s*[:=]\s*['\"]?([\d.,]+)['\"]?", onclick)
                price = price_match.group(1).replace(",", ".") if price_match else "N/A"

                logo_src = await tag.evaluate("node => node.closest('div.flex')?.querySelector('div.merchant__logo-image img')?.src || ''")

                if "logos/7413.png" in logo_src:
                    merchant = "Amazon"
                elif "logos/198223.gif" in logo_src:
                    merchant = "eBay"

                print(f"  -> {merchant} - {price} - {href}")

                if href == "N/A" or price == "N/A":
                    continue

                offers.append({
                    "retailer": merchant,
                    "price": price,
                    "url": href,
                    "source": "geizhals"
                })

            except:
                continue

        try:
            image_slide = await page.query_selector(".swiper-wrapper .swiper-slide")
            if image_slide:
                image_url = await image_slide.get_attribute("data-pswp-src")
                print(f"- IMAGE - {search_term} -> {image_url}")
            else:
                print(f"- NO IMAGE - {search_term}")
                image_url = ""
            row_result["image"] = image_url
        except:
            row_result["image"] = ""

        row_result["offers"] = json.dumps(offers)
        save_partial_result(output_csv, row_result)
        return row_result

    finally:
        await page.close()

async def scrape_cpu_prices_geizhals():
    start_time = time.time()
    df = pd.read_csv(INPUT_CSV)

    if MAX_ROWS is not None:
        df = df.iloc[START_ROW:START_ROW + MAX_ROWS].copy().reset_index(drop=True)
    else:
        df = df.copy().reset_index(drop=True)

    df["offers"] = ""
    df["image"] = ""

    stop_event = asyncio.Event()

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Safari/537.36"
    ]

    viewports = [
        {"width": 1920, "height": 1080}, {"width": 1366, "height": 768},
        {"width": 1536, "height": 864}, {"width": 1280, "height": 720},
        {"width": 1600, "height": 900}, {"width": 1440, "height": 900},
        {"width": 1680, "height": 1050}, {"width": 1024, "height": 768},
        {"width": 1920, "height": 1200}, {"width": 1360, "height": 768}
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        sem = asyncio.Semaphore(3)

        async def process_row(row):
            async with sem:
                if stop_event.is_set():
                    return

                row = row.to_dict()
                brand = row["brand"]
                series = row["series"]
                model = row["model"]
                search_term = f"{brand} {series} {model}"
                encoded_search = quote(search_term)

                base_url = "https://geizhals.de/"
                search_url = f"{base_url}?fs={encoded_search}&hloc=at&hloc=de&hloc=eu&hloc=pl&hloc=uk"
                if brand.lower() == "amd":
                    search_url += "&cat=cpuamdam4"
                elif brand.lower() == "intel":
                    search_url += "&cat=cpu1151"

                context = await browser.new_context(
                    user_agent=random.choice(user_agents),
                    viewport=random.choice(viewports)
                )

                await context.route("**/*", lambda route, request: asyncio.create_task(route.abort()) if request.resource_type in ["stylesheet", "font"] else asyncio.create_task(route.continue_()))
                page = await context.new_page()

                try:
                    print(f"- SEARCH - {search_term} -> {search_url}")
                    response = await page.goto(search_url, timeout=15000, wait_until="domcontentloaded")

                    if response.status == 429:
                        print(f"- BANNED - {search_term} (429)")
                        stop_event.set()
                        await context.close()
                        return

                    h1 = await page.text_content("h1")
                    if h1 and "banned" in h1.lower():
                        print(f"- BANNED - {search_term} page blocked")
                        stop_event.set()
                        await context.close()
                        return

                    if await accept_cookies_if_present(page):
                        await page.click("#onetrust-accept-btn-handler")
                        await page.wait_for_timeout(random.randint(300, 1000))

                    items = await page.query_selector_all("article.listview__item")
                    product_url = None
                    best_ratio = 0
                    best_item = None
                    best_price_link = None

                    for item in items[:5]:
                        name_tag = await item.query_selector("h3.listview__name a")
                        title = (await name_tag.inner_text()).strip() if name_tag else ""
                        title_prefix = title.split(",")[0].strip()
                        ratio = fuzzy_match(search_term, title_prefix)
                        print(f"- MATCH - {search_term} vs {title_prefix}: {round(ratio, 3)}")
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_item = item
                            best_price_link = await item.query_selector("a.listview__price-link")

                    if best_item and best_price_link:
                        href = await best_price_link.get_attribute("href")
                        product_url = urljoin(base_url, href)

                    await page.close()
                    await context.close()

                    if not product_url:
                        print(f"- NO MATCH - {search_term}")
                        row_result = row.copy()
                        row_result["offers"] = json.dumps([])
                        row_result["image"] = ""
                        save_partial_result(OUTPUT_CSV, row_result)
                        return row_result

                    context2 = await browser.new_context(
                        user_agent=random.choice(user_agents),
                        viewport=random.choice(viewports)
                    )
                    await context2.route("**/*", lambda route, request: asyncio.create_task(route.abort()) if request.resource_type in ["stylesheet", "font"] else asyncio.create_task(route.continue_()))
                    return await get_offers_from_product_page(context2, row, search_term, product_url, OUTPUT_CSV, stop_event)

                except Exception:
                    await context.close()
                    row_result = row.copy()
                    row_result["offers"] = json.dumps([])
                    row_result["image"] = ""
                    save_partial_result(OUTPUT_CSV, row_result)
                    return row_result

        tasks = [process_row(row) for _, row in df.iterrows()]
        await asyncio.gather(*tasks)
        await browser.close()

    print(f"\ncpu scraping complete - saved to {OUTPUT_CSV} in {round(time.time() - start_time, 2)}s")

if __name__ == "__main__":
    asyncio.run(scrape_cpu_prices_geizhals())
