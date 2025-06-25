"""
Copyright April 15, 2025, 
Kristina Camacho, All rights reserved.
"""

import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Set page config
st.set_page_config(
	page_title="Ki Wellness Meal Classifier",
	page_icon="🥗",
	layout="centered"
	)
st.title("🥗 Ki Wellness: Meal Classifier")
st.markdown("Adjust the nutritional values of your meal and click **Predict** to see if it's considered healthy.")

# --- USER INPUT SLIDERS ---
calories = st.slider("Calories", 100, 1000, 400)
protein = st.slider("Protein (g)", 0, 50, 20)
fat = st.slider("Fat (g)", 0, 50, 10)
carbs = st.slider("Carbs (g)", 0, 100, 30)
sugar = st.slider("Sugar (g)", 0, 50, 10)
fiber = st.slider("Fiber (g)", 0, 20, 5)

user_input = np.array([[calories, protein, fat, carbs, sugar, fiber]])

# --- TRAINING DATA ---
X_train = np.array([
    [350, 25, 10, 20, 5, 8],
    [700, 15, 30, 50, 20, 2],
    [250, 20, 8, 15, 4, 7],
    [800, 10, 40, 60, 25, 1],
    [300, 22, 9, 18, 6, 6]
], dtype=float)

y_train = np.array([1, 0, 1, 0, 1])

# Normalize data (based on training max)
X_max = np.max(X_train, axis=0)
X_train_norm = X_train / X_max
user_input_norm = user_input / X_max

# Build & train the model (for demo purposes, we retrain on each run)
model = Sequential([
    Dense(8, activation='relu', input_shape=(6,)),
    Dense(4, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(X_train_norm, y_train, epochs=100, verbose=0)

# --- PREDICT BUTTON ---
if st.button("Predict"):
    prediction = model.predict(user_input_norm)[0][0]
    st.markdown(f"**Healthy Probability:** `{prediction:.2f}`")
    
    if prediction > 0.5:
        st.success("✅ This meal is classified as **Healthy**!")
    else:
        st.error("⚠️ This meal is classified as **Not Healthy**.")
