from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.services.auth_service import AuthService, get_current_user
from asyncpg import Connection

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(email: str, username: str, password: str, conn: Connection = Depends(get_db)):
    try:
        # Check if user exists using service layer
        existing = await AuthService.get_user_by_email(conn, email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed = AuthService.get_password_hash(password)
        user_info = await AuthService.create_user(conn, email, username, hashed)
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn: Connection = Depends(get_db)):
    try:
        # Note: OAuth2PasswordRequestForm uses "username" field for email
        user = await AuthService.get_user_by_email(conn, form_data.username)
        
        if not user or not AuthService.verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        access_token = AuthService.create_access_token({"sub": user["email"]})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Remove the sensitive password hash before returning the profile
    safe_user_profile = {k: v for k, v in current_user.items() if k != "password_hash"}
    return safe_user_profile