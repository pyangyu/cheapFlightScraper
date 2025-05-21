let flightData = {}; // Initialize an empty object to hold the flight data

// Function to fetch the flight data from the JSON file
async function loadFlightData() {
    try {
        const response = await fetch('/static/flight_data_us.json'); // Correct path for Flask static files
        flightData = await response.json();
    } catch (error) {
        console.error('Error loading flight data:', error);
    }
}

function getClosestMatches(input, data, maxResults = 5) {
    const query = input.toLowerCase();

    // Sort the data based on priority
    const matches = Object.values(data)
        .filter(item =>
            item.id.toLowerCase().includes(query) || 
            item.city.toLowerCase().includes(query) || 
            item.name.toLowerCase().includes(query)
        )
        .sort((a, b) => {
            // Exact match with ID comes first
            if (a.id.toLowerCase() === query) return -1;
            if (b.id.toLowerCase() === query) return 1;

            // Prioritize matches where the first three letters match the ID
            const aIdStartsWith = a.id.toLowerCase().startsWith(query);
            const bIdStartsWith = b.id.toLowerCase().startsWith(query);

            if (aIdStartsWith && !bIdStartsWith) return -1;
            if (!aIdStartsWith && bIdStartsWith) return 1;

            // Prioritize matches where the first three letters match the city
            const aCityStartsWith = a.city.toLowerCase().startsWith(query);
            const bCityStartsWith = b.city.toLowerCase().startsWith(query);

            if (aCityStartsWith && !bCityStartsWith) return -1;
            if (!aCityStartsWith && bCityStartsWith) return 1;

            // Prioritize matches where the first three letters match the name
            const aNameStartsWith = a.name.toLowerCase().startsWith(query);
            const bNameStartsWith = b.name.toLowerCase().startsWith(query);

            if (aNameStartsWith && !bNameStartsWith) return -1;
            if (!aNameStartsWith && bNameStartsWith) return 1;

            // Otherwise, maintain the original order
            return 0;
        })
        .slice(0, maxResults); // Limit to maxResults

    return matches;
}

function setupAutocomplete(inputId, resultContainerId) {
    const inputField = document.getElementById(inputId);
    const resultContainer = document.getElementById(resultContainerId);

    inputField.addEventListener("input", () => {
        const query = inputField.value.trim();
        resultContainer.innerHTML = ""; // Clear previous results

        if (query.length > 0) {
            const results = getClosestMatches(query, flightData);
            results.forEach(result => {
                const resultItem = document.createElement("div");
                resultItem.textContent = `${result.id} - ${result.name} (${result.city})`;
                resultItem.classList.add("autocomplete-item");
                resultContainer.appendChild(resultItem);

                // Add click event to populate the input field
                resultItem.addEventListener("click", () => {
                    inputField.value = `${result.id} - ${result.city}`;
                    resultContainer.innerHTML = ""; // Clear results
                });
            });
            resultContainer.style.display = "block"; // Show the result box
        } else {
            resultContainer.style.display = "none"; // Hide the result box when input is empty
        }
    });

    // Hide results when clicking outside
    document.addEventListener("click", (event) => {
        if (!resultContainer.contains(event.target) && event.target !== inputField) {
            resultContainer.innerHTML = "";
            resultContainer.style.display = "none"; // Ensure the result box is hidden
        }
    });
}

function validateForm() {
    const fromInput = document.getElementById("from_airport").value.trim();
    const errorMessage = document.getElementById("error-message");

    if (!fromInput) {
        // Show error message if "From" input is empty
        errorMessage.textContent = "Please enter the From";
        errorMessage.style.display = "block";
    } else {
        // Hide error message if input is valid
        errorMessage.style.display = "none";

        // Take only the first three letters of the input
        const fromInputShort = fromInput.substring(6).toLowerCase().replace(/\s+/g, '-');

        // Redirect to result.html with the shortened input value as a query parameter
        const queryParams = new URLSearchParams({ from_airport: fromInputShort });
        window.location.href = `/result?${queryParams.toString()}`;
    }
}

function toggleDateInputs() {
    const isChecked = document.getElementById("enable_dates").checked;
    const outboundDate = document.getElementById("outbound_date");
    const returnDate = document.getElementById("return_date");

    // Enable or disable the date inputs based on the checkbox state
    outboundDate.disabled = isChecked;
    returnDate.disabled = isChecked;
}

function toggleToInput() {
    const isChecked = document.getElementById("enable_to").checked;
    const toInput = document.getElementById("to_airport");
    // Enable or disable the "To" input based on the checkbox state
    toInput.disabled = isChecked;
}

// Initialize autocomplete after loading the flight data
document.addEventListener("DOMContentLoaded", async () => {
    await loadFlightData(); // Load the flight data
    setupAutocomplete("from_airport", "from_results");
    setupAutocomplete("to_airport", "to_results");
});