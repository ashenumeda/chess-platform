import asyncio
import asyncpg
from app.core.database import DB_CONFIG

async def create_tables():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) NOT NULL,
            password_hash TEXT,
            oauth_provider VARCHAR(50),
            oauth_id VARCHAR(255),
            rating INTEGER DEFAULT 1200 CHECK (rating >= 0),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            white_player_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            black_player_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            winner_id UUID REFERENCES users(id),
            status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed', 'resigned', 'draw')),
            fen TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMPTZ
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
            player_id UUID NOT NULL REFERENCES users(id),
            move_number INTEGER NOT NULL CHECK (move_number > 0),
            from_square VARCHAR(2) NOT NULL,
            to_square VARCHAR(2) NOT NULL,
            piece VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            invited_user UUID REFERENCES users(id),
            invite_token VARCHAR(255) UNIQUE NOT NULL,
            status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'accepted', 'expired')),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ
        )
    """)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())