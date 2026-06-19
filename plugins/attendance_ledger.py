from __future__ import annotations

from datetime import datetime
from typing import Any
from sqlalchemy import insert, select
from core.persistence import get_sqlite_engine, Asistencia
from plugins.base import BasePlugin

class AttendanceLedgerPlugin(BasePlugin):
    name = "attendance_ledger"

    async def execute(self, *, estudiante_id: str, aula_id: str, estado_visual: str) -> dict[str, Any]:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        hora_hoy = datetime.now().strftime("%H:%M:%S")

        if estado_visual == "ausente":
            return {
                "registrado": False,
                "estudiante_id": estudiante_id,
                "fecha": fecha_hoy,
                "ya_existia": False,
                "mensaje": "Estudiante ausente, no se registra asistencia"
            }

        engine = get_sqlite_engine()

        async with engine.begin() as conn:
            # Check if attendance already exists
            query = select(Asistencia).where(
                Asistencia.estudiante_id == estudiante_id,
                Asistencia.fecha == fecha_hoy
            )
            result = await conn.execute(query)
            existing = result.fetchone()

            if existing is not None:
                return {
                    "registrado": True,
                    "estudiante_id": estudiante_id,
                    "fecha": fecha_hoy,
                    "ya_existia": True,
                    "mensaje": "La asistencia ya estaba registrada para hoy"
                }

            # Insert new attendance record (idempotent via INSERT OR IGNORE)
            stmt = insert(Asistencia).values(
                estudiante_id=estudiante_id,
                fecha=fecha_hoy,
                hora_registro=hora_hoy,
                aula_id=aula_id
            ).prefix_with("OR IGNORE")
            await conn.execute(stmt)

        return {
            "registrado": True,
            "estudiante_id": estudiante_id,
            "fecha": fecha_hoy,
            "ya_existia": False,
            "mensaje": f"Asistencia registrada exitosamente hoy a las {hora_hoy} en el aula {aula_id}"
        }