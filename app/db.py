# python
"""
Модуль `app.db` — настройка подключения к базе данных и фабрика сессий.

Содержит:
- `Base` — базовый класс для ORM‑моделей (наследуется всеми моделями SQLAlchemy);
- `engine` — SQLAlchemy Engine, создаваемый по `settings.database_url`;
- `SessionLocal` — фабрика сессий для получения объектов `Session`;
- `get_db` — генератор для получения сессии и её безопасного закрытия (удобен как
  dependency в FastAPI).
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    """
    Базовый класс для декларативных ORM-моделей.

    Наследовать этот класс при объявлении моделей, чтобы SQLAlchemy корректно
    регистрировал таблицы в `Base.metadata`.
    """
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """
    Генератор, выдающий экземпляр `Session` и обеспечивающий его закрытие.

    Используется как dependency в FastAPI:
    ```python
    def endpoint(db: Session = Depends(get_db)):
        ...
    ```

    Returns:
        Generator[Session, None, None]: объект сессии SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()