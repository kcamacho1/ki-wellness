from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from app.core.supabase_client import supabase
from postgrest.exceptions import APIError
from fastapi import Query



router = APIRouter()


@router.post("/early-access")
async def early_access_signup(request: Request, email: str = Form(...)):
    try:
        response = supabase.table("early_access_emails").insert({
            "email": email,
            "unsubscribed": False
        }).execute()
    except APIError as e:
        if e.code == "23505":
            url = str(request.url_for("homepage")) + f"?message=You are already signed up!&email={email}"
            return RedirectResponse(url=url, status_code=303)
        else:
            url = str(request.url_for("homepage")) + "?message=Something went wrong, Please try again."
            return RedirectResponse(url=url, status_code=303)
    
    url = str(request.url_for("homepage")) + f"?message=Thank you for signing up! We will email you when we launch.&email={email}"
    return RedirectResponse(url=url, status_code=303)

@router.get("/unsubscribe")
async def unsubscribe(request: Request, email: str = Query(...)):
    response = supabase.table("early_access_emails").update({
        "unsubscribed": True
    }).eq("email", email).execute()

    url = str(request.url_for("homepage")) + "?message=You have been unsubscribed."
    return RedirectResponse(url=url, status_code=303)