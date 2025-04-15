import aiohttp
import asyncio
import pandas as pd
import time
import urllib.parse
import json
import random
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL_CASE = "https://www.gputracker.eu/en/search/category/7/cases?textualSearch="
INPUT_CSV = "Case.csv"
OUTPUT_CSV = "case_prices3.csv"
START_ROW = 200
MAX_ROWS = None
CONCURRENT_LIMIT = 5

semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

def extract_case_query(name):
    keywords = ["ATX", "MicroATX", "ITX"]
    split_words = name.split()

    for i, word in enumerate(split_words):
        if any(keyword in word for keyword in keywords):
            return " ".join(split_words[:i])
    return " ".join(split_words)

def construct_case_search_url(query):
    encoded_query = urllib.parse.quote(query)
    return BASE_URL_CASE + encoded_query + "&onlyInStock=true"

def get_multiple_offers(soup, search_term=""):
    offer_blocks = soup.find_all("div", class_="stock-item-block")
    offers = []

    if not offer_blocks:
        print(f"no offers found for {search_term}")
        return json.dumps([])

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
            print(f"failed to parse offer block for {search_term}: {e}")
            continue

    print(f"{len(offers)} offer(s) found for {search_term}")
    return json.dumps(offers)

async def fetch_case_data(session, i, row, total, df):
    async with semaphore:
        name = row["name"]
        search_term = extract_case_query(name)
        search_url = construct_case_search_url(search_term)
        index_display = f"[{i+1}/{total}]"

        print(f"{index_display} scraping {name}")
        print(f"{index_display} url: {search_url}")

        try:
            async with session.get(search_url, headers=HEADERS, timeout=20) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, "html.parser")
                    offers_json = get_multiple_offers(soup, search_term)
                else:
                    print(f"http {response.status} error for {search_term}")
                    offers_json = json.dumps([{
                        "retailer": "N/A",
                        "price": "HTTP Error",
                        "url": search_url
                    }])
        except Exception as e:
            print(f"exception while fetching {search_term}: {e}")
            offers_json = json.dumps([{
                "retailer": "Error",
                "price": "Error",
                "url": str(e)
            }])

        df.at[i, "offers"] = offers_json
        df.iloc[:i+1].to_csv(OUTPUT_CSV, index=False)

        await asyncio.sleep(random.uniform(0.5, 1.5))

async def scrape_case_prices():
    df = pd.read_csv(INPUT_CSV)
    if MAX_ROWS is not None:
        df = df.iloc[START_ROW:START_ROW + MAX_ROWS].copy()
    else:
        df = df.iloc[START_ROW:].copy()

    df["offers"] = ""
    total = len(df)

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_case_data(session, i, row, total, df)
            for i, row in df.iterrows()
        ]
        await asyncio.gather(*tasks)

    duration = round(time.time() - start_time, 2)
    print(f"\nscraping complete - {total} rows")
    print(f"time taken: {duration} seconds")
    print(f"saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(scrape_case_prices())
