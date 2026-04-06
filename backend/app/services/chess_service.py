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

                # If ofer a draw, clear it since a move has been made
                await db.execute(
                    "UPDATE games SET draw_offered_by = NULL WHERE id = $1",
                    game_id
                )

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
        
    @staticmethod
    async def resign_game(db: Connection, game_id: uuid.UUID, player_id: uuid.UUID) -> dict:
        """Allow a player to resign from an active game. Returns game result."""
        try:
            async with db.transaction():
                # 1. Get current game state
                game = await ChessService.get_game_state(db, game_id)
                if not game:
                    return {"success": False, "error": "Game not found"}
                if game["status"] != "active":
                    return {"success": False, "error": "Game is already finished"}
                
                # 2. Determine winner
                if player_id == game["white_player_id"]:
                    winner_id = game["black_player_id"]
                    result = "resignation - black wins"
                elif player_id == game["black_player_id"]:
                    winner_id = game["white_player_id"]
                    result = "resignation - white wins"
                else:
                    return {"success": False, "error": "You are not a player in this game"}

                # 3. Update game status
                await db.execute(
                    "UPDATE games SET status = $1, finished_at = CURRENT_TIMESTAMP, winner_id = $2 WHERE id = $3",
                    "resigned", winner_id, game_id
                )

                return {"success": True, "result": result, "winner_id": winner_id}
        except ValueError as ve:
            return {"success": False, "error": str(ve)}
        except Exception as e:
            return {"success": False, "error": f"Failed to process resignation: {str(e)}"}
        
    @staticmethod
    async def offer_draw(db: Connection, game_id: uuid.UUID, offering_player_id: uuid.UUID) -> dict:
        """Allow a player to offer a draw. Returns success or error."""
        try:
            async with db.transaction():
                # 1. Get current game state
                game = await ChessService.get_game_state(db, game_id)
                if not game:
                    return {"success": False, "error": "Game not found"}
                if game["status"] != "active":
                    return {"success": False, "error": "Game is already finished"}
                
                # 2. Check if offering player is part of the game
                if offering_player_id not in [game["white_player_id"], game["black_player_id"]]:
                    return {"success": False, "error": "You are not a player in this game"}
                
                # 3. Check if draw offer is already pending
                existing_offer = await db.fetchrow(
                    "SELECT draw_offered_by FROM games WHERE id = $1", game_id  
                )

                # The `fetchrow` above actually returns a Record if there is a game row. 
                # We need to explicitly check the value of `draw_offered_by` column.
                if existing_offer and existing_offer["draw_offered_by"] is not None:
                    return {"success": False, "error": "A draw offer is already pending"}
                
                # 4. Store the draw offer
                await db.execute(
                    "UPDATE games SET draw_offered_by = $1 WHERE id = $2",
                    offering_player_id, game_id
                )   

                return {"success": True, "message": "Draw offer made"}
        except ValueError as ve:
            return {"success": False, "error": str(ve)}
        except Exception as e:
            return {"success": False, "error": f"Failed to offer draw: {str(e)}"}

    @staticmethod
    async def respond_draw(db: Connection, game_id: uuid.UUID, responding_player_id: uuid.UUID, accept: bool) -> dict:
        """Allow a player to respond to a draw offer. Returns result."""
        try:
            async with db.transaction():
                # 1. Get current game state
                game = await ChessService.get_game_state(db, game_id)
                if not game:
                    return {"success": False, "error": "Game not found"}
                if game["status"] != "active":
                    return {"success": False, "error": "Game is already finished"}
                
                # 2. Check if responding player is part of the game
                if responding_player_id not in [game["white_player_id"], game["black_player_id"]]:
                    return {"success": False, "error": "You are not a player in this game"}
                
                # 3. Check if there is a pending draw offer
                existing_offer = await db.fetchrow(
                    "SELECT draw_offered_by FROM games WHERE id = $1", game_id  
                )
                if not existing_offer or existing_offer["draw_offered_by"] is None:
                    return {"success": False, "error": "No draw offer to respond to"}
                
                offering_player_id = existing_offer["draw_offered_by"]
                
                # 4. Validate that the responding player is not the one who offered the draw
                if responding_player_id == offering_player_id:
                    return {"success": False, "error": "You cannot respond to your own draw offer"}

                if accept:
                    # Update game status to draw
                    await db.execute(
                        """
                        UPDATE games SET status = $1, finished_at = CURRENT_TIMESTAMP,
                                        fen = $2, draw_offered_by = NULL
                        WHERE id = $3
                        """,
                        "draw", game["fen"], game_id
                    )
                    return {"success": True, "result": "Draw accepted"}
                else:
                    # Clear the draw offer
                    await db.execute(
                        "UPDATE games SET draw_offered_by = NULL WHERE id = $1",
                        game_id
                    )
                    return {"success": True, "result": "Draw declined"}
        except ValueError as ve:
            return {"success": False, "error": str(ve)}
        except Exception as e:
            return {"success": False, "error": f"Failed to respond to draw offer: {str(e)}"}
        