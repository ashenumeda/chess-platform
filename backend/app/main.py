from fastapi import FastAPI
from app.routes import example

app = FastAPI(title="Chess Platform API")

# Include routers
app.include_router(example.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Chess Platform API"}
