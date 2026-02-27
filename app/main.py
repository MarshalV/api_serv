import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import engine
from app.models import Base
from app.routers import departments as departments_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы если их ещё нет (fallback на случай сбоя alembic)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")
    yield

# Создание приложения
app = FastAPI(
    title="D&E API",
    description="API управления организационной структурой (подразделения и сотрудники)",
    version="1.0.0",
    lifespan=lifespan,
)

# Подключение маршрутов
app.include_router(departments_router.router)
