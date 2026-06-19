from __future__ import annotations

import os
import json
import pytest
from datetime import date, time
from sqlalchemy import insert
from core.persistence import init_db, get_sqlite_engine, Asistencia
from plugins.student_analytics import StudentAnalyticsPlugin


@pytest.mark.asyncio
async def test_student_analytics_risk_levels():
    """
    Prueba que calcula el porcentaje de asistencia desde SQLite y valida
    que la heurística ponderada arroje los 3 niveles de riesgo según los umbrales:
    - bajo (< 30)
    - medio (30-65)
    - alto (> 65)
    """
    await init_db()

    # 1. Crear archivo temporal de datos académicos mock
    mock_data = {
        "estudiantes": {
            "est_bajo": {
                "nombre": "Estudiante Bajo Riesgo",
                "promedio_notas_historico": [4.5, 4.8],
                "tendencia_declarada": "mejora",
            },
            "est_medio": {
                "nombre": "Estudiante Medio Riesgo",
                "promedio_notas_historico": [3.5, 3.2],
                "tendencia_declarada": "estable",
            },
            "est_alto": {
                "nombre": "Estudiante Alto Riesgo",
                "promedio_notas_historico": [2.0, 1.8],
                "tendencia_declarada": "declive",
            },
        }
    }

    temp_path = "simulation/temp_academic_data.json"
    os.makedirs("simulation", exist_ok=True)
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    try:
        # 2. Poblar base de datos SQLite con registros de asistencia
        engine = get_sqlite_engine()
        async with engine.begin() as conn:
            # est_bajo: 14 asistencias de 15 días hábiles
            for day in range(1, 15):
                stmt = insert(Asistencia).values(
                    estudiante_id="est_bajo",
                    fecha=date(2026, 6, day),
                    hora_registro=time(8, 0, 0),
                    aula_id="304",
                )
                await conn.execute(stmt)

            # est_medio: 8 asistencias de 15 días hábiles
            for day in range(1, 9):
                stmt = insert(Asistencia).values(
                    estudiante_id="est_medio",
                    fecha=date(2026, 6, day),
                    hora_registro=time(8, 0, 0),
                    aula_id="304",
                )
                await conn.execute(stmt)

            # est_alto: 0 asistencias (se deja vacío en SQLite)

        # 3. Instanciar el plugin apuntando al archivo temporal
        # Nota: forzar la recarga del caché del módulo
        import plugins.student_analytics
        plugins.student_analytics._MOCK_DATA_CACHE = None
        plugin = StudentAnalyticsPlugin(data_path=temp_path)

        # Caso bajo riesgo (14/15 asistencias = 93.3% asistencia, tendencia "mejora")
        # riesgo = round(100 * (0.6 * (1 - 0.933) + 0.4 * 0)) = round(4.0) = 4
        res_bajo = await plugin.execute(estudiante_id="est_bajo")
        assert res_bajo["nivel_riesgo"] == "bajo"
        assert res_bajo["riesgo_desercion"] < 30

        # Caso medio riesgo (8/15 asistencias = 53.3% asistencia, tendencia "estable")
        # riesgo = round(100 * (0.6 * (1 - 0.533) + 0.4 * 0.5)) = round(100 * (0.28 + 0.20)) = 48
        res_medio = await plugin.execute(estudiante_id="est_medio")
        assert res_medio["nivel_riesgo"] == "medio"
        assert 30 <= res_medio["riesgo_desercion"] <= 65

        # Caso alto riesgo (0 asistencias = 0.0% asistencia, tendencia "declive")
        # riesgo = round(100 * (0.6 * 1.0 + 0.4 * 1.0)) = 100
        res_alto = await plugin.execute(estudiante_id="est_alto")
        assert res_alto["nivel_riesgo"] == "alto"
        assert res_alto["riesgo_desercion"] > 65

    finally:
        # 4. Limpieza del archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
