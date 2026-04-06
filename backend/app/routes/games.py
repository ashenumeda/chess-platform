from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
import chess
from asyncpg import Connection

from app.services.chess_service import ChessService
from app.core.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/games", tags=["games"])

class CreateGameRequest(BaseModel):
    # Only need to provide the opponent (black player in this test case)
    black_player_id: uuid.UUID

class MoveRequest(BaseModel):
    # We will also pull the player_id implicitly from the current user below instead of the request body
    move: str  # UCI format, e.g., "e2e4"

class DrawResponseRequest(BaseModel):
    accept: bool  # True to accept the draw, False to decline

@router.post("/")
async def create_game(
    request: CreateGameRequest, 
    db: Connection = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Create a new chess game with the current user as White."""
    try:
        # User auth forces current_user["id"] as the white player
        white_player_id = current_user["id"]
        game_info = await ChessService.create_game(db, white_player_id, request.black_player_id)
        return game_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{game_id}")
async def get_game(game_id: uuid.UUID, db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get the current state of a game."""
    try:
        game_state = await ChessService.get_game_state(db, game_id)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
        
    board = chess.Board(game_state["fen"])
    return {
        "game_id": game_id,
        "fen": game_state["fen"],
        "status": game_state["status"],
        "white_player_id": game_state["white_player_id"],
        "black_player_id": game_state["black_player_id"],
        "turn": "white" if board.turn else "black", # board.turn returns True for "white" and False for "black"
        "is_game_over": board.is_game_over(),
        "legal_moves": [move.uci() for move in board.legal_moves]
    }

@router.post("/{game_id}/move")
async def make_move(
    game_id: uuid.UUID, 
    request: MoveRequest, 
    db: Connection = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Make a move on the given game. Must be authenticated."""
    player_id = current_user["id"]
    result = await ChessService.make_move(db, game_id, player_id, request.move)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result

@router.post("/{game_id}/resign")
async def resign_game(
    game_id: uuid.UUID, 
    db: Connection = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Resign from the game. Must be authenticated."""
    player_id = current_user["id"]
    result = await ChessService.resign_game(db, game_id, player_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result

@router.post("/{game_id}/offer_draw")
async def offer_draw(
    game_id: uuid.UUID, 
    db: Connection = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Offer a draw in the game. Must be authenticated."""
    player_id = current_user["id"]
    result = await ChessService.offer_draw(db, game_id, player_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result

@router.post("/{game_id}/respond_draw")
async def respond_draw(
    game_id: uuid.UUID, 
    request: DrawResponseRequest, 
    db: Connection = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Respond to a draw offer in the game. Must be authenticated."""
    player_id = current_user["id"]
    result = await ChessService.respond_draw(db, game_id, player_id, request.accept)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result