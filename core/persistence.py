import asyncio
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, UniqueConstraint

Base = declarative_base()

class Asistencia(Base):
    __tablename__ = "asistencias"

    estudiante_id = Column(String, primary_key=True)
    fecha = Column(String, primary_key=True)  # YYYY-MM-DD
    hora_registro = Column(String, nullable=False)  # HH:MM:SS
    aula_id = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("estudiante_id", "fecha", name="uq_estudiante_fecha"),
    )

_sqlite_engine: Optional[AsyncEngine] = None
_in_memory_store: dict[str, dict[str, Any]] = {}
_in_memory_lock = asyncio.Lock()

def get_sqlite_engine() -> AsyncEngine:
    global _sqlite_engine
    if _sqlite_engine is None:
        _sqlite_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            pool_pre_ping=False,
            connect_args={"check_same_thread": False},
        )
    return _sqlite_engine

async def init_db() -> None:
    engine = get_sqlite_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class InMemoryKeyValueStore:
    @staticmethod
    async def get(namespace: str, key: str) -> Optional[dict[str, Any]]:
        async with _in_memory_lock:
            return _in_memory_store.get(f"{namespace}:{key}")

    @staticmethod
    async def set(namespace: str, key: str, value: dict[str, Any]) -> None:
        async with _in_memory_lock:
            _in_memory_store[f"{namespace}:{key}"] = value

    @staticmethod
    async def list_namespace(namespace: str) -> list[dict[str, Any]]:
        async with _in_memory_lock:
            prefix = f"{namespace}:"
            return [v for k, v in _in_memory_store.items() if k.startswith(prefix)]
