from __future__ import annotations

from fastapi import APIRouter
from core.fiftyone_manager import get_fiftyone_manager
from core.persistence import InMemoryKeyValueStore, get_sqlite_engine, Asistencia
from sqlalchemy import select, func

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def get_dashboard() -> dict:
    """
    Dashboard administrativo general: consolida las métricas del dataset
    de FiftyOne y estadísticas de la base de datos de asistencia SQLite.
    """
    fo_manager = get_fiftyone_manager()
    fo_summary = fo_manager.get_dataset_summary()

    # Consultar total de asistencias registradas en SQLite
    engine = get_sqlite_engine()
    async with engine.begin() as conn:
        query = select(func.count(Asistencia.estudiante_id))
        result = await conn.execute(query)
        total_asistencias = result.scalar() or 0

    return {
        "fiftyone": fo_summary,
        "database": {
            "total_asistencias_registradas": total_asistencias
        }
    }


@router.get("/alerts")
async def get_alerts() -> dict:
    """
    Retorna el listado de alertas de anomalías físicas generadas por
    los sensores de las aulas.
    """
    alerts = await InMemoryKeyValueStore.list_namespace("anomalias")
    return {
        "total_alertas": len(alerts),
        "alertas": alerts,
    }


@router.get("/spaces")
async def get_spaces() -> dict:
    """
    Retorna el historial de ocupación y recomendaciones de optimización de
    espacios físicos.
    """
    spaces_history = await InMemoryKeyValueStore.list_namespace("ocupacion_historica")
    return {
        "total_espacios_monitoreados": len(spaces_history),
        "historial_ocupacion": spaces_history,
    }
