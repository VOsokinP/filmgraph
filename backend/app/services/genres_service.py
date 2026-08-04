from sqlalchemy import text
from sqlalchemy.engine import Connection

def list_genres(conn: Connection) -> list[dict]:
    rows = conn.execute(text("SELECT id, name FROM genres ORDER BY name")).mappings().all()
    return [dict(row) for row in rows]