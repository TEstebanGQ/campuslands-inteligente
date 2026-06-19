from __future__ import annotations

import asyncio
import os
import json
from pathlib import Path
from core.persistence import init_db, get_sqlite_engine, Asistencia, InMemoryKeyValueStore
from core.fiftyone_manager import get_fiftyone_manager
from agents.vision.pipeline import VisionPipeline
from agents.orchestrator.graph import get_orchestrator_graph
from agents.orchestrator.state import AgentState, OrigenEntrada
from langchain_core.messages import HumanMessage
from sqlalchemy import select


async def main():
    print("=== STARTING CAMPUSLANDS INTELIGENTE SIMULATION ===")

    # 1. Inicialización y creación de carpetas/archivos
    print("\n--- 1. Inicialización ---")
    await init_db()
    print("Base de datos SQLite en memoria inicializada.")

    frames_dir = Path("simulation/frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Crear imágenes mock (el motor determinista clasifica según la palabra clave en el nombre)
    atento_path = frames_dir / "atento_aula_304.jpg"
    distraido_path = frames_dir / "distraido_aula_304.jpg"
    ausente_path = frames_dir / "ausente_aula_304.jpg"

    atento_path.write_bytes(b"mock atento image content")
    distraido_path.write_bytes(b"mock distraido image content")
    ausente_path.write_bytes(b"mock ausente image content")
    print("Archivos de frames simulados creados en simulation/frames/.")

    # Arrancar FiftyOne Manager de manera no bloqueante
    fo_manager = get_fiftyone_manager()
    await fo_manager.startup()
    print("FiftyOne Dataset Manager iniciado.")

    # 2. Ejecutar Pipeline de Visión (Agente 1)
    print("\n--- 2. Procesamiento de Frames de Visión (Agente 1) ---")
    pipeline = VisionPipeline()

    print("\nProcesando frame 'atento' en el aula 304:")
    event_atento = await pipeline.process_frame(str(atento_path), "304")
    print(
        f"Evento de Visión generado -> ID: {event_atento.id}, Aula: {event_atento.aula_id}, "
        f"Estado: {event_atento.estado}, Confianza: {event_atento.confidence:.2f}"
    )

    # Simular la reacción del orquestador (Agente 2) registrando la asistencia de estudiante_1
    graph = get_orchestrator_graph()

    print("\nSimulando orquestación de asistencia para estudiante_1:")
    prompt_asistencia = (
        f"Registrar asistencia para el estudiante estudiante_1 en el aula 304 "
        f"tras detección visual confirmada en estado atento"
    )
    state_asistencia = AgentState(
        session_id="sim-asistencia-1",
        origen=OrigenEntrada.VISION_EVENT,
        aula_id="304",
        messages=[HumanMessage(content=prompt_asistencia)],
    )
    res_asistencia = await graph.ainvoke(state_asistencia)
    print(f"Respuesta del Orquestador:\n{res_asistencia.get('respuesta_final')}")

    # 3. Consulta académica del estudiante (Chat Estudiante)
    print("\n--- 3. Consulta de Analítica de Estudiante (Agente 2) ---")
    prompt_chat_camilo = "¿Cómo voy este mes? Estudiante estudiante_1"
    state_camilo = AgentState(
        session_id="sim-chat-camilo",
        origen=OrigenEntrada.CHAT_ESTUDIANTE,
        usuario_id="estudiante_1",
        rol="estudiante",
        messages=[HumanMessage(content=prompt_chat_camilo)],
    )
    res_camilo = await graph.ainvoke(state_camilo)
    print(f"Pregunta: '{prompt_chat_camilo}'")
    print(f"Respuesta:\n{res_camilo.get('respuesta_final')}")

    # Consulta de Maria Gomez (riesgo de deserción por ausentismo previo)
    prompt_chat_maria = "¿Cuál es mi nivel de riesgo de deserción? Estudiante estudiante_2"
    state_maria = AgentState(
        session_id="sim-chat-maria",
        origen=OrigenEntrada.CHAT_ESTUDIANTE,
        usuario_id="estudiante_2",
        rol="estudiante",
        messages=[HumanMessage(content=prompt_chat_maria)],
    )
    res_maria = await graph.ainvoke(state_maria)
    print(f"\nPregunta: '{prompt_chat_maria}'")
    print(f"Respuesta:\n{res_maria.get('respuesta_final')}")

    # 4. Alerta de Anomalía (Chat Administrador / Evento)
    print("\n--- 4. Evaluación de Anomalías en Aulas (Agente 2) ---")
    prompt_chat_alerta = "Evaluar anomalía en el aula 304: el aula ha estado en estado ausente durante 20 minutos"
    state_alerta = AgentState(
        session_id="sim-chat-alerta",
        origen=OrigenEntrada.CHAT_ADMIN,
        rol="administrador",
        messages=[HumanMessage(content=prompt_chat_alerta)],
    )
    res_alerta = await graph.ainvoke(state_alerta)
    print(f"Pregunta: '{prompt_chat_alerta}'")
    print(f"Respuesta:\n{res_alerta.get('respuesta_final')}")

    # 5. Optimización de Espacios (Chat Administrador)
    print("\n--- 5. Optimización de Espacios Físicos (Agente 2) ---")
    prompt_chat_espacio = "Optimizar espacio del aula 304. Ocupación actual: 4 personas, capacidad máxima: 25"
    state_espacio = AgentState(
        session_id="sim-chat-espacio",
        origen=OrigenEntrada.CHAT_ADMIN,
        rol="administrador",
        messages=[HumanMessage(content=prompt_chat_espacio)],
    )
    res_espacio = await graph.ainvoke(state_espacio)
    print(f"Pregunta: '{prompt_chat_espacio}'")
    print(f"Respuesta:\n{res_espacio.get('respuesta_final')}")

    # 6. Inspección de datos consolidados
    print("\n--- 6. Verificación de Integridad de Datos ---")

    # Registro de Asistencia SQLite
    engine = get_sqlite_engine()
    async with engine.begin() as conn:
        q = select(Asistencia)
        res = await conn.execute(q)
        records = res.fetchall()
        print("\nRegistros de asistencia guardados en SQLite:")
        for r in records:
            print(
                f"- Estudiante ID: {r.estudiante_id}, Fecha: {r.fecha}, "
                f"Hora: {r.hora_registro}, Aula: {r.aula_id}"
            )

    # Anomalias en KeyValueStore
    print("\nAlertas activas en InMemoryKeyValueStore:")
    anomalias = await InMemoryKeyValueStore.list_namespace("anomalias")
    print(json.dumps(anomalias, indent=2))

    # Ocupación histórica en KeyValueStore
    print("\nHistorial de ocupación en InMemoryKeyValueStore:")
    ocupaciones = await InMemoryKeyValueStore.list_namespace("ocupacion_historica")
    print(json.dumps(ocupaciones, indent=2))

    # Resumen de FiftyOne
    print("\nResumen del Dataset de FiftyOne:")
    summary = fo_manager.get_dataset_summary()
    print(json.dumps(summary, indent=2))

    # Cierre
    await fo_manager.shutdown()
    print("\n=== SIMULACIÓN COMPLETADA CON ÉXITO ===")


if __name__ == "__main__":
    asyncio.run(main())
