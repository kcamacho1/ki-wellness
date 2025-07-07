entry = {
    "user_id": user_id,
    "date_logged": date.today().isoformat(),
    "meal_type": "Other",
    "food_name": food_name,
    "servings": servings,
    "serving_unit": serving_unit,
    "calories": round(nutrition["calories"] * servings, 2),
    "protein": round(nutrition["protein"] * servings, 2),
    "carbs": round(nutrition["carbs"] * servings, 2),
    "fat": round(nutrition["fat"] * servings, 2),
}
# Add micronutrients to entry
for k in [
    "vitamin_a","vitamin_c","vitamin_d","vitamin_e","vitamin_k",
    "vitamin_b1","vitamin_b2","vitamin_b3","vitamin_b6","vitamin_b12","folate",
    "calcium","iron","magnesium","potassium","zinc","sodium",
    "copper","selenium","manganese"
]:
    entry[k] = round((nutrition.get(k) or 0) * servings, 2)
