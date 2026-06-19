from __future__ import annotations

from langchain_core.tools import tool

from plugins.attendance_ledger import AttendanceLedgerPlugin
from plugins.student_analytics import StudentAnalyticsPlugin
from plugins.anomaly_notifier import AnomalyNotifierPlugin
from plugins.space_optimizer import SpaceOptimizerPlugin

_attendance_plugin = AttendanceLedgerPlugin()
_analytics_plugin = StudentAnalyticsPlugin()
_anomaly_plugin = AnomalyNotifierPlugin()
_space_plugin = SpaceOptimizerPlugin()


@tool
async def registrar_asistencia(estudiante_id: str, aula_id: str, estado_visual: str) -> dict:
    """
    Registra la asistencia de un estudiante a partir de una detección
    visual confirmada. Usar cuando se recibe un VisionEvent con
    identidad reconocida, o cuando el administrador solicita confirmar
    asistencia de un estudiante de forma manual.
    """
    return await _attendance_plugin.execute(
        estudiante_id=estudiante_id, aula_id=aula_id, estado_visual=estado_visual
    )


@tool
async def consultar_analitica_estudiante(estudiante_id: str) -> dict:
    """
    Retorna el resumen académico y de asistencia de un estudiante:
    porcentaje de asistencia, inasistencias estimadas, tendencia de
    desempeño y nivel de riesgo. Usar cuando un estudiante pregunta por
    su propio estado, o cuando un administrador consulta un caso puntual.
    """
    return await _analytics_plugin.execute(estudiante_id=estudiante_id)


@tool
async def evaluar_anomalia(aula_id: str, estado_visual: str, duracion_minutos: int) -> dict:
    """
    Evalúa si un patrón visual sostenido (aula ausente o break extendido)
    amerita una notificación de alerta temprana al administrador.
    """
    return await _anomaly_plugin.execute(
        aula_id=aula_id, estado_visual=estado_visual, duracion_minutos=duracion_minutos
    )


@tool
async def optimizar_espacio(aula_id: str, ocupacion_actual: int, capacidad_maxima: int) -> dict:
    """
    Calcula recomendaciones de optimización de uso de espacio físico
    a partir de la ocupación real medida frente a la capacidad
    declarada del aula.
    """
    return await _space_plugin.execute(
        aula_id=aula_id, ocupacion_actual=ocupacion_actual, capacidad_maxima=capacidad_maxima
    )


CATALOGO_DE_HERRAMIENTAS = [
    registrar_asistencia,
    consultar_analitica_estudiante,
    evaluar_anomalia,
    optimizar_espacio,
]
