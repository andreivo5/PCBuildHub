import asyncio
import aiohttp
import pandas as pd
import json
import os
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

INPUT_CSV = "PSU.csv"
OUTPUT_CSV = "psu_prices_output.csv"
CONCURRENCY = 8

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 Chrome/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/121.0.0.0"
]

def extract_search_term(name):
    parts = name.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name

def construct_psu_search_url(search_term, power):
    base_url = "https://www.gputracker.eu/en/search/category/6/power-supplies"
    query = f"textualSearch={quote(search_term)}&onlyInStock=true"
    if power:
        query += f"&fr_psu.power_min={power}&fr_psu.power_max={power}"
    return f"{base_url}?{query}"

def save_partial_result(row):
    if not os.path.exists(OUTPUT_CSV):
        pd.DataFrame([row]).to_csv(OUTPUT_CSV, index=False)
    else:
        existing = pd.read_csv(OUTPUT_CSV)
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        updated.to_csv(OUTPUT_CSV, index=False)

async def fetch_and_parse(session, url, headers):
    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status == 200:
                return BeautifulSoup(await response.text(), "html.parser")
    except:
        pass
    return None

def extract_offers(soup):
    offer_blocks = soup.find_all("div", class_="stock-item-block")
    offers = []

    for offer in offer_blocks[:10]:
        try:
            link_tag = offer.find("a", class_="tracked-product-click", href=True)
            link = link_tag["href"].strip() if link_tag else ""
            if not link.startswith("http"):
                link = "https://www.gputracker.eu" + link

            retailer_tag = offer.find("span", class_="text-muted h6 d-block lead mb-2")
            retailer = retailer_tag.get_text(strip=True) if retailer_tag else "N/A"

            price_tag = offer.find("div", class_="font-weight-bold text-secondary w-100 d-block h1 mb-2")
            price = price_tag.find("span").get_text(strip=True).replace(",", ".") if price_tag else "N/A"

            offers.append({"retailer": retailer, "price": price, "url": link})
        except:
            continue
    return offers

async def scrape_row(session, row, i, total):
    row = row.to_dict()
    name = row["name"]
    power = int(row.get("power", 0))
    search_term = extract_search_term(name)
    search_url = construct_psu_search_url(search_term, power)
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    print(f"[{i+1}/{total}] scraping {search_term} | {power}w")

    soup = await fetch_and_parse(session, search_url, headers)
    if soup:
        offers = extract_offers(soup)
        row["offers"] = json.dumps(offers)
        if offers:
            print(f"[{i+1}/{total}] found {len(offers)} offers for {name}")
        else:
            print(f"[{i+1}/{total}] no offers for {name}")
    else:
        row["offers"] = json.dumps([])
        print(f"[{i+1}/{total}] failed to load page for {name}")

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