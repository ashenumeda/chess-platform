import chess
from typing import Optional

class ChessService:
    def __init__(self):
        # We'll manage games in memory for now
        self.games = {}  # game_id -> chess.Board()

    def create_game(self) -> str:
        """Create a new game and return its ID."""
        board = chess.Board()
        game_id = str(len(self.games) + 1)  # simple increment (replace with UUID later)
        self.games[game_id] = board
        return game_id

    def get_board(self, game_id: str) -> Optional[chess.Board]:
        """Retrieve the board for a given game ID."""
        return self.games.get(game_id)

    def make_move(self, game_id: str, move_uci: str) -> dict:
        """
        Apply a move in UCI format (e.g., "e2e4") to the game.
        Returns a dict with success flag, new FEN, and game over status.
        """
        board = self.games.get(game_id)
        if not board:
            return {"success": False, "error": "Game not found"}

        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            return {"success": False, "error": "Illegal move"}

        board.push(move)

        # Check if game is over
        result = {
            "success": True,
            "fen": board.fen(),
            "is_game_over": board.is_game_over(),
        }
        if board.is_game_over():
            result["result"] = self._get_game_result(board)

        return result

    def _get_game_result(self, board: chess.Board) -> str:
        """Return the game result as a string."""
        if board.is_checkmate():
            winner = "white" if board.turn == chess.BLACK else "black"  # because turn of the side that just moved
            return f"checkmate - {winner} wins"
        elif board.is_stalemate():
            return "stalemate"
        elif board.is_insufficient_material():
            return "insufficient material"
        else:
            return "draw"