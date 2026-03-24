from pydantic import BaseModel

class GameStatus(BaseModel):
    status: str
