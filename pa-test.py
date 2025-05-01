import requests
from lxml import html
import re, json
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import itertools
import time

DESTS = [
    "ATL",  # Atlanta Hartsfield-Jackson
    "LAX",  # Los Angeles
    "ORD",  # Chicago O'Hare
    "DFW",  # Dallas/Fort Worth
    "DEN",  # Denver
    "JFK",  # New York John F. Kennedy
    "SFO",  # San Francisco
    "SEA",  # Seattle-Tacoma
    "LAS",  # Las Vegas McCarran
    "MCO",  # Orlando
    "CLT",  # Charlotte Douglas
    "PHX",  # Phoenix Sky Harbor
    "MIA",  # Miami
    "IAH",  # Houston George Bush
    "BOS",  # Boston Logan
    "MSP",  # Minneapolis/St. Paul
    "FLL",  # Fort Lauderdale
    "DTW",  # Detroit Metro
    "PHL",  # Philadelphia
    "LGA",  # New York LaGuardia
    "BWI",  # Baltimore-Washington
    "SLC",  # Salt Lake City
    "DCA",  # Washington National
    "SAN",  # San Diego
    "TPA",  # Tampa
    "HNL",  # Honolulu
    "MDW",  # Chicago Midway
    "AUS",  # Austin-Bergstrom
    "STL",  # St. Louis Lambert
    "DAL",  # Dallas Love Field
    "BNA",  # Nashville
    "PDX",  # Portland
    "SJC",  # San Jose
    "OAK",  # Oakland
    "CLE",  # Cleveland
    "SMF",  # Sacramento
    "RSW",  # Fort Myers
    "PIT",  # Pittsburgh
    "MCI",  # Kansas City
    "SNA",  # Santa Ana/Orange County
    "MSY",  # New Orleans
    "RDU",  # Raleigh-Durham
    "CMH",  # Columbus
    "SAT",  # San Antonio
    "HOU",  # Houston Hobby
    "ONT",  # Ontario (California)
    "IND",  # Indianapolis
    "CVG",  # Cincinnati
    "JAX",  # Jacksonville
    "ANC",  # Anchorage
    "PBI",  # West Palm Beach
]

DEPARTURES = [
    "atlanta",
    "los-angeles",
    "chicago",            # O'Hare or Midway 都可以叫 chicago
    "dallas",             # 合并 DFW 和 DAL
    "denver",
    "new-york",           # JFK 和 LGA 可统一为 new-york
    "san-francisco",
    "seattle",
    "las-vegas",
    "orlando",
    "charlotte",
    "phoenix",
    "miami",
    "houston",            # IAH 和 HOU 合并为 houston
    "boston",
    "minneapolis",        # 对应 MSP
    "fort-lauderdale",
    "detroit",
    "philadelphia",
    "baltimore",
    "salt-lake-city",
    "washington",         # 可统一 DCA/IAD 为 washington
    "san-diego",
    "tampa",
    "honolulu",
    "austin",
    "st-louis",
    "nashville",
    "portland",
    "san-jose",
    "oakland",
    "cleveland",
    "sacramento",
    "fort-myers",
    "pittsburgh",
    "kansas-city",
    "santa-ana",          # 对应 Orange County
    "new-orleans",
    "raleigh",
    "columbus",
    "san-antonio",
    "ontario",            # California
    "indianapolis",
    "cincinnati",
    "jacksonville",
    "anchorage",
    "west-palm-beach"
]

