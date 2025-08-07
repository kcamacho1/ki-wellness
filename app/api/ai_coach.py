# app/api/coach.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase_client import get_user_profile
from app.utils.ai import generate_ai_coach_tips
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from openai import OpenAI
import markdown



client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class ChatRequest(BaseModel):
    message: str
    user_profile: dict = None  # Optional profile for personalization

@router.post("/ai-coach")
async def ai_coach(request: ChatRequest):
    try:
        # Build personalization context
        profile_text = ""
        if request.user_profile:
            profile_text = (
                f"Name: {request.user_profile.get('name', '')}\n"
                f"Goals: {request.user_profile.get('goals', '')}\n"
                f"Ailments: {request.user_profile.get('ailments', '')}\n"
                f"Dietary Preferences: {request.user_profile.get('diet', '')}\n"
            )

        # SYSTEM PROMPT: Tone, style, structure
        system_prompt = f"""
        You are a warm, motivational, and knowledgeable AI wellness coach for Ki Wellness.
        Always be empathetic, encouraging, and uplifting.
        Personalize your guidance based on the provided profile.

        Structure your answer in this format:
        ## Quick Summary
        (One or two warm sentences summarizing your advice.)

        ## Action Steps
        - Step 1
        - Step 2
        - Step 3

        ## Encouragement
        (One short motivating statement.)

        Keep answers concise but impactful.
        Use friendly, supportive language.
        If a profile is provided, reflect their personal goals and needs.

        USER PROFILE (if any):
        {profile_text}
        """

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper, faster
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            max_tokens=350
        )

        # Convert Markdown to HTML
        raw_text = response.choices[0].message.content.strip()
        html_output = markdown.markdown(raw_text)

        return {"response": html_output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-coach", response_class=HTMLResponse)
async def ai_coach_dashboard(request: Request):
    try:
        user_id = request.session.get("user_id") or "dev-id"  # fallback for dev
        print("Using user_id:", user_id)

        user_data = get_user_profile(user_id)
        print("Fetched user_data:", user_data)

        tips = await generate_ai_coach_tips(user_data)
        print("Generated tips:", tips)

        return templates.TemplateResponse("ai-coach.html", {
            "request": request,
            "summary": user_data,
            "tips": tips
        })

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

