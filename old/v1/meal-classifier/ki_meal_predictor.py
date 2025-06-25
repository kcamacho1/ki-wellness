##
# Copyright April 15, 2025, 
# Kristina Camacho, All rights reserved.
##

import streamlit as st
import numpy as np
import os
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense
from usda_api import search_usda_foods, get_usda_food_nutrition

st.set_page_config(page_title="Ki Wellness: Smart Meal Classifier", page_icon="🥗", layout="centered")
st.title("🥗 Ki Wellness: AI-Powered Meal Evaluator")
st.markdown("Search for foods using the USDA database, then let AI analyze how healthy and goal-aligned your meal is.")

# --- Initialize session state to persist selected foods ---
if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = {}

# --- USDA Food Search ---
search_query = st.text_input("🔍 Search for a food using USDA database:")

if search_query:
    try:
        results = search_usda_foods(search_query)
        if results:
            food_choices = {f"{food['description']} (ID: {food['fdcId']})": food["fdcId"] for food in results}
            selected_from_search = st.multiselect(
                "🍴 Select food items from search:",
                options=list(food_choices.keys()),
                key="food_selector"
            )
            for label in selected_from_search:
                st.session_state.selected_foods[label] = food_choices[label]
        else:
            st.warning("No foods found. Try a more specific keyword.")
    except Exception as e:
        st.error(f"USDA API Error: {e}")

# --- Selected Foods Display ---
if st.session_state.selected_foods:
    st.subheader("✅ Selected Foods (Saved Across Searches)")
    for label in st.session_state.selected_foods:
        st.markdown(f"- {label}")

    meal_type = st.selectbox("🍽️ Meal Type:", ["Breakfast", "Lunch", "Dinner", "Snack"])
    goal = st.selectbox("🎯 Health Goal:", ["Weight Loss", "Muscle Gain", "Balanced Nutrition"])


    # --- Calculate Nutrition ---
    meal_nutrition = np.zeros(6)
    nutrition_labels = ["Calories", "Protein (g)", "Fat (g)", "Carbs (g)", "Sugar (g)", "Fiber (g)"]

    st.subheader("📊 Nutritional Summary")
    for label, fdc_id in st.session_state.selected_foods.items():
        try:
            nutrition = get_usda_food_nutrition(fdc_id)
            values = [nutrition[n] for n in nutrition_labels]
            meal_nutrition += values
            st.markdown(f"**{label}**")
            for n, v in zip(nutrition_labels, values):
                st.write(f"- {n}: {v}")
        except Exception as e:
            st.error(f"Failed to fetch nutrition for {label}: {e}")


    # --- Normalize for Model ---
    X_train = np.array([
        [350, 25, 10, 20, 5, 8],
        [700, 15, 30, 50, 20, 2],
        [250, 20, 8, 15, 4, 7],
        [800, 10, 40, 60, 25, 1],
        [300, 22, 9, 18, 6, 6]
    ], dtype=float)
    y_train = np.array([1, 0, 1, 0, 1])
    X_max = np.max(X_train, axis=0)
    input_norm = meal_nutrition / X_max

    # --- Load or Train Model ---
    model_path = "meal_model.h5"
    if os.path.exists(model_path):
        model = load_model(model_path)
    else:
        model = Sequential([
            Dense(8, activation='relu', input_shape=(6,)),
            Dense(4, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X_train / X_max, y_train, epochs=100, verbose=0)
        model.save(model_path)

    prediction = model.predict(np.array([input_norm]))[0][0]

    st.subheader("🧠 AI Healthiness Prediction")
    st.markdown(f"**Healthy Probability:** `{prediction:.2f}`")
    if prediction > 0.5:
        st.success("✅ This meal is classified as **Healthy**")
    else:
        st.error("⚠️ This meal is classified as **Not Healthy**")

    # --- Goal Check ---
    def goal_match(n, goal):
        calories, protein, fat, carbs, sugar, fiber = n
        if goal == "Weight Loss":
            return calories < 500 and sugar < 10
        elif goal == "Muscle Gain":
            return protein > 20 and calories > 400
        elif goal == "Balanced Nutrition":
            return all([calories < 700, protein > 15, fiber > 3])
        return False

    if goal_match(meal_nutrition, goal):
        st.success(f"🎯 This meal supports your **{goal}** goal.")
    else:
        st.warning(f"⚠️ This meal may not fully support **{goal}**. Consider adjustments.")

else:
    st.info("👆 Use the search above to add foods to your meal.")
