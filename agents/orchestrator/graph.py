from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from agents.orchestrator.state import AgentState
from agents.orchestrator.nodes import router_node, ejecutar_herramienta_node, responder_node
from core.event_bus import EventBus

logger = logging.getLogger("campuslands.orchestrator")


def _hay_tools_pendientes(state: AgentState) -> str:
    return "ejecutar_herramienta" if state.tool_calls_pendientes else "responder"


def build_orchestrator_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("ejecutar_herramienta", ejecutar_herramienta_node)
    graph.add_node("responder", responder_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _hay_tools_pendientes,
        {"ejecutar_herramienta": "ejecutar_herramienta", "responder": "responder"},
    )
    graph.add_edge("ejecutar_herramienta", "router")
    graph.add_edge("responder", END)

    return graph.compile()


_compiled_graph = None


def get_orchestrator_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_orchestrator_graph()
    return _compiled_graph


async def start_event_listener(event_bus: EventBus) -> None:
    """
    Tarea de fondo lanzada en el lifespan de FastAPI: consume
    VisionEvents del bus y los empuja al grafo como entradas reactivas.
    """
    graph = get_orchestrator_graph()
    async for vision_event in event_bus.subscribe():
        initial_state = AgentState(
            session_id=f"vision-{vision_event.aula_id}-{vision_event.timestamp.isoformat()}",
            origen="vision_event",
            vision_event_id=vision_event.id,
            aula_id=vision_event.aula_id,
            messages=[
                HumanMessage(
                    content=(
                        f"Evento de visión recibido en aula {vision_event.aula_id}: "
                        f"estado={vision_event.estado}, confianza={vision_event.confidence:.2f}."
                    )
                )
            ],
        )
        try:
            await graph.ainvoke(initial_state)
        except Exception:
            logger.exception("Error procesando VisionEvent %s", vision_event.id)
