from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
import uuid
from app.core import database
from app.services.chess_service import ChessService
from app.services.auth_service import AuthService
from app.websocket.manager import manager

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/game/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    game_id: uuid.UUID,
    token: str = Query(...)
):
    await websocket.accept() # MUST accept the connection before doing custom close codes
    
    # Authenticate the user using the token
    try:
        email = AuthService.decode_token(token)
        if not email:
            await websocket.close(code=1008, reason="user not found")
            return
        
        # Use the global pool directly since Depends with yield sometimes fails in WebSocket routes
        async with database.pool.acquire() as db:
            user = await AuthService.get_user_by_email(db, email)
            if not user:
                await websocket.close(code=1008, reason="user not found") 
                return
            
            # Check if game is valid and the user is a player in the game
            game = await ChessService.get_game_state(db, game_id)
            if not game:
                await websocket.close(code=1008, reason="game not found") 
                return  
            if user["id"] not in [game["white_player_id"], game["black_player_id"]]:
                await websocket.close(code=1008, reason="not a player in this game") 
                return  
    except JWTError:
        await websocket.close(code=1008, reason="invalid token") 
        return
    except Exception as e:
        await websocket.close(code=1011, reason="internal error") 
        print(f"WebSocket auth error: {e}")
        return  
    
    await manager.connect(game_id, websocket)

    try:
        # Send the initial game state to the client upon connection
        await websocket.send_json({
            "type": "game_state",
            "fen": game["fen"],
            "status": game["status"],
            "white_player_id": str(game["white_player_id"]),
            "black_player_id": str(game["black_player_id"]),
        })

        # Keep the connection open to listen for moves or other messages from the client
        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
    except Exception as e:
        manager.disconnect(game_id, websocket)
        print(f"WebSocket error: {e}")  
