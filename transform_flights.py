import json

# Load the current structure from a JSON file
with open('flights_output.json', 'r') as file:
    data = json.load(file)

# Function to transform the structure
def transform_structure(flight_data):
    if not flight_data:  # Check if flight_data is empty
        return {
            "min_price": None,  # Set min_price to None if no data is available
            "data": []
        }
    
    # Find the minimum price across all airlines
    min_price = min(flight["min_price"] for flight in flight_data)
    
    # Return the transformed structure
    return {
        "min_price": min_price,
        "data": flight_data
    }

# Example usage: Transform a specific city's flight data
for city, city_data in data.items():
    for destination, flights in city_data.items():
        if isinstance(flights[1], list) and flights[1]:  # Ensure it's a non-empty list of flights
            city_data[destination][1] = transform_structure(flights[1])
        else:
            city_data[destination][1] = transform_structure([])  # Handle empty or invalid data

# Save the transformed structure back to a JSON file
with open('transformed_flights_output.json', 'w') as file:
    json.dump(data, file, indent=4)

print("Transformation complete. Saved to 'transformed_flights_output.json'.")