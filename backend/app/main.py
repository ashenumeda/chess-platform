from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db, close_db
from app.routes import games, auth, invitations, ws  # import the games router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # Initialize the database connection pool
    yield
    await close_db()  # Close the database connection pool on shutdown

app = FastAPI(title="Chess Platform API", lifespan=lifespan)

# Include routers
app.include_router(games.router)
app.include_router(auth.router)
app.include_router(invitations.router)
app.include_router(ws.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Chess Platform API"}