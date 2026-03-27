from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import uuid

SECRET_KEY = "secret-key-here"  # move to .env 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In‑memory user store (replace with DB later)
fake_users_db = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str):
    user = fake_users_db.get(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_user(user_data):
    email = user_data.email
    if email in fake_users_db:
        return None
    user_id = str(uuid.uuid4())
    fake_users_db[email] = {
        "id": user_id,
        "email": email,
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
        "rating": 1200
    }
    return fake_users_db[email]