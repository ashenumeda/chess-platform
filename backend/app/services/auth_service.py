import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from asyncpg import Connection
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db

load_dotenv()  # Load environment variables from .env file

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")  # Should be set in .env
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Fallback to HS256 if not set

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a password hash."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create a new JWT token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        # Note: If algorithm isn't supplied, default securely to HS256
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[str]:
        """Decode the token and return the email (sub) if valid and not expired, else None."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            # Token completely valid but past its 'exp' date
            return None
        except jwt.JWTError:
            # Token invalid, tampered with, or corrupted
            return None

    @staticmethod
    async def get_user_by_email(db: Connection, email: str) -> Optional[dict]:
        """Fetch a user by their email address."""
        row = await db.fetchrow(
            "SELECT id, email, username, password_hash, rating FROM users WHERE email = $1", 
            email
        )
        return dict(row) if row else None

    @staticmethod
    async def create_user(db: Connection, email: str, username: str, password_hash: str) -> dict:
        """Create a new user and insert them into the database."""
        user_id = uuid.uuid4()
        await db.execute(
            """
            INSERT INTO users (id, email, username, password_hash, rating)
            VALUES ($1, $2, $3, $4, $5)
            """,
            user_id, email, username, password_hash, 1200
        )
        return {"id": user_id, "email": email, "username": username}

async def get_current_user(token: str = Depends(oauth2_scheme), conn: Connection = Depends(get_db)):
    """FastAPI Dependency: Get the current authenticated user from the token."""
    try:
        # We explicitly decode inline here to catch the specific expiration error if needed for custom responses, 
        # or we can rely on our `decode_token` helper which safely returns None. Let's use the helper.
        email = AuthService.decode_token(token)
        if not email:
            raise HTTPException(
                status_code=401, 
                detail="Could not validate credentials, token might be expired or invalid", 
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = await AuthService.get_user_by_email(conn, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user data: {str(e)}")
