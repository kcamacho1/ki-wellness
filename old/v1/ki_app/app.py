# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.wellness_tips import get_random_tip
import os

st.set_page_config(page_title="Ki Wellness", layout="wide")

# Sidebar
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
st.sidebar.image(logo_path, width=150)
page = st.sidebar.selectbox("Navigate", ["🏠 Dashboard", "🍽️ Meals", "🧘 Mood Tracker", "💡 Wellness Tip"])

# Dummy data
if "meals" not in st.session_state:
    st.session_state.meals = []

if "moods" not in st.session_state:
    st.session_state.moods = []

# Dashboard
if page == "🏠 Dashboard":
    st.title("Welcome to Ki Wellness 🌿")
    st.subheader("Your Mind, Body, Spirit Companion")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Meals Logged Today", len(st.session_state.meals))

    with col2:
        st.metric("Mood Logs Today", len(st.session_state.moods))

# Meals
elif page == "🍽️ Meals":
    st.header("Meal Logger")
    meal = st.text_input("What did you eat?")
    if st.button("Log Meal"):
        st.session_state.meals.append({"meal": meal, "time": datetime.now()})
        st.success("Meal logged!")

    if st.session_state.meals:
        df = pd.DataFrame(st.session_state.meals)
        st.dataframe(df)

# Mood Tracker
elif page == "🧘 Mood Tracker":
    st.header("Mood Tracker")
    mood = st.selectbox("How are you feeling?", ["Happy", "Sad", "Neutral", "Anxious", "Excited"])
    if st.button("Log Mood"):
        st.session_state.moods.append({"mood": mood, "time": datetime.now()})
        st.success("Mood logged!")

    if st.session_state.moods:
        df = pd.DataFrame(st.session_state.moods)
        st.dataframe(df)

# Wellness Tip
elif page == "💡 Wellness Tip":
    st.header("Wellness Tip of the Moment 🌟")
    tip = get_random_tip()
    st.info(tip)
