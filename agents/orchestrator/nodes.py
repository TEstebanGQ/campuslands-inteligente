from __future__ import annotations

import logging
import json
from typing import Any

from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from agents.orchestrator.state import AgentState, ToolExecutionRecord
from agents.orchestrator.tools import CATALOGO_DE_HERRAMIENTAS
from shared.config import get_settings

logger = logging.getLogger("campuslands.orchestrator.nodes")

_SYSTEM_PROMPT = (
    "Eres el Cognitive Orchestrator de Campuslands Inteligente. "
    "Tu trabajo es decidir, a partir de eventos de visión o mensajes "
    "de chat, qué herramientas del catálogo deben ejecutarse para "
    "resolver la necesidad del estudiante o del administrador. "
    "Nunca inventes datos académicos o de asistencia: siempre que "
    "necesites un dato del sistema, usa la herramienta correspondiente "
    "en lugar de asumirlo."
)


class MockChatOpenAI:
    """
    Mock LLM que realiza Tool Calling basado en reglas simples para cuando
    no hay una API key de OpenAI válida configurada.
    """
    def __init__(self, model: str, temperature: float) -> None:
        self.model = model
        self.temperature = temperature
        self.tools = []

    def bind_tools(self, tools: list[Any]) -> MockChatOpenAI:
        self.tools = tools
        return self

    async def ainvoke(self, messages: list[Any]) -> AIMessage:
        last_msg = ""
        if messages:
            last_msg = messages[-1].content.lower()

        tool_calls = []
        reply_content = ""

        has_tool_response = any(isinstance(m, ToolMessage) for m in messages)

        if has_tool_response:
            tool_responses = []
            for m in messages:
                if isinstance(m, ToolMessage):
                    try:
                        parsed = json.loads(m.content)
                        msg_detail = parsed.get("mensaje") or parsed.get("recomendacion") or str(parsed)
                        tool_responses.append(msg_detail)
                    except Exception:
                        tool_responses.append(m.content)

            reply_content = (
                f"He procesado la consulta a través de los servicios internos. "
                f"Resultados: {'; '.join(tool_responses)}"
            )
        else:
            if "asistencia" in last_msg or "registrar_asistencia" in last_msg or "evento de visión" in last_msg:
                estudiante_id = "estudiante_1"
                for word in last_msg.replace(":", " ").replace(",", " ").split():
                    if word.startswith("estudiante_") or word.isdigit():
                        estudiante_id = word if word.startswith("estudiante_") else f"estudiante_{word}"
                
                aula_id = "304"
                for word in last_msg.split():
                    if word.isdigit() and not word.startswith("estudiante"):
                        aula_id = word

                estado_visual = "atento"
                if "ausente" in last_msg:
                    estado_visual = "ausente"
                elif "distraido" in last_msg or "distraído" in last_msg:
                    estado_visual = "distraído"

                tool_calls.append({
                    "name": "registrar_asistencia",
                    "args": {"estudiante_id": estudiante_id, "aula_id": aula_id, "estado_visual": estado_visual},
                    "id": "call_asistencia",
                    "type": "tool_call"
                })

            elif "analitica" in last_msg or "analítica" in last_msg or "riesgo" in last_msg or "desempeño" in last_msg or "notas" in last_msg or "cómo voy" in last_msg or "como voy" in last_msg:
                estudiante_id = "estudiante_1"
                for word in last_msg.replace(":", " ").replace(",", " ").split():
                    if word.startswith("estudiante_") or word.isdigit():
                        estudiante_id = word if word.startswith("estudiante_") else f"estudiante_{word}"

                tool_calls.append({
                    "name": "consultar_analitica_estudiante",
                    "args": {"estudiante_id": estudiante_id},
                    "id": "call_analitica",
                    "type": "tool_call"
                })

            elif "anomalia" in last_msg or "anomalía" in last_msg or "alerta" in last_msg:
                aula_id = "304"
                for word in last_msg.split():
                    if word.isdigit():
                        aula_id = word
                
                estado_visual = "ausente"
                if "distraido" in last_msg or "distraído" in last_msg:
                    estado_visual = "distraído"

                tool_calls.append({
                    "name": "evaluar_anomalia",
                    "args": {"aula_id": aula_id, "estado_visual": estado_visual, "duracion_minutos": 20},
                    "id": "call_anomalia",
                    "type": "tool_call"
                })

            elif "optimizar" in last_msg or "espacio" in last_msg or "ocupacion" in last_msg or "ocupación" in last_msg or "capacidad" in last_msg:
                aula_id = "304"
                for word in last_msg.split():
                    if word.isdigit():
                        aula_id = word

                tool_calls.append({
                    "name": "optimizar_espacio",
                    "args": {"aula_id": aula_id, "ocupacion_actual": 8, "capacidad_maxima": 25},
                    "id": "call_espacio",
                    "type": "tool_call"
                })
            else:
                reply_content = (
                    "¡Hola! Soy el Cognitive Orchestrator de Campuslands Inteligente. "
                    "Puedo ayudarte a consultar el estado académico/asistencia de estudiantes, "
                    "evaluar anomalías en aulas o calcular la optimización de espacios físicos."
                )

        return AIMessage(content=reply_content, tool_calls=tool_calls)


def _build_llm():
    settings = get_settings()
    if not settings.openai_api_key or settings.openai_api_key.startswith("mock"):
        return MockChatOpenAI(
            model=settings.orchestrator_model,
            temperature=0,
        ).bind_tools(CATALOGO_DE_HERRAMIENTAS)
    return ChatOpenAI(
        model=settings.orchestrator_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).bind_tools(CATALOGO_DE_HERRAMIENTAS)


async def router_node(state: AgentState) -> AgentState:
    llm = _build_llm()
    mensajes = [SystemMessage(content=_SYSTEM_PROMPT), *state.messages]
    respuesta = await llm.ainvoke(mensajes)
    state.messages = [respuesta]
    state.tool_calls_pendientes = respuesta.tool_calls or []
    return state


async def ejecutar_herramienta_node(state: AgentState) -> AgentState:
    tool_node = ToolNode(CATALOGO_DE_HERRAMIENTAS)
    resultado = await tool_node.ainvoke({"messages": state.messages})

    for tool_message in resultado["messages"]:
        if isinstance(tool_message, ToolMessage):
            state.registrar_ejecucion(
                ToolExecutionRecord(
                    plugin_name=tool_message.name or "desconocido",
                    arguments={},
                    result={"contenido": tool_message.content},
                )
            )
    state.messages = resultado["messages"]
    state.tool_calls_pendientes = []
    return state


async def responder_node(state: AgentState) -> AgentState:
    llm = _build_llm()
    mensajes = [SystemMessage(content=_SYSTEM_PROMPT), *state.messages]
    respuesta = await llm.ainvoke(mensajes)
    state.respuesta_final = respuesta.content
    return state
