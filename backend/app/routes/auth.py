from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta
from app.core.database import get_db
from dotenv import load_dotenv
import os   

load_dotenv()  # Load environment variables from .env file

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")  # Should be set in .env
ALGORITHM = os.getenv("ALGORITHM")  # Should be set in .env

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
async def register(email: str, username: str, password: str, conn=Depends(get_db)):
    try:
        # Check if user exists
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user_id = uuid.uuid4()
        hashed = get_password_hash(password)
        await conn.execute(
            """
            INSERT INTO users (id, email, username, password_hash, rating)
            VALUES ($1, $2, $3, $4, $5)
            """,
            user_id, email, username, hashed, 1200
        )
        return {"id": user_id, "email": email, "username": username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn=Depends(get_db)):
    try:
        # Note: OAuth2PasswordRequestForm uses "username" field for email
        user = await conn.fetchrow(
            "SELECT id, email, username, password_hash FROM users WHERE email = $1",
            form_data.username
        )
        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        access_token = create_access_token({"sub": user["email"]})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me")
async def read_users_me(token: str = Depends(oauth2_scheme), conn=Depends(get_db)):
    # Decode token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user = await conn.fetchrow("SELECT id, email, username, rating FROM users WHERE email = $1", email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user data: {str(e)}")