from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.security import DUMMY_PASSWORD_HASH, verify_password

def authenticate_customer(conn: Connection, email: str, password: str) -> dict | None:
    row = conn.execute(
        text("SELECT id, firstName, lastName, email, passwordHash FROM customers WHERE email = :email"),
        {"email": email},
    ).mappings().first()
    if row is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    if not verify_password(password, row["passwordHash"]):
        return None
    return {"id": row["id"], "firstName": row["firstName"], "lastName": row["lastName"], "email": row["email"]}

def get_customer_by_id(conn: Connection, customer_id: int) -> dict | None:
    row = conn.execute(
        text("SELECT id, firstName, lastName, email FROM customers WHERE id = :id"),
        {"id": customer_id},
    ).mappings().first()
    return dict(row) if row else None