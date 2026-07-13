from app.db.engine import engine
def get_db():
    with engine.connect() as conn:
        yield conn