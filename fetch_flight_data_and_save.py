import requests
import json
from datetime import datetime
from test import find_cheapest_price_from_file

def fetch_flight_data(departure_id, arrival_id, outbound_date, return_date):
    # Define the API endpoint
    url = "https://serpapi.com/search"
    
    # Define the query parameters, including the API key
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "hl": "en",
        "api_key": "b378ab498cb0201bc87157b6ee171c79baf592943012e7293a8051c53e18ecdd"
    }
    
    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse and return the JSON data
            data = response.json()
            # Save the data to a JSON file with a unique name
            # filename = f"flight_data_{departure_id}_{arrival_id}_{outbound_date}_{return_date}.json"
            # with open(filename, "w") as json_file:
            #     json.dump(data, json_file, indent=4)
            # print(f"Successfully saved data for {arrival_id}")
            
            # Find the cheapest flight
            cheapest_flight = find_cheapest_price_from_file(data)
            if cheapest_flight and cheapest_flight.get("price") != float('inf'):
                print(f"\nCheapest Flight Details for {arrival_id}:")
                print(json.dumps(cheapest_flight, indent=4))
            else:
                print(f"{departure_id} to {arrival_id}: no flight")
            
            return data
        else:
            print(f"Error for {arrival_id}: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred for {arrival_id}: {e}")
        return None

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    # Get user input
    departure_id = input("Enter departure airport code (e.g., JFK): ").upper()
    
    while True:
        outbound_date = input("Enter outbound date (YYYY-MM-DD): ")
        if validate_date(outbound_date):
            break
        print("Invalid date format. Please use YYYY-MM-DD format.")
    
    while True:
        return_date = input("Enter return date (YYYY-MM-DD): ")
        if validate_date(return_date):
            break
        print("Invalid date format. Please use YYYY-MM-DD format.")
    
    # Load the list of airports
    with open("flight_data.json", "r") as f:
        airports_data = json.load(f)
    
    n = 10
    # Loop through each airport
    for airport_code, airport_info in airports_data.items():
        print(f"\nSearching flights to {airport_code} ({airport_info['name']})...")
        fetch_flight_data(departure_id, airport_code, outbound_date, return_date)
        n -= 1
        if n == 0:
            break