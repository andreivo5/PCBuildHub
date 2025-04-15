import asyncio
import aiohttp
import pandas as pd
import json
import os
import random
from bs4 import BeautifulSoup
from urllib.parse import quote

INPUT_CSV = "GPU.csv"
OUTPUT_CSV = "gpu_prices_output_async.csv"
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

def construct_gpu_search_url(subbrand, model):
    query = f"{subbrand} {model}"
    return f"https://www.gputracker.eu/en/search/category/1/graphics-cards?textualSearch={quote(query)}"

def save_partial_result(row):
    if not os.path.exists(OUTPUT_CSV):
        pd.DataFrame([row]).to_csv(OUTPUT_CSV, index=False)
    else:
        df_existing = pd.read_csv(OUTPUT_CSV)
        df_new = pd.concat([df_existing, pd.DataFrame([row])], ignore_index=True)
        df_new.to_csv(OUTPUT_CSV, index=False)

async def fetch_and_parse(session, url, headers, i, total, name):
    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status == 200:
                html = await response.text()
                return BeautifulSoup(html, "html.parser")
            else:
                print(f"[{i+1}/{total}] http {response.status} for {name}")
    except Exception as e:
        print(f"[{i+1}/{total}] fetch error for {name}: {e}")
    return None

def extract_offers(soup, search_term):
    offer_blocks = soup.find_all("div", class_="stock-item-block")
    offers = []

    for offer_block in offer_blocks[:10]:
        try:
            link_tag = offer_block.find("a", class_="tracked-product-click", href=True)
            link = link_tag["href"].strip() if link_tag else "N/A"
            if not link.startswith("http"):
                link = "https://www.gputracker.eu" + link

            retailer_span = offer_block.find("span", class_="text-muted h6 d-block lead mb-2")
            retailer = retailer_span.get_text(strip=True) if retailer_span else "N/A"

            price_div = offer_block.find("div", class_="font-weight-bold text-secondary w-100 d-block h1 mb-2")
            price_span = price_div.find("span") if price_div else None
            price = price_span.get_text(strip=True).replace(",", ".") if price_span else "N/A"

            offers.append({
                "retailer": retailer,
                "price": price,
                "url": link
            })
        except Exception as e:
            print(f"- ERROR - failed to parse offer for {search_term}: {e}")
            continue

    return offers

async def scrape_row(session, row, i, total):
    row = row.to_dict()
    subbrand = row["name"].split()[0]
    model = row["model"]
    search_term = f"{subbrand} {model}"
    search_url = construct_gpu_search_url(subbrand, model)
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    soup = await fetch_and_parse(session, search_url, headers, i, total, row["name"])
    if soup:
        offers = extract_offers(soup, search_term)
        row["offers"] = json.dumps(offers)

        if offers:
            print(f"[{i+1}/{total}] found {len(offers)} offers for {row['name']}")
        else:
            print(f"[{i+1}/{total}] no offers for {row['name']}")
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