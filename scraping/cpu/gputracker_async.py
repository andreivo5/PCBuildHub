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

INPUT_CSV = "CPU.csv"
OUTPUT_CSV = "CPU_gputracker.csv"
START_ROW = 0
MAX_ROWS = None
CONCURRENT_LIMIT = 5

semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

def construct_cpu_search_url(brand, series, model):
    search_term = f"{brand} {series} {model}"
    encoded_search = urllib.parse.quote(search_term)
    return f"https://www.gputracker.eu/en/search/category/2/processors?textualSearch={encoded_search}&onlyInStock=true"

def get_multiple_offers(soup, search_term=""):
    offer_blocks = soup.find_all("a", class_="tracked-product-click", href=True)
    offers = []
    first_image = ""

    if not offer_blocks:
        print(f"- NO OFFERS - {search_term}")
        return json.dumps([]), ""

    for offer in offer_blocks[:10]:
        try:
            link = offer["href"].strip()
            if not link.startswith("http"):
                link = "https://www.gputracker.eu" + link

            retailer = offer.get("data-shop-name", "N/A")
            price_tag = offer.select_one("div.font-weight-bold.text-secondary span")
            price = price_tag.get_text(strip=True).replace(",", ".") if price_tag else "N/A"

            if not first_image:
                img_tag = offer.select_one("img")
                if img_tag and img_tag.get("src"):
                    first_image = img_tag["src"]
                    if first_image.startswith("/"):
                        first_image = "https://www.gputracker.eu" + first_image

            offers.append({
                "retailer": retailer,
                "price": price,
                "url": link
            })

        except Exception as e:
            print(f"- ERROR - parsing failed for {search_term}: {e}")
            continue

    print(f"- FOUND - {len(offers)} offers for {search_term}")
    return json.dumps(offers), first_image

async def fetch_cpu_data(session, i, row, total, df):
    async with semaphore:
        brand = row["brand"]
        series = row["series"]
        model = row["model"]
        search_term = f"{brand} {series} {model}"
        search_url = construct_cpu_search_url(brand, series, model)
        index_display = f"[{i+1}/{total}]"

        print(f"{index_display} scraping {search_term}")
        print(f"{index_display} url: {search_url}")

        try:
            async with session.get(search_url, headers=HEADERS, timeout=20) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, "html.parser")
                    offers_json, first_image = get_multiple_offers(soup, search_term)
                else:
                    print(f"- HTTP ERROR - {search_term} ({response.status})")
                    offers_json = json.dumps([{"retailer": "N/A", "price": "HTTP Error", "url": search_url}])
                    first_image = ""
        except Exception as e:
            print(f"- EXCEPTION - {search_term}: {e}")
            offers_json = json.dumps([{"retailer": "Error", "price": "Error", "url": str(e)}])
            first_image = ""

        df.at[i, "offers"] = offers_json
        df.at[i, "image"] = first_image
        df.iloc[:i+1].to_csv(OUTPUT_CSV, index=False)

        await asyncio.sleep(random.uniform(0.5, 1.5))

async def scrape_cpu_prices():
    df = pd.read_csv(INPUT_CSV)

    if MAX_ROWS is not None:
        df = df.iloc[START_ROW:START_ROW + MAX_ROWS].copy().reset_index(drop=True)
    else:
        df = df.copy().reset_index(drop=True)

    df["offers"] = ""
    df["image"] = ""
    total = len(df)

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_cpu_data(session, i, row, total, df)
            for i, row in df.iterrows()
        ]
        await asyncio.gather(*tasks)

    duration = round(time.time() - start_time, 2)
    print(f"\nscraping complete - {total} rows")
    print(f"time taken: {duration} seconds")
    print(f"saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(scrape_cpu_prices())