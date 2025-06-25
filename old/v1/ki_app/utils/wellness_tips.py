# utils/wellness_tips.py
import random

def get_random_tip():
    tips = [
        "Drink water before your meals to boost digestion.",
        "Take a few deep breaths—your nervous system needs it.",
        "Add leafy greens to at least one meal a day.",
        "Move your body gently even on rest days.",
        "Mindfulness meditation improves your focus and mood."
    ]
    return random.choice(tips)
