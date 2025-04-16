import pandas as pd
import re
import json
import time
import asyncio
import random
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import os

def extract_product_code(name):
    matches = re.findall(r"\((.*?)\)", name)
    return matches[-1] if matches else ""

async def accept_cookies_if_present(page):
    try:
        return await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=10000)
    except:
        return None

def save_partial_result(output_csv, row_result):
    if not os.path.exists(output_csv):
        pd.DataFrame([row_result]).to_csv(output_csv, index=False)
    else:
        df_existing = pd.read_csv(output_csv)
        df_updated = pd.concat([df_existing, pd.DataFrame([row_result])], ignore_index=True)
        df_updated.to_csv(output_csv, index=False)

async def get_offers_from_product_page(context, row, code, product_url, output_csv, stop_event):
    offers = []
    page = await context.new_page()
    try:
        print(f"- VISIT - {code} -> {product_url}")
        await page.goto(product_url, timeout=15000, wait_until="domcontentloaded")

        h1 = await page.text_content("h1")
        if h1 and "banned" in h1.lower():
            print(f"- BANNED - {code} blocked on product page")
            stop_event.set()
            raise Exception("banned page")

        if await accept_cookies_if_present(page):
            await page.click("#onetrust-accept-btn-handler")
            await page.wait_for_timeout(500)

        try:
            await page.wait_for_selector("a.gh_offerlist__offerurl", timeout=5000)
        except:
            print(f"- SKIP - {code} no offers found")
            row_result = row.copy()
            row_result["offers"] = json.dumps([])
            save_partial_result(output_csv, row_result)
            return row_result

        offer_tags = await page.query_selector_all("a.gh_offerlist__offerurl")
        offer_tags = offer_tags[:10]

        for tag in offer_tags:
            try:
                onclick = await tag.get_attribute("onclick") or ""
                href = await tag.get_attribute("href") or "N/A"
                merchant = await tag.get_attribute("data-merchant-name") or "Unknown"

                price_match = re.search(r"price\s*[:=]\s*['\"]?([\d\.,]+)['\"]?", onclick)
                price = price_match.group(1).replace(",", ".") if price_match else "N/A"

                logo_src = await tag.evaluate("node => node.closest('div.flex')?.querySelector('div.merchant__logo-image img')?.src || ''")

                if "logos/7413.png" in logo_src:
                    merchant = "Amazon"
                elif "logos/198223.gif" in logo_src:
                    merchant = "eBay"

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

    finally:
        await page.close()

    print(f"- DONE - {code} offers: {len(offers)}")
    row_result = row.copy()
    row_result["offers"] = json.dumps(offers)
    save_partial_result(output_csv, row_result)
    return row_result

async def scrape_gpu_prices_from_geizhals(input_csv, output_csv, max_concurrent_tasks=8):
    start_time = time.time()
    df = pd.read_csv(input_csv).iloc[1520:].reset_index(drop=True)
    df["product_code"] = df["name"].apply(extract_product_code)

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Chrome/114.0.5735.199 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 Chrome/117.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/116.0.5845.96 Safari/537.36"
    ]

    viewports = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1280, "height": 720},
        {"width": 1600, "height": 900},
        {"width": 1440, "height": 900},
        {"width": 1680, "height": 1050},
        {"width": 1024, "height": 768},
        {"width": 1920, "height": 1200},
        {"width": 1360, "height": 768}
    ]

    stop_event = asyncio.Event()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        sem = asyncio.Semaphore(max_concurrent_tasks)

        async def process_row(i, row, total):
            async with sem:
                if stop_event.is_set():
                    return

                row = row.to_dict()
                name = row["name"]
                code = row["product_code"]
                search_url = f"https://geizhals.de/?fs={'+'.join(code.split())}"

                print(f"[{i+1}/{total}] searching for {code}")

                context = await browser.new_context(
                    user_agent=random.choice(user_agents),
                    viewport=random.choice(viewports)
                )
                await context.route("**/*", lambda route, request: asyncio.create_task(route.abort()) if request.resource_type in ["stylesheet", "font"] else asyncio.create_task(route.continue_()))
                page = await context.new_page()

                try:
                    response = await page.goto(search_url, timeout=15000, wait_until="domcontentloaded")
                    h1 = await page.text_content("h1") or ""

                    if response.status == 429 or "banned" in h1.lower():
                        print(f"[{i+1}/{total}] - BANNED - {code}")
                        stop_event.set()
                        await context.close()
                        return

                    if await accept_cookies_if_present(page):
                        await page.click("#onetrust-accept-btn-handler")
                        await page.wait_for_timeout(random.randint(300, 1200))

                    items = await page.query_selector_all("article.listview__item")
                    product_url = None

                    for item in items:
                        mpn_tag = await item.query_selector("span.listview__mpn")
                        if mpn_tag:
                            mpn = (await mpn_tag.inner_text()).strip()
                            if mpn.lower() == code.lower():
                                link = await item.query_selector("a.listview__price-link")
                                if link:
                                    href = await link.get_attribute("href")
                                    product_url = urljoin("https://geizhals.de", href)
                                    break

                    await page.close()
                    await context.close()

                    if not product_url:
                        print(f"[{i+1}/{total}] no match for {code}")
                        row_result = row.copy()
                        row_result["offers"] = json.dumps([])
                        save_partial_result(output_csv, row_result)
                        return row_result

                    print(f"[{i+1}/{total}] match found: {code}")
                    await asyncio.sleep(random.uniform(2.0, 4.0))

                    context2 = await browser.new_context(
                        user_agent=random.choice(user_agents),
                        viewport=random.choice(viewports)
                    )
                    await context2.route("**/*", lambda route, request: asyncio.create_task(route.abort()) if request.resource_type in ["stylesheet", "font"] else asyncio.create_task(route.continue_()))
                    return await get_offers_from_product_page(context2, row, code, product_url, output_csv, stop_event)

                except Exception as e:
                    print(f"[{i+1}/{total}] error for {code}: {e}")
                    await context.close()
                    row_result = row.copy()
                    row_result["offers"] = json.dumps([])
                    save_partial_result(output_csv, row_result)
                    return row_result

        tasks = [process_row(i, row, len(df)) for i, row in df.iterrows()]
        await asyncio.gather(*tasks)
        await browser.close()

    elapsed = round(time.time() - start_time, 2)
    print(f"\nscraping complete - saved to {output_csv} in {elapsed}s")

if __name__ == "__main__":
    asyncio.run(scrape_gpu_prices_from_geizhals("GPU.csv", "gpu_geizhals.csv"))