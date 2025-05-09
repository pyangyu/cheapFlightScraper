import json

def find_cheapest_price_from_file(data):
    # Initialize variables to store the cheapest flight details
    cheapest_price = float('inf')
    cheapest_flight_details = None

    # Check if price_insights is available
    if "price_insights" in data and "lowest_price" in data["price_insights"]:
        cheapest_price = data["price_insights"]["lowest_price"]

    # Check best_flights and other_flights for the lowest price
    for flight_group in ["best_flights", "other_flights"]:
        if flight_group in data:
            for flight in data[flight_group]:
                if "price" in flight and flight["price"] <= cheapest_price:
                    cheapest_price = flight["price"]
                    # Extract flight details
                    first_leg = flight["flights"][0]
                    last_leg = flight["flights"][-1]
                    cheapest_flight_details = {
                        "departure_airport": first_leg["departure_airport"]["name"],
                        "departure_time": first_leg["departure_airport"]["time"],
                        "arrival_airport": last_leg["arrival_airport"]["name"],
                        "arrival_time": last_leg["arrival_airport"]["time"],
                        "price": flight["price"],
                        "airline": first_leg["airline"],
                        "flight_number": first_leg["flight_number"],
                        "total_duration": flight.get("total_duration", "N/A"),
                        "carbon_emissions": flight.get("carbon_emissions", {}).get("this_flight", "N/A")
                    }

    # Return the cheapest price and its details
    return cheapest_flight_details if cheapest_flight_details else {"price": cheapest_price}

def get_us_airports(file_path):
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        
        us_airports = {}
        for airport_code, airport_info in data.items():
            if airport_info.get("country") == "US":
                us_airports[airport_code] = airport_info
        
        return us_airports
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {file_path}")
        return None

# Example usage
if __name__ == "__main__":
    file_path = "./flight_data.json"  # Path to the JSON file
    
    # Get US airports and save to new file
    us_airports = get_us_airports(file_path)
    if us_airports:
        with open("flight_data_us.json", "w") as f:
            json.dump(us_airports, f, indent=4)
        print(f"Successfully saved {len(us_airports)} US airports to flight_data_us.json")
    
    # Original flight data processing
    # try:
    #     with open(file_path, "r") as json_file:
    #         data = json.load(json_file)
    #     cheapest_flight = find_cheapest_price_from_file(data)
    #     if cheapest_flight:
    #         print("Cheapest Flight Details:")
    #         print(json.dumps(cheapest_flight, indent=4))
    #     else:
    #         print("No flight details found.")
    # except FileNotFoundError:
    #     print(f"Error: File not found at {file_path}")
    # except json.JSONDecodeError:
    #     print(f"Error: Failed to decode JSON from {file_path}")