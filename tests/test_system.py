from __future__ import annotations

import pytest
import pytest_asyncio
import os
import json
import asyncio
from datetime import datetime, timezone
from shared.enums import AulaEstado
from shared.schemas import VisionEvent
from core.persistence import init_db, get_sqlite_engine, Asistencia, InMemoryKeyValueStore
from core.event_bus import get_event_bus
from plugins.attendance_ledger import AttendanceLedgerPlugin
from plugins.student_analytics import StudentAnalyticsPlugin
from plugins.anomaly_notifier import AnomalyNotifierPlugin
from plugins.space_optimizer import SpaceOptimizerPlugin
from agents.vision.embedding_engine import EmbeddingEngine
from agents.vision.classifier import LightweightStateClassifier
from agents.orchestrator.graph import get_orchestrator_graph
from agents.orchestrator.state import AgentState, OrigenEntrada
from langchain_core.messages import HumanMessage
from sqlalchemy import select


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_test_db():
    await init_db()

    # Respaldar mock_academic_data.json si existe
    backup_path = "simulation/mock_academic_data.json.bak"
    has_backup = os.path.exists("simulation/mock_academic_data.json")
    if has_backup:
        os.rename("simulation/mock_academic_data.json", backup_path)

    # Escribir archivo de datos académicos simulados temporal para los tests
    data = {
        "estudiantes": {
            "test_est_1": {
                "nombre": "Test Student 1",
                "notas": [4.0, 4.5],
                "asistencias_previas": 8,
                "total_sesiones": 10,
            }
        }
    }
    os.makedirs("simulation", exist_ok=True)
    with open("simulation/mock_academic_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f)

    yield

    try:
        os.remove("simulation/mock_academic_data.json")
    except Exception:
        pass

    # Restaurar el respaldo original
    if has_backup:
        os.rename(backup_path, "simulation/mock_academic_data.json")


@pytest.mark.asyncio
async def test_event_bus():
    bus = get_event_bus()
    events_received = []

    async def subscriber():
        async for event in bus.subscribe():
            events_received.append(event)
            break  # Consumir solo un evento

    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.1)  # Esperar registro del subscriptor

    test_event = VisionEvent(
        id="test-id",
        aula_id="304",
        estado=AulaEstado.ATENTO,
        confidence=0.95,
    )
    await bus.publish(test_event)
    await task

    assert len(events_received) == 1
    assert events_received[0].id == "test-id"
    assert events_received[0].aula_id == "304"


@pytest.mark.asyncio
async def test_attendance_ledger_plugin():
    plugin = AttendanceLedgerPlugin()

    # Ejecutar registro normal (atento)
    res = await plugin.execute(
        estudiante_id="test_est_1", aula_id="304", estado_visual="atento"
    )
    assert res["registrado"] is True
    assert res["ya_existia"] is False

    # Ejecutar registro duplicado (idempotencia)
    res_again = await plugin.execute(
        estudiante_id="test_est_1", aula_id="304", estado_visual="atento"
    )
    assert res_again["registrado"] is True
    assert res_again["ya_existia"] is True

    # Ejecutar con estudiante ausente
    res_ausente = await plugin.execute(
        estudiante_id="test_est_2", aula_id="304", estado_visual="ausente"
    )
    assert res_ausente["registrado"] is False


@pytest.mark.asyncio
async def test_student_analytics_plugin():
    plugin = StudentAnalyticsPlugin()

    res = await plugin.execute(estudiante_id="test_est_1")
    assert res["estudiante_id"] == "test_est_1"
    assert res["porcentaje_asistencia"] > 0
    assert res["nivel_riesgo"] in ["bajo", "medio", "alto"]


@pytest.mark.asyncio
async def test_anomaly_notifier_plugin():
    plugin = AnomalyNotifierPlugin()

    # Resetear tienda KV para el test
    await InMemoryKeyValueStore.set("anomalias", "304:posible_desercion_sesion", None)

    # Duración bajo umbral (sin alerta)
    res = await plugin.execute(
        aula_id="304", estado_visual="ausente", duracion_minutos=10
    )
    assert res["alerta_generada"] is False

    # Duración sobre umbral (genera alerta)
    res_alert = await plugin.execute(
        aula_id="304", estado_visual="ausente", duracion_minutos=20
    )
    assert res_alert["alerta_generada"] is True
    assert res_alert["tipo_alerta"] == "posible_desercion_sesion"

    # Segunda ejecución (bloqueada por cooldown)
    res_cooldown = await plugin.execute(
        aula_id="304", estado_visual="ausente", duracion_minutos=20
    )
    assert res_cooldown["alerta_generada"] is False
    assert "cooldown" in res_cooldown["mensaje"].lower()


@pytest.mark.asyncio
async def test_space_optimizer_plugin():
    plugin = SpaceOptimizerPlugin()

    res = await plugin.execute(aula_id="304", ocupacion_actual=2, capacidad_maxima=20)
    assert res["aula_id"] == "304"
    assert res["tasa_utilizacion"] == 0.1
    assert res["requiere_accion"] is True


@pytest.mark.asyncio
async def test_classifier_and_embedding():
    classifier = LightweightStateClassifier()
    engine = EmbeddingEngine()

    # Embedding mock de atento
    emb_atento = engine.get_embedding("simulation/frames/atento_classroom.jpg")
    estado, confidence = classifier.classify(emb_atento)
    assert estado == AulaEstado.ATENTO
    assert confidence > 0.8

    # Embedding mock de ausente
    emb_ausente = engine.get_embedding("simulation/frames/ausente_classroom.jpg")
    estado_aus, conf_aus = classifier.classify(emb_ausente)
    assert estado_aus == AulaEstado.AUSENTE
    assert conf_aus > 0.8


@pytest.mark.asyncio
async def test_orchestrator_graph():
    graph = get_orchestrator_graph()

    state = AgentState(
        session_id="test-session-chat",
        origen=OrigenEntrada.CHAT_ESTUDIANTE,
        usuario_id="test_est_1",
        rol="estudiante",
        messages=[HumanMessage(content="¿Cómo voy este mes? Estudiante test_est_1")],
    )

    final_state = await graph.ainvoke(state)
    assert final_state["respuesta_final"] is not None
    assert len(final_state["tool_executions"]) > 0
