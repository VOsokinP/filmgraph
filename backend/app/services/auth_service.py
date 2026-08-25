from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password

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

def create_customer(
    conn: Connection, *, email: str, password: str, first_name: str, last_name: str
) -> dict | None:
    """Insert a customer. Returns None if the email is already registered.

    Relies on the unique index rather than checking first, so two simultaneous registrations
    cannot both pass a check and then both insert.
    """
    try:
        result = conn.execute(
            text(
                "INSERT INTO customers (firstName, lastName, email, passwordHash) "
                "VALUES (:first_name, :last_name, :email, :password_hash)"
            ),
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password_hash": hash_password(password),
            },
        )
    except IntegrityError:
        conn.rollback()
        return None

    conn.commit()
    return {
        "id": result.lastrowid,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
    }


def get_customer_by_id(conn: Connection, customer_id: int) -> dict | None:
    row = conn.execute(
        text("SELECT id, firstName, lastName, email FROM customers WHERE id = :id"),
        {"id": customer_id},
    ).mappings().first()
    return dict(row) if row else None