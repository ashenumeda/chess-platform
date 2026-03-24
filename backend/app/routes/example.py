from fastapi import APIRouter
import chess

router = APIRouter(prefix="/chess", tags=["chess"])

@router.get("/board")
def get_initial_board():
    board = chess.Board()
    return {"fen": board.fen()}
