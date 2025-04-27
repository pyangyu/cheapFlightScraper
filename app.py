from flask import Flask, render_template, request, jsonify
from fetch_flight_data_and_save import fetch_flight_data
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Load US airports
with open("flight_data_us.json", "r") as f:
    US_AIRPORTS = json.load(f)

# Convert to list of tuples (code, name, city) for dropdown and search
AIRPORT_OPTIONS = [(code, f"{info['name']} ({code})", info['city']) 
                  for code, info in US_AIRPORTS.items()]

@app.route('/search_airports', methods=['GET'])
def search_airports():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    results = []
    for code, name, city in AIRPORT_OPTIONS:
        if (query in code.lower() or 
            query in name.lower() or 
            query in city.lower()):
            results.append({
                'code': code,
                'name': name,
                'city': city
            })
    
    return jsonify(results[:10])  # Limit to 10 results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        departure_id = request.form.get('from_airport')
        arrival_id = request.form.get('to_airport')  # Can be None
        outbound_date = request.form.get('outbound_date')
        return_date = request.form.get('return_date')
        
        # Validate dates
        try:
            outbound_date = datetime.strptime(outbound_date, '%Y-%m-%d')
            return_date = datetime.strptime(return_date, '%Y-%m-%d')
            
            # Get flight results
            results = []
            if arrival_id:  # If specific arrival airport is selected
                flight_data = fetch_flight_data(departure_id, arrival_id, 
                                              outbound_date.strftime('%Y-%m-%d'),
                                              return_date.strftime('%Y-%m-%d'))
                if flight_data:
                    results.append({
                        'arrival_airport': arrival_id,
                        'airport_name': US_AIRPORTS[arrival_id]['name'],
                        'data': flight_data
                    })
            else:  # Search all airports
                for airport_code, airport_info in list(US_AIRPORTS.items())[:10]:  # Limit to 10 airports for demo
                    flight_data = fetch_flight_data(departure_id, airport_code, 
                                                  outbound_date.strftime('%Y-%m-%d'),
                                                  return_date.strftime('%Y-%m-%d'))
                    if flight_data:
                        results.append({
                            'arrival_airport': airport_code,
                            'airport_name': airport_info['name'],
                            'data': flight_data
                        })
            
            return render_template('index.html',
                                airports=AIRPORT_OPTIONS,
                                results=results,
                                selected_from=departure_id,
                                selected_to=arrival_id,
                                selected_outbound=outbound_date.strftime('%Y-%m-%d'),
                                selected_return=return_date.strftime('%Y-%m-%d'))
        except ValueError:
            return render_template('index.html',
                                airports=AIRPORT_OPTIONS,
                                error="Invalid date format")
    
    return render_template('index.html',
                         airports=AIRPORT_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True) 