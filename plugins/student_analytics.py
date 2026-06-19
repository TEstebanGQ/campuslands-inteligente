from __future__ import annotations

import json
import os
from typing import Any
from sqlalchemy import select, func
from core.persistence import get_sqlite_engine, Asistencia
from plugins.base import BasePlugin

class StudentAnalyticsPlugin(BasePlugin):
    name = "student_analytics"

    def __init__(self, data_path: str = "simulation/mock_academic_data.json") -> None:
        self.data_path = data_path

    async def execute(self, *, estudiante_id: str) -> dict[str, Any]:
        student_profile = None
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    student_profile = data.get("estudiantes", {}).get(estudiante_id)
            except Exception:
                pass

        if not student_profile:
            student_profile = {
                "nombre": f"Estudiante {estudiante_id}",
                "notas": [3.5, 3.2, 3.0],
                "asistencias_previas": 8,
                "total_sesiones": 10
            }

        # Query SQLite for additional attendance records recorded during execution
        engine = get_sqlite_engine()
        async with engine.begin() as conn:
            query = select(func.count(Asistencia.estudiante_id)).where(
                Asistencia.estudiante_id == estudiante_id
            )
            result = await conn.execute(query)
            asistencias_db = result.scalar() or 0

        total_asistencias = student_profile["asistencias_previas"] + asistencias_db
        total_sesiones = student_profile["total_sesiones"]
        if total_sesiones <= 0:
            total_sesiones = 10

        pct_asistencia = min(100.0, (total_asistencias / total_sesiones) * 100.0)

        # Academic grades trend
        notas = student_profile.get("notas", [3.0])
        if len(notas) >= 2:
            diff = notas[-1] - notas[-2]
            if diff > 0.1:
                tendencia = "mejora"
            elif diff < -0.1:
                tendencia = "declive"
            else:
                tendencia = "estable"
        else:
            tendencia = "estable"

        # Heuristic for academic risk (using 5.0 as max grade)
        avg_grade = sum(notas) / len(notas) if notas else 3.0
        grade_risk = max(0.0, min(100.0, (5.0 - avg_grade) / 4.0 * 100.0))

        # Heuristic for trend risk
        trend_risk = 50.0
        if tendencia == "declive":
            trend_risk = 100.0
        elif tendencia == "mejora":
            trend_risk = 0.0

        # Heuristic for attendance risk
        attendance_risk = 100.0 - pct_asistencia

        # Weighted score (50% attendance, 30% academic, 20% trend)
        riesgo_desercion = int(0.5 * attendance_risk + 0.3 * grade_risk + 0.2 * trend_risk)

        if riesgo_desercion > 70:
            nivel_riesgo = "alto"
        elif riesgo_desercion > 35:
            nivel_riesgo = "medio"
        else:
            nivel_riesgo = "bajo"

        return {
            "estudiante_id": estudiante_id,
            "nombre": student_profile["nombre"],
            "porcentaje_asistencia": round(pct_asistencia, 1),
            "tendencia_academica": tendencia,
            "riesgo_desercion": riesgo_desercion,
            "nivel_riesgo": nivel_riesgo,
            "mensaje": (
                f"El estudiante {student_profile['nombre']} tiene un porcentaje de asistencia de "
                f"{pct_asistencia:.1f}%, tendencia académica '{tendencia}' y nivel de riesgo de deserción "
                f"'{nivel_riesgo}' ({riesgo_desercion}/100)."
            )
        }
