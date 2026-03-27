from fastapi import FastAPI
from app.routes import games, auth  # import the games router

app = FastAPI(title="Chess Platform API")

# Include routers
app.include_router(games.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Chess Platform API"}