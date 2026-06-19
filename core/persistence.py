import asyncio
from typing import Any, Optional
from sqlalchemy import Column, String, Date, Time, Integer, DateTime, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

Base = declarative_base()

class Asistencia(Base):
    __tablename__ = "asistencias"

    estudiante_id = Column(String, primary_key=True)
    fecha = Column(Date, primary_key=True)  # YYYY-MM-DD
    hora_registro = Column(Time, nullable=False)  # HH:MM:SS
    aula_id = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("estudiante_id", "fecha", name="uq_estudiante_fecha"),
    )

class AsyncConnectionAdapter:
    def __init__(self, conn: Any) -> None:
        self._conn = conn

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._conn.execute(*args, **kwargs)

    async def run_sync(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(self._conn, *args, **kwargs)


class AsyncBeginContext:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._context: Any = None

    async def __aenter__(self) -> AsyncConnectionAdapter:
        self._context = self._engine.begin()
        conn = self._context.__enter__()
        return AsyncConnectionAdapter(conn)

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return self._context.__exit__(exc_type, exc, tb)


class AsyncEngineAdapter:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def begin(self) -> AsyncBeginContext:
        return AsyncBeginContext(self._engine)


_sqlite_engine: Optional[AsyncEngineAdapter] = None
_in_memory_store: dict[str, dict[str, Any]] = {}
_in_memory_lock = asyncio.Lock()

def get_sqlite_engine() -> AsyncEngineAdapter:
    global _sqlite_engine
    if _sqlite_engine is None:
        sync_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _sqlite_engine = AsyncEngineAdapter(sync_engine)
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
