import requests

def fetch_flight_data():
    # Define the API endpoint
    url = "https://serpapi.com/search"
    
    # Define the query parameters, including the API key
    params = {
        "engine": "google_flights",
        "departure_id": "JFK",  # Replace with your desired departure airport code
        "arrival_id": "LAX",  # Replace with your desired arrival airport code
        "outbound_date": "2025-05-01",  # Replace with your desired outbound date
        "return_date": "2025-05-10",  # Replace with your desired return date
        "currency": "USD",  # Currency for the results
        "hl": "en",  # Language for the results
        "api_key": "b378ab498cb0201bc87157b6ee171c79baf592943012e7293a8051c53e18ecdd"  # Your API key
    }
    
    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse and return the JSON data
            data = response.json()
            return data
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")  # Print the response for debugging
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
if __name__ == "__main__":
    flight_data = fetch_flight_data()
    if flight_data:
        print(flight_data)