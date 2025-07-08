from fastapi import APIRouter, HTTPException
from app.models import OnboardUser
from app.core.supabase_client import supabase
from datetime import datetime

router = APIRouter()

@router.post("/onboard")
def onboard_user(user: OnboardUser):
    try:
        data = user.dict()
        data['created_at'] = datetime.utcnow().isoformat()

        response = supabase.table("profiles").insert(data).execute()
        if response.error:
            raise HTTPException(status_code=500, detail=response.error.message)

        return {"status": "success", "message": "User onboarded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
