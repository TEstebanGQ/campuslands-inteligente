from __future__ import annotations

import json
import os
from typing import Any
from sqlalchemy import select, func
from core.persistence import get_sqlite_engine, Asistencia
from plugins.base import BasePlugin

DIAS_HABILES = 15

# Módulo global para almacenar en caché los datos académicos simulados
_MOCK_DATA_CACHE: dict[str, Any] | None = None


def get_academic_data(data_path: str = "simulation/mock_academic_data.json") -> dict[str, Any]:
    global _MOCK_DATA_CACHE
    if _MOCK_DATA_CACHE is None:
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    _MOCK_DATA_CACHE = json.load(f)
            except Exception:
                _MOCK_DATA_CACHE = {"estudiantes": {}}
        else:
            _MOCK_DATA_CACHE = {"estudiantes": {}}
    return _MOCK_DATA_CACHE


class StudentAnalyticsPlugin(BasePlugin):
    name = "student_analytics"

    def __init__(self, data_path: str = "simulation/mock_academic_data.json") -> None:
        self.data_path = data_path

    async def execute(self, *, estudiante_id: str) -> dict[str, Any]:
        # (a) Leer mock_academic_data.json una sola vez al primer uso y cachear en memoria a nivel de módulo
        data = get_academic_data(self.data_path)
        student_profile = data.get("estudiantes", {}).get(estudiante_id)

        if not student_profile:
            student_profile = {
                "nombre": f"Estudiante {estudiante_id}",
                "promedio_notas_historico": [3.0],
                "tendencia_declarada": "estable",
            }

        # (b) Calcular porcentaje_asistencia consultando la tabla asistencias vía SQLite
        engine = get_sqlite_engine()
        async with engine.begin() as conn:
            query = select(func.count(Asistencia.estudiante_id)).where(
                Asistencia.estudiante_id == estudiante_id
            )
            result = await conn.execute(query)
            asistencias_db = result.scalar() or 0

        # Porcentaje de asistencia entre 0.0 y 1.0 (días con registro / días hábiles)
        porcentaje_asistencia = min(1.0, asistencias_db / DIAS_HABILES)
        inasistencias_estimadas = max(0, DIAS_HABILES - asistencias_db)

        # (c) Tomar tendencia_academica directamente del JSON cacheado
        tendencia = student_profile.get("tendencia_declarada", "estable")

        # (d) Calcular riesgo_desercion (0-100) con la heurística ponderada especificada
        peso_tendencia = 0.5
        if tendencia == "declive":
            peso_tendencia = 1.0
        elif tendencia == "mejora":
            peso_tendencia = 0.0

        riesgo = round(100 * (0.6 * (1.0 - porcentaje_asistencia) + 0.4 * peso_tendencia))

        # Derivar nivel_riesgo ("bajo" < 30, "medio" 30-65, "alto" > 65)
        if riesgo < 30:
            nivel_riesgo = "bajo"
        elif riesgo <= 65:
            nivel_riesgo = "medio"
        else:
            nivel_riesgo = "alto"

        return {
            "estudiante_id": estudiante_id,
            "nombre": student_profile["nombre"],
            "porcentaje_asistencia": round(porcentaje_asistencia * 100.0, 1),
            "inasistencias_estimadas": inasistencias_estimadas,
            "retardos_estimados": 0,
            "tendencia_academica": tendencia,
            "riesgo_desercion": riesgo,
            "nivel_riesgo": nivel_riesgo,
            "mensaje": (
                f"El estudiante {student_profile['nombre']} tiene asistencia de "
                f"{porcentaje_asistencia * 100.0:.1f}%, {inasistencias_estimadas} inasistencias estimadas, "
                f"0 retardos estimados, tendencia académica '{tendencia}' y nivel de alerta "
                f"'{nivel_riesgo}' ({riesgo}/100)."
            ),
        }
