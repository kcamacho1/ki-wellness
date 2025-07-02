from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY
from fastapi.templating import Jinja2Templates
import httpx

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def login_user(email: str, password: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        return resp.json()


async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        if resp.status_code != 200:
            return None
        return resp.json()


# Auth routes
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    auth_data = await login_user(email, password)
    access_token = auth_data["access_token"]

    response = RedirectResponse("/food-journal", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False,
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.post("/forgot-password")
async def handle_forgot_password(email: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/auth/v1/recover",
            json={"email": email},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
        )

    if resp.status_code != 200:
        print(f"Error from Supabase: {resp.text}")

    return RedirectResponse("/login", status_code=302)
