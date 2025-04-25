import requests

url = "https://www.expedia.com/Flights-Search?flight-type=on&mode=search&trip=roundtrip&leg1=from:Chicago,%20IL,%20United%20States%20of%20America%20(ORD-O%27Hare%20Intl.),to:New%20York,%20NY,%20United%20States%20of%20America%20(NYC-All%20Airports),departure:5/8/2025TANYT,fromType:AIRPORT,toType:METROCODE&leg2=from:New%20York,%20NY,%20United%20States%20of%20America%20(NYC-All%20Airports),to:Chicago,%20IL,%20United%20States%20of%20America%20(ORD-O%27Hare%20Intl.),departure:5/15/2025TANYT,fromType:METROCODE,toType:AIRPORT&options=cabinclass:economy&fromDate=5/8/2025&toDate=5/15/2025&d1=2025-5-8&d2=2025-5-15&passengers=adults:1,infantinlap:N"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(response.text)  # This will print the HTML content of the page
else:
    print(f"Failed to fetch the page. Status code: {response.status_code}")