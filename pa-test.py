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

DESTINATIONS = DEPARTURES

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

def parse_flight_info(text):
    """
    解析航班信息文本，提取关键信息
    参数:
        text: 包含航班信息的文本
    返回:
        解析后的航班信息字典或None（如果解析失败）
    """
    try:
        # 提取航空公司名称
        airline_match = re.search(r'^(\w+)\s+(?:Nonstop\s+)?from', text)
        if not airline_match:
            return None
        airline = airline_match.group(1)

        # 提取最低价格
        min_price_match = re.search(r'from\s+\$(\d+)', text)
        min_price = int(min_price_match.group(1)) if min_price_match else None

        # 提取价格区间
        price_range_match = re.search(r'Typical price:\s+\$(\d+)–(\d+)', text)
        if price_range_match:
            price_min = int(price_range_match.group(1))
            price_max = int(price_range_match.group(2))
        else:
            price_min = price_max = None

        # 提取航班类型和数量
        is_nonstop = 'Nonstop' in text
        flights_match = re.search(r'(\d+)\s+weekly\s+(nonstop|connecting)\s+flights', text)
        weekly_flights = int(flights_match.group(1)) if flights_match else None
        flight_type = flights_match.group(2) if flights_match else None

        return {
            "airline": airline,
            "is_nonstop": is_nonstop,
            "min_price": min_price,
            "price_range": {
                "min": price_min,
                "max": price_max
            },
            "weekly_flights": weekly_flights,
            "flight_type": flight_type
        }
    except Exception as e:
        print(f"解析错误: {e}")
        return None

def crawl2(departure, destination):
    """
    从Google Flights抓取指定出发地和目的地的航班信息
    参数:
        departure: 出发城市
        destination: 目的地城市
    返回:
        (目的地, 航班信息列表)的元组
    """
    url = f"https://www.google.com/travel/flights/flights-from-{departure.lower()}-to-{destination.lower()}.html"
    try:
        # 发送请求获取页面内容
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[{destination}] 请求失败，状态码: {response.status_code}")
            return destination.lower(), []

        # 解析页面内容
        tree = html.fromstring(response.content)
        ul_elements = tree.xpath('//h2[contains(text(), "Popular airlines")]/ancestor::section[1]//ul')

        # 提取航班信息
        results = []
        for ul in ul_elements:
            li_elements = ul.xpath('.//li')
            for li in li_elements:
                text = ' '.join(li.xpath('.//text()')).strip()
                if text:
                    flight_info = parse_flight_info(text)
                    if flight_info:
                        results.append(flight_info)

        return destination.lower(), results
    except Exception as e:
        print(f"[{destination}] 错误: {e}")
        return destination.lower(), []

def main():
    """
    主函数：并行抓取所有城市对的航班信息并保存结果
    """
    start = time.time()

    # 初始化结果存储
    grouped_results = defaultdict(dict)
    city_pairs = list(itertools.product(DEPARTURES, DESTINATIONS))

    # 使用线程池并行抓取数据
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(lambda args: crawl2(*args), city_pairs)
        for (departure, destination), results in zip(city_pairs, futures):
            if results:  # 只保存有结果的航线
                grouped_results[departure][destination] = results

    # 保存结果到JSON文件
    with open("flights_output.json", "w", encoding="utf-8") as f:
        json.dump(grouped_results, f, indent=2, ensure_ascii=False)

    end = time.time()
    print(f"结果已保存到 flights_output.json")
    print(f"⏱️ 总执行时间: {end - start:.2f} 秒")