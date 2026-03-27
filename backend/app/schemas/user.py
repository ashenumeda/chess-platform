from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    rating: int = 1200

class Token(BaseModel):
    access_token: str
    token_type: str