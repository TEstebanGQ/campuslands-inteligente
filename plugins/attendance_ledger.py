from __future__ import annotations

from datetime import date, datetime
from typing import Any
from sqlalchemy import insert, select, text
from core.persistence import get_sqlite_engine, Asistencia
from plugins.base import BasePlugin

class AttendanceLedgerPlugin(BasePlugin):
    name = "attendance_ledger"
    _ddl_initialized = False

    @classmethod
    async def _ensure_attendance_table(cls, conn: Any) -> None:
        if cls._ddl_initialized:
            return

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asistencias (
                estudiante_id VARCHAR NOT NULL,
                fecha DATE NOT NULL,
                hora_registro TIME NOT NULL,
                aula_id INTEGER NOT NULL,
                PRIMARY KEY (estudiante_id, fecha),
                CONSTRAINT uq_estudiante_fecha UNIQUE (estudiante_id, fecha)
            )
        """))
        cls._ddl_initialized = True

    async def execute(self, *, estudiante_id: str, aula_id: str, estado_visual: str) -> dict[str, Any]:
        ahora = datetime.now()
        fecha_hoy = ahora.date()
        hora_hoy = ahora.time().replace(microsecond=0)
        fecha_respuesta = fecha_hoy.isoformat()
        hora_respuesta = hora_hoy.isoformat()

        engine = get_sqlite_engine()
        async with engine.begin() as conn:
            await self._ensure_attendance_table(conn)

            if estado_visual == "ausente":
                return {
                    "registrado": False,
                    "estudiante_id": estudiante_id,
                    "fecha": fecha_respuesta,
                    "ya_existia": False,
                    "mensaje": "Aula ausente o estudiante no detectado: se marca inasistencia preventiva, no se registra asistencia"
                }

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
                    "fecha": fecha_respuesta,
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
            "fecha": fecha_respuesta,
            "ya_existia": False,
            "mensaje": f"Asistencia automática registrada hoy a las {hora_respuesta} en el aula {aula_id}"
        }
