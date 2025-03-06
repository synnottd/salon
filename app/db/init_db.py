from sqlalchemy.orm import Session
from app.db.session import Base, engine
import app.models  # This imports all models

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    init_db() 