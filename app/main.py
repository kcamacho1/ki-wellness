from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import auth, frontend, food_journal, early_access, ai_coach, spiritual, exercise, meals
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Basic Routers
app.include_router(auth.router)
app.include_router(frontend.router)
app.include_router(early_access.router)

# AI Health Coach Routers
app.include_router(ai_coach.router)
app.include_router(spiritual.router)
app.include_router(exercise.router)
app.include_router(meals.router)
app.include_router(food_journal.router)



