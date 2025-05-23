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

def parse_flight_info_for_faq(question, answer):
    """
    把原始的 FAQ 问题和答案文本再做清洗或整合，返回一个 dict。
    在这里统一命名 key, 做后续处理。
    """
    # Skip FAQs 4, 5, 6, and 9
    if any(skip in question.lower() for skip in ["best airline", "direct flights available", "airlines have direct", "find cheap dates"]):
        return None

    result = {}
    
    # FAQ 1: Travel time
    if "how long does it take" in question.lower():
        time_match = re.search(r'(\d+)\s+hr\s+(\d+)\s+min', answer)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            result["travel_time"] = f"{hours}hr {minutes}min"
    
    # FAQ 2: Cheapest month
    elif "cheapest days" in question.lower():
        month_match = re.search(r'in\s+(\w+)\.\s+Typical\s+ticket\s+prices.*?\$(\d+)\s+to\s+\$(\d+)', answer)
        if month_match:
            result["cheapest_month"] = {
                "month": month_match.group(1),
                "price_range": {
                    "min": int(month_match.group(2)),
                    "max": int(month_match.group(3))
                }
            }
    
    # FAQ 3: Cheapest airlines
    elif "cheapest flights" in question.lower() and "airlines" in question.lower():
        airlines_info = []
        # Extract round-trip info
        round_trip_match = re.search(r'cheapest round-trip flight.*?with\s+(\w+)\s+from\s+\$(\d+)', answer)
        if round_trip_match:
            airlines_info.append(f"round-trip {round_trip_match.group(1)}: ${round_trip_match.group(2)}")
        
        # Extract one-way info
        one_way_match = re.search(r'cheapest one-way flight.*?with\s+(\w+)\s+from\s+\$(\d+)', answer)
        if one_way_match:
            airlines_info.append(f"one-way {one_way_match.group(1)}: ${one_way_match.group(2)}")
        
        # Extract other airline deals
        airline_deals = re.finditer(r'The cheapest (\w+) flight.*?is \$(\d+)', answer)
        for deal in airline_deals:
            airlines_info.append(f"{deal.group(1)}: ${deal.group(2)}")
        
        if airlines_info:
            result["cheapest_airlines"] = airlines_info
    
    # FAQ 7: Cheapest airline details
    elif "what are the cheapest flights" in question.lower():
        round_trip_match = re.search(r'starts at \$(\d+) from (.*?)\.', answer)
        one_way_match = re.search(r'one-way flight starts at \$(\d+) and departs on (.*?)\.', answer)
        
        cheapest_info = {}
        if round_trip_match:
            cheapest_info["round_trip"] = {
                "price": f"${round_trip_match.group(1)}",
                "dates": round_trip_match.group(2)
            }
        if one_way_match:
            cheapest_info["one_way"] = {
                "price": f"${one_way_match.group(1)}",
                "date": one_way_match.group(2)
            }
        if cheapest_info:
            result["cheapest_airline"] = cheapest_info
    
    # FAQ 8: Destination info
    elif "when should you" in question.lower():
        result["destination_info"] = answer

    return result if result else None

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

        # 提取最低价格 (处理带逗号的格式，如 $1,134)
        min_price_match = re.search(r'from\s+\$([\d,]+)', text)
        min_price = int(min_price_match.group(1).replace(',', '')) if min_price_match else None

        # 提取价格区间 (处理不同的格式，如 $1,250–1,450 或 $300-$1,900)
        price_range_match = re.search(r'Typical price:\s+\$([\d,]+)[–-]\$?([\d,]+)', text)
        if price_range_match:
            price_min = int(price_range_match.group(1).replace(',', ''))
            price_max = int(price_range_match.group(2).replace(',', ''))
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
    从 Google Flights 抓取航班信息 + Frequently asked questions
    返回: (departure, destination, list_of_flight_dicts_and_faq_dicts)
    """
    url = f"https://www.google.com/travel/flights/flights-from-{departure.lower()}-to-{destination.lower()}.html"
    try:
        # 1. 请求页面
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[{departure}->{destination}] 请求失败，状态码: {response.status_code}")
            return departure, destination, []

        tree = html.fromstring(response.content)
        results = []

        # 2. 抓航班列表
        # 先按组抓，再按文本解析
        ul_elements = tree.xpath('//h2[contains(text(), "Popular airlines")]/ancestor::section[1]//ul')
        for ul in ul_elements:
            for li in ul.xpath('.//li'):
                text = ' '.join(li.xpath('.//text()')).strip()
                if text:
                    flight_info = parse_flight_info(text)
                    if flight_info:
                        results.append(flight_info)

        # 3. 抓 FAQ
        # 找到 <h2>…Frequently asked questions…</h2> 的第一个祖先 <section>
        faq_section = tree.xpath('//h2[contains(text(), "Frequently asked questions")]/ancestor::section[1]')
        if faq_section:
            sec = faq_section[0]
            # 取该 section 下面的第二个直接子 <div>
            divs = sec.xpath('./div')
            if len(divs) >= 2:
                faq_container = divs[1]
                # 取这个 container 下所有子 <div>，每个是一个问答组
                faq_groups = faq_container.xpath('./div')
                for idx, faq_div in enumerate(faq_groups, start=1):
                    # 每个 faq_div 下第1个子 div 是 question，第2个是 answer
                    q_text = ' '.join(faq_div.xpath('./div[1]//text()')).strip()
                    a_text = ' '.join(faq_div.xpath('./div[2]//text()')).strip()
                    if q_text and a_text:
                        faq_info = parse_flight_info_for_faq(q_text, a_text)
                        if faq_info:  # 只添加非None的结果
                            results.append(faq_info)

        return results

    except Exception as e:
        print(f"[{departure}->{destination}] 抓取异常: {e}")
        return departure, destination, []

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
            if results and departure != destination:
                grouped_results[departure][destination] = results

    # 保存结果到JSON文件
    with open("flights_output_new.json", "w", encoding="utf-8") as f:
        json.dump(grouped_results, f, indent=2, ensure_ascii=False)

    end = time.time()
    print(f"结果已保存到 flights_output.json")
    print(f"⏱️ 总执行时间: {end - start:.2f} 秒")

if __name__ == "__main__":
    main() 
