from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

CART_SESSION_KEY = "cart"

def add_item(session: dict, movie_id: str, delta: int) -> None:
    cart = session.get(CART_SESSION_KEY, {})
    new_quantity = cart.get(movie_id, 0) + delta
    if new_quantity <= 0:
        cart.pop(movie_id, None)
    else:
        cart[movie_id] = new_quantity
    session[CART_SESSION_KEY] = cart

def remove_item(session: dict, movie_id: str) -> None:
    cart = session.get(CART_SESSION_KEY, {})
    cart.pop(movie_id, None)
    session[CART_SESSION_KEY] = cart

def clear_cart(session: dict) -> None:
    session[CART_SESSION_KEY] = {}

def resolve_cart(conn: Connection, session: dict) -> dict:
    cart: dict[str, int] = session.get(CART_SESSION_KEY, {})
    if not cart:
        return {"items": [], "total": 0.0}

    rows = conn.execute(
        text("SELECT id, title, price FROM movies WHERE id IN :ids")
        .bindparams(bindparam("ids", expanding=True)),
        {"ids": list(cart.keys())},
    ).mappings().all()
    
    items = []
    total = 0.0
    for row in rows:
        quantity = cart[row["id"]]
        subtotal = round(float(row["price"]) * quantity, 2)
        total += subtotal
        items.append({
            "movie_id": row["id"],
            "title": row["title"],
            "price": float(row["price"]),
            "quantity": quantity,
            "subtotal": subtotal,
        })
    return {"items": items, "total": round(total, 2)}