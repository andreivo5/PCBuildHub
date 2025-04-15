import asyncio
import aiohttp
import pandas as pd
import json
import os
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

INPUT_CSV = "Memory.csv"
OUTPUT_CSV = "ram_prices_output.csv"
CONCURRENCY = 8

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Chrome/114.0.5735.199 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 Chrome/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/121.0.0.0"
]

LAPTOP_KEYWORDS = ["SODIMM", "Notebook", "SO-DIMM"]

def extract_ram_search_term(name):
    parts = name.split()
    brand_series = " ".join(parts[:2]) if len(parts) >= 2 else parts[0]
    match = re.search(r"(DDR\d-\d+)", name.upper())
    ddr_speed = match.group(1) if match else ""
    return f"{brand_series} {ddr_speed}".strip()

def construct_ram_search_url(search_term, capacity_gb, ddr_type=None):
    base_url = "https://www.gputracker.eu/en/search/category/11/memory-ram"
    query = f"textualSearch={quote(search_term)}&onlyInStock=true"
    query += f"&fr_memory-ram.capacity_min={capacity_gb}&fr_memory-ram.capacity_max={capacity_gb}"
    if ddr_type:
        query += f"&fv_memory-ram.type={ddr_type}"
    return f"{base_url}?{query}"

def save_partial_result(row):
    if not os.path.exists(OUTPUT_CSV):
        pd.DataFrame([row]).to_csv(OUTPUT_CSV, index=False)
    else:
        existing = pd.read_csv(OUTPUT_CSV)
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        updated.to_csv(OUTPUT_CSV, index=False)

async def fetch_and_parse(session, url, headers, i, total, name):
    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status == 200:
                html = await response.text()
                return BeautifulSoup(html, "html.parser")
            else:
                print(f"[{i+1}/{total}] http {response.status} for {name}")
    except Exception as e:
        print(f"[{i+1}/{total}] error for {name}: {e}")
    return None

def extract_offers(soup, search_term):
    offer_blocks = soup.find_all("div", class_="stock-item-block")
    offers = []

    for offer_block in offer_blocks[:10]:
        try:
            title_text = offer_block.get_text().lower()
            if any(keyword.lower() in title_text for keyword in LAPTOP_KEYWORDS):
                continue

            link_tag = offer_block.find("a", class_="tracked-product-click", href=True)
            link = link_tag["href"].strip() if link_tag else "N/A"
            if not link.startswith("http"):
                link = "https://www.gputracker.eu" + link

            retailer_tag = offer_block.find("span", class_="text-muted h6 d-block lead mb-2")
            retailer = retailer_tag.get_text(strip=True) if retailer_tag else "N/A"

            price_tag = offer_block.find("div", class_="font-weight-bold text-secondary w-100 d-block h1 mb-2")
            price_span = price_tag.find("span") if price_tag else None
            price = price_span.get_text(strip=True).replace(",", ".") if price_span else "N/A"

            offers.append({
                "retailer": retailer,
                "price": price,
                "url": link
            })
        except Exception:
            continue
    return offers

async def scrape_row(session, row, i, total):
    row = row.to_dict()
    name = row["name"]
    search_term = extract_ram_search_term(name)
    capacity = int(row["size"])
    ddr_type = None
    match = re.search(r"DDR\d", name.upper())
    if match:
        ddr_type = match.group(0)

    search_url = construct_ram_search_url(search_term, capacity, ddr_type)
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    print(f"[{i+1}/{total}] scraping {name} -> {search_url}")

    soup = await fetch_and_parse(session, search_url, headers, i, total, name)
    if soup:
        offers = extract_offers(soup, search_term)
        row["offers"] = json.dumps(offers)

        if offers:
            print(f"[{i+1}/{total}] found {len(offers)} offers for {name}")
        else:
            print(f"[{i+1}/{total}] no offers for {name}")
    else:
        row["offers"] = json.dumps([])

    save_partial_result(row)

async def run_scraper():
    df = pd.read_csv(INPUT_CSV)
    total = len(df)

    async with aiohttp.ClientSession() as session:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bounded_scrape(row, i):
            async with sem:
                await scrape_row(session, row, i, total)

        await asyncio.gather(*(bounded_scrape(row, i) for i, row in df.iterrows()))

    print(f"\nscraping complete - saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(run_scraper())