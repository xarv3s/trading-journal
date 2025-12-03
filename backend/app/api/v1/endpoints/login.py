from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.services.kite_service import KiteClient
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/")
def login():
    """
    Redirects the user to Zerodha's login page.
    """
    kite = KiteClient(api_key=settings.KITE_API_KEY)
    login_url = kite.get_login_url()
    return RedirectResponse(login_url)

@router.get("/callback")
def login_callback(request_token: str, status: str = None):
    """
    Handles the callback from Zerodha.
    Exchanges request_token for access_token and saves it.
    """
    if status != 'success':
        raise HTTPException(status_code=400, detail="Login failed or denied by user")
        
    kite = KiteClient(api_key=settings.KITE_API_KEY)
    try:
        data = kite.kite.generate_session(request_token, api_secret=settings.KITE_API_SECRET)
        kite.kite.set_access_token(data["access_token"])
        kite.save_access_token(data["access_token"])
        
        # Redirect back to frontend
        return RedirectResponse("http://localhost:3000/?login=success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating session: {str(e)}")

@router.get("/status")
def check_login_status():
    """
    Checks if the current session is valid.
    """
    kite = KiteClient(api_key=settings.KITE_API_KEY)
    # Load token from file
    token = KiteClient.load_access_token()
    if token:
        kite.kite.set_access_token(token)
        if kite.validate_token():
            return {"status": "connected"}
    return {"status": "disconnected"}
