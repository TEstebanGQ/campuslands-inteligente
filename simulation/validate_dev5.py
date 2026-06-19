from __future__ import annotations

import asyncio
from core.persistence import init_db, get_sqlite_engine, Asistencia
from sqlalchemy import insert
from plugins.student_analytics import StudentAnalyticsPlugin
from plugins.anomaly_notifier import AnomalyNotifierPlugin


async def validate():
    print("=== VALIDACIÓN DE DESARROLLADOR 5 EN AISLAMIENTO ===")

    # 1. Inicializar la base de datos SQLite en memoria
    await init_db()

    # 2. Registrar 14 asistencias en SQLite para estudiante_1 para verificar riesgo bajo
    engine = get_sqlite_engine()
    async with engine.begin() as conn:
        for day in range(1, 15):
            stmt = insert(Asistencia).values(
                estudiante_id="estudiante_1",
                fecha=f"2026-06-{day:02d}",
                hora_registro="08:00:00",
                aula_id="304",
            )
            await conn.execute(stmt)

    # 3. Probar StudentAnalyticsPlugin
    analytics_plugin = StudentAnalyticsPlugin()

    # Verificación de estudiante_1 (Camilo Torres: 14 asistencias, tendencia "mejora")
    # riesgo = round(100 * (0.6 * (1 - 14/15) + 0.4 * 0)) = 4% -> riesgo bajo
    print("\n--- Ejecutando StudentAnalytics para estudiante_1 (Camilo Torres) ---")
    res_camilo = await analytics_plugin.execute(estudiante_id="estudiante_1")
    print(f"Nombre: {res_camilo['nombre']}")
    print(f"Asistencia %: {res_camilo['porcentaje_asistencia']}%")
    print(f"Riesgo: {res_camilo['riesgo_desercion']}/100 ({res_camilo['nivel_riesgo']})")
    print(f"Mensaje: {res_camilo['mensaje']}")

    # Verificación de estudiante_2 (Maria Gomez: 0 asistencias, tendencia "declive")
    # riesgo = round(100 * (0.6 * 1.0 + 0.4 * 1.0)) = 100% -> riesgo alto
    print("\n--- Ejecutando StudentAnalytics para estudiante_2 (Maria Gomez) ---")
    res_maria = await analytics_plugin.execute(estudiante_id="estudiante_2")
    print(f"Nombre: {res_maria['nombre']}")
    print(f"Asistencia %: {res_maria['porcentaje_asistencia']}%")
    print(f"Riesgo: {res_maria['riesgo_desercion']}/100 ({res_maria['nivel_riesgo']})")
    print(f"Mensaje: {res_maria['mensaje']}")

    # 4. Probar AnomalyNotifierPlugin
    anomaly_plugin = AnomalyNotifierPlugin()

    # Disparar alerta por primera vez
    print("\n--- Ejecutando AnomalyNotifier en aula 101 por primera vez (ausente por 25 min) ---")
    res_alert = await anomaly_plugin.execute(
        aula_id="101", estado_visual="ausente", duracion_minutos=25
    )
    print(f"Alerta generada: {res_alert['alerta_generada']}")
    print(f"Tipo alerta: {res_alert['tipo_alerta']}")
    print(f"Mensaje: {res_alert['mensaje']}")

    # Segunda llamada inmediata (supresión por cooldown)
    print("\n--- Ejecutando AnomalyNotifier en aula 101 por segunda vez (cooldown activo) ---")
    res_cooldown = await anomaly_plugin.execute(
        aula_id="101", estado_visual="ausente", duracion_minutos=25
    )
    print(f"Alerta generada: {res_cooldown['alerta_generada']}")
    print(f"Tipo alerta: {res_cooldown['tipo_alerta']}")
    print(f"Mensaje: {res_cooldown['mensaje']}")

    print("\n=== VALIDACIÓN COMPLETA ===")


if __name__ == "__main__":
    asyncio.run(validate())
