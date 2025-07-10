# app/utils/ai.py
async def generate_ai_coach_tips(user_data: dict) -> list:
    # TODO: Replace with OpenAI/OpenRouter call
    goals = user_data.get("goals", "fitness and energy")
    mood = user_data.get("mood", "okay")
    return [
        f"Based on your goal to improve {goals}, stay hydrated today.",
        f"Try 5 mins of breathwork if you're feeling {mood.lower()}.",
        "Log your meals to get a tailored meal suggestion tomorrow."
    ]
