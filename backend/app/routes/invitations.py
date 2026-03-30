# app/routes/invitations.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from asyncpg import Connection
from app.core.database import get_db
from app.services.auth_service import get_current_user
from app.services.chess_service import ChessService

router = APIRouter(prefix="/invitations", tags=["invitations"])

class CreateInvitationRequest(BaseModel):
    invited_email: str | None = None  # optional, can be used to invite by email

@router.post("/")
async def create_invitation(
    data: CreateInvitationRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new invitation link."""
    try:
        token = secrets.token_urlsafe(32)  # generate random token
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days validity
        await db.execute(
            """
            INSERT INTO invitations (id, created_by, invite_token, status, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.uuid4(), current_user["id"], token, "pending", expires_at
        )
        # Return the invitation link (frontend will use it)
        return {"invite_token": token, "expires_at": expires_at}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create invitation: {str(e)}")

@router.post("/{token}/accept")
async def accept_invitation(
    token: str,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Accept an invitation, create a game, and mark invitation accepted."""
    try:
        # Check invitation exists and is pending
        inv = await db.fetchrow(
            "SELECT id, created_by, expires_at, status FROM invitations WHERE invite_token = $1",
            token
        )
        if not inv:
            raise HTTPException(status_code=404, detail="Invitation not found")
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail="Invitation already used or expired")
        
        # Make the current datetime aware (UTC) to match PostgreSQL's datetime (which is usually timezone-aware)
        now_utc = datetime.now(timezone.utc)
        
        # If the db datetime is offset-naive, we forcefully add the UTC timezone to it for the comparison to work
        expires_at = inv["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now_utc:
            # Mark as expired
            await db.execute("UPDATE invitations SET status = 'expired' WHERE id = $1", inv["id"])
            raise HTTPException(status_code=400, detail="Invitation expired")

        # Create game: creator is white, acceptor is black (or vice versa - we choose)
        creator_id = inv["created_by"]
        acceptor_id = current_user["id"]
        if creator_id == acceptor_id:
            raise HTTPException(status_code=400, detail="You cannot accept your own invitation")

        # Create game
        try:
            game = await ChessService.create_game(db, white_player_id=creator_id, black_player_id=acceptor_id)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        # Update invitation status
        await db.execute(
            "UPDATE invitations SET status = 'accepted', invited_user = $1 WHERE id = $2",
            acceptor_id, inv["id"]
        )

        return {
            "message": "Invitation accepted, game created",
            "game_id": game["game_id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process invitation: {str(e)}")