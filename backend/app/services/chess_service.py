import chess
import uuid
from typing import Optional
from asyncpg import Connection

class ChessService:
    @staticmethod
    async def create_game(db: Connection, white_player_id: uuid.UUID, black_player_id: uuid.UUID) -> dict:
        """Create a new game, store initial board in games table, return game info."""
        game_id = uuid.uuid4()
        initial_fen = chess.Board().fen()
        
        try:
            await db.execute(
                """ 
                INSERT INTO games (id, white_player_id, black_player_id, status, fen)
                VALUES ($1, $2, $3, $4, $5)
                """,
                game_id, white_player_id, black_player_id, "active", initial_fen
            )
        except Exception as e:
            raise ValueError(f"Failed to create game: {str(e)}")

        return {
            "game_id": game_id,
            "fen": initial_fen,
            "status": "active"
        }

    @staticmethod
    async def get_game_state(db: Connection, game_id: uuid.UUID) -> Optional[dict]:
        """Retrieve current game state (fen, status, players)."""
        try:
            row = await db.fetchrow(
                "SELECT fen, status, white_player_id, black_player_id FROM games WHERE id = $1",
                game_id
            )
            if not row:
                return None
            return dict(row)
        except Exception as e:
            raise ValueError(f"Failed to retrieve game state: {str(e)}")

    @staticmethod
    async def make_move(db: Connection, game_id: uuid.UUID, player_id: uuid.UUID, move_uci: str) -> dict:
        """
        Apply a move to the game.
        Returns dict with success flag, new FEN, game over status, etc.
        """
        try:
            # Start a transaction to ensure consistency
            async with db.transaction():
                # 1. Get current game state
                game = await ChessService.get_game_state(db, game_id)
                if not game:
                    return {"success": False, "error": "Game not found"}
                if game["status"] != "active":
                    return {"success": False, "error": "Game is already finished"}

                # 2. Reconstruct board from FEN
                board = chess.Board(game["fen"])

                # 3. Validate and apply move
                try:
                    move = chess.Move.from_uci(move_uci)
                except ValueError:
                    return {"success": False, "error": "Invalid move format"}

                if move not in board.legal_moves:
                    return {"success": False, "error": "Illegal move"}
                
                # Check if it's the correct player's turn
                if (board.turn == chess.WHITE and player_id != game["white_player_id"]) or \
                   (board.turn == chess.BLACK and player_id != game["black_player_id"]):
                    return {"success": False, "error": "Not your turn"}

                # 4. Determine move number (current ply count + 1)
                move_number = board.fullmove_number
                board.push(move)

                # 5. Prepare result
                result = {
                    "success": True,
                    "fen": board.fen(),
                    "is_game_over": board.is_game_over(),
                    "move_number": move_number
                }

                # 6. Update game status and fen in database
                new_status = "active"
                if board.is_game_over():
                    if board.is_checkmate():
                        # winner is the player who made the last move (opposite of board.turn)
                        winner = "white" if board.turn == chess.BLACK else "black"
                        new_status = "completed"
                        result["result"] = f"checkmate - {winner} wins"
                        # Determine winner_id from player who moved
                        winner_id = player_id  # because the player who just moved caused checkmate
                        await db.execute(
                            """
                            UPDATE games SET status = $1, finished_at = CURRENT_TIMESTAMP,
                                            winner_id = $2, fen = $3
                            WHERE id = $4
                            """,
                            new_status, winner_id, board.fen(), game_id
                        )
                    else:
                        # draw conditions
                        new_status = "draw"
                        result["result"] = ChessService._get_game_result(board)
                        await db.execute(
                            """
                            UPDATE games SET status = $1, finished_at = CURRENT_TIMESTAMP,
                                            fen = $2
                            WHERE id = $3
                            """,
                            new_status, board.fen(), game_id
                        )
                else:
                    # just update fen
                    await db.execute(
                        "UPDATE games SET fen = $1 WHERE id = $2",
                        board.fen(), game_id
                    )

                # 7. Insert move record (always, even if game ended)
                await db.execute(
                    """
                    INSERT INTO moves (id, game_id, player_id, move_number, from_square, to_square, piece)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    uuid.uuid4(), game_id, player_id, move_number,
                    chess.square_name(move.from_square), chess.square_name(move.to_square), 
                    chess.piece_name(board.piece_at(move.to_square).piece_type)
                    # Note: piece type might need mapping; you could store as string.
                )

                return result
        except ValueError as ve:
            return {"success": False, "error": str(ve)}
        except Exception as e:
            return {"success": False, "error": f"Failed to process move: {str(e)}"}

    @staticmethod
    def _get_game_result(board: chess.Board) -> str:
        """Return human-readable game result."""
        if board.is_stalemate():
            return "stalemate"
        elif board.is_insufficient_material():
            return "insufficient material"
        elif board.is_seventyfive_moves():
            return "75-move rule"
        elif board.is_fivefold_repetition():
            return "fivefold repetition"
        else:
            return "draw"