import json

# filepath: d:\Personal\cheapFlightScraper\airports.json
def transform_airports_json(input_file, output_file):
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Transform the JSON data
    transformed_data = {}
    for key, value in data.items():
        iata = value.get("iata")
        if iata:  # Only include entries with non-empty "iata"
            transformed_data[iata] = {
                "id": iata,
                "name": value.get("name", ""),
                "city": value.get("city", ""),
                "state": value.get("state", ""),
                "country": value.get("country", "")
            }

    # Write the transformed data back to a new JSON file
    with open(output_file, 'w') as file:
        json.dump(transformed_data, file, indent=4)

# Input and output file paths
input_file = "./airports.json"
output_file = "./flight_data.json"

# Run the function
transform_airports_json(input_file, output_file)