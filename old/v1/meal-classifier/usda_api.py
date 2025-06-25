import requests

API_KEY = "MbvZGPVrj9P3eECrXnVpicA2xfS9Ky0LwaWrUjBR"
SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food/"

REQUIRED_NUTRIENTS = [
    "Energy",
    "Protein",
    "Total lipid (fat)",
    "Carbohydrate, by difference",
    "Sugars, total including NLEA",
    "Fiber, total dietary"
]

def search_usda_foods(query):
    params = {
        "api_key": API_KEY,
        "query": query,
        "pageSize": 10
    }
    res = requests.get(SEARCH_URL, params=params)
    res.raise_for_status()
    all_results = res.json().get("foods", [])

    # Keep only foods that have at least 4 of the 6 nutrients
    valid_results = []
    for food in all_results:
        nutrients = {n.get("nutrientName"): n.get("value") for n in food.get("foodNutrients", []) if n.get("nutrientName")}
        nutrient_match_count = sum(1 for key in REQUIRED_NUTRIENTS if key in nutrients and nutrients[key] is not None)

        if nutrient_match_count >= 4:
            valid_results.append(food)

    return valid_results

def get_usda_food_nutrition(fdc_id):
    res = requests.get(f"{FOOD_URL}{fdc_id}?api_key={API_KEY}")
    res.raise_for_status()
    food = res.json()

    # Nutrient IDs we want to capture
    nutrient_ids = {
        1008: "Calories",
        1003: "Protein (g)",
        1004: "Fat (g)",
        1005: "Carbs (g)",
        2000: "Sugar (g)",
        1079: "Fiber (g)"
    }

    # Initialize result with all 0s
    nutrients = {v: 0 for v in nutrient_ids.values()}

    for n in food.get("foodNutrients", []):
        # Try both ID locations: top-level or nested under 'nutrient'
        nid = n.get("nutrientId") or (n.get("nutrient") or {}).get("id")
        value = n.get("value")

        if nid in nutrient_ids and value is not None:
            label = nutrient_ids[nid]
            nutrients[label] = value

    return nutrients



