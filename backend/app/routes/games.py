from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.chess_service import ChessService

router = APIRouter(prefix="/games", tags=["games"])

# Instantiate the service (you could also use dependency injection)
chess_service = ChessService()

class MoveRequest(BaseModel):
    move: str  # UCI format, e.g., "e2e4"

@router.post("/")
def create_game():
    """Create a new chess game."""
    game_id = chess_service.create_game()
    return {"game_id": game_id}

@router.get("/{game_id}")
def get_game(game_id: str):
    """Get the current state of a game."""
    board = chess_service.get_board(game_id)
    if not board:
        raise HTTPException(status_code=404, detail="Game not found")
    return {
        "game_id": game_id,
        "fen": board.fen(),
        "turn": "white" if board.turn else "black", # board.turn returns True for "white" and False for "Black"
        "is_game_over": board.is_game_over(),
        "legal_moves": [move.uci() for move in board.legal_moves]  # optional
    }

@router.post("/{game_id}/move")
def make_move(game_id: str, request: MoveRequest):
    """Make a move on the given game."""
    result = chess_service.make_move(game_id, request.move)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result