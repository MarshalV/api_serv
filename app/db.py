import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:testadmin@localhost:5433/main_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Генератор сессии базы данных.
    Открывает сессию перед запросом и закрывает после.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