DESTINATIONS = [
    "atlanta",
    "los-angeles",
    "chicago",            # O'Hare or Midway 都可以叫 chicago
    "dallas",             # 合并 DFW 和 DAL
    "denver",
    "new-york",           # JFK 和 LGA 可统一为 new-york
    "san-francisco",
    "seattle",
    "las-vegas",
    "orlando",
    "charlotte",
    "phoenix",
    "miami",
    "houston",            # IAH 和 HOU 合并为 houston
    "boston",
    "minneapolis",        # 对应 MSP
    "fort-lauderdale",
    "detroit",
    "philadelphia",
    "baltimore",
    "salt-lake-city",
    "washington",         # 可统一 DCA/IAD 为 washington
    "san-diego",
    "tampa",
    "honolulu",
    "austin",
    "st-louis",
    "nashville",
    "portland",
    "san-jose",
    "oakland",
    "cleveland",
    "sacramento",
    "fort-myers",
    "pittsburgh",
    "kansas-city",
    "santa-ana",          # 对应 Orange County
    "new-orleans",
    "raleigh",
    "columbus",
    "san-antonio",
    "ontario",            # California
    "indianapolis",
    "cincinnati",
    "jacksonville",
    "anchorage",
    "west-palm-beach"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Referer": "https://www.expedia.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

def parse_info(text, destination):
    match = re.search(r'Select (.*?) flight.*?departing .*? ([A-Z][a-z]+ \d+).*?returning .*? ([A-Z][a-z]+ \d+)', text)
    price_match = re.search(r'([$€£])(\d+)', text)

    if not (match and price_match):
        return None

    year = datetime.now().year
    try:
        out_date = datetime.strptime(f"{match[2]} {year}", "%b %d %Y").strftime("%Y-%m-%d")
        ret_date = datetime.strptime(f"{match[3]} {year}", "%b %d %Y").strftime("%Y-%m-%d")
    except:
        return None

    return {
        "departure_id": "chicago",
        "destination_id": destination.lower(),
        "currency": price_match[1],
        "price": int(price_match[2]),
        "outbound_date": out_date,
        "return_date": ret_date,
        "flight_company": match[1]
    }

def crawl(destination):
    url = f"https://www.expedia.com/lp/flights/chi/{destination.lower()}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[{destination}] Failed to fetch, status: {response.status_code}")
            return destination.lower(), []

        tree = html.fromstring(response.content)
        # 这是一个假设的 XPath，真实页面可能不同（需要你打开页面源代码查看）
        spans = tree.xpath('//span[contains(@class, "is-visually-hidden")]/text()')

        results = []
        for text in spans:
            text = text.strip()
            if text.startswith("Select") and "flight" in text:
                data = parse_info(text, destination)
                if data:
                    results.append(data)

        return destination.lower(), results
    except Exception as e:
        print(f"[{destination}] Error: {e}")
        return destination.lower(), []
    
def crawl2(departure, destination):
    url = f"https://www.google.com/travel/flights/flights-from-{departure.lower()}-to-{destination.lower()}.html"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[{destination}] Failed to fetch, status: {response.status_code}")
            return destination.lower(), []

        tree = html.fromstring(response.content)

        # 示例：抓取页面标题或描述等静态内容（JS 渲染的航班数据抓不到）
        ul_elements = tree.xpath('//h2[contains(text(), "Popular airlines")]/ancestor::section[1]//ul')

        results = []
        for ul in ul_elements:
            li_elements = ul.xpath('.//li')
            for li in li_elements:
                text = ' '.join(li.xpath('.//text()')).strip()
                if text:
                    results.append(text)

        return destination, results
    except Exception as e:
        print(f"[{destination}] Error: {e}")
        return destination.lower(), {}

def main():
    start = time.time()  # 开始计时

    grouped_results = defaultdict(dict)
    city_pairs = list(itertools.product(DEPARTURES, DESTINATIONS))

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(lambda args: crawl2(*args), city_pairs)

        for (departure, destination), results in zip(city_pairs, futures):
            grouped_results[departure][destination] = results

    with open("flights_output.json", "w", encoding="utf-8") as f:
        json.dump(grouped_results, f, indent=2, ensure_ascii=False)

    end = time.time()  # 结束计时
    print(f"Saved to flights_output.json")
    print(f"⏱️ Total execution time: {end - start:.2f} seconds")