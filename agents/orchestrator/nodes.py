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
            cleaned_msg = last_msg.replace(":", " ").replace(",", " ").replace(".", " ").replace("?", " ").replace("¿", " ")
            words = cleaned_msg.split()

            # Helper to find student ID
            estudiante_id = "estudiante_1"
            for i, word in enumerate(words):
                if word.startswith("estudiante_"):
                    estudiante_id = word
                    break
                elif word == "estudiante" and i + 1 < len(words):
                    next_word = words[i+1]
                    if next_word.isdigit():
                        estudiante_id = f"estudiante_{next_word}"
                        break
                    elif next_word.startswith("estudiante_"):
                        estudiante_id = next_word
                        break

            # Helper to find classroom/aula ID
            aula_id = "304"
            for i, word in enumerate(words):
                if word == "aula" and i + 1 < len(words):
                    next_word = words[i+1]
                    if next_word.isdigit():
                        aula_id = next_word
                        break

            if "asistencia" in last_msg or "registrar_asistencia" in last_msg or "evento de visión" in last_msg:
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
                tool_calls.append({
                    "name": "consultar_analitica_estudiante",
                    "args": {"estudiante_id": estudiante_id},
                    "id": "call_analitica",
                    "type": "tool_call"
                })

            elif "anomalia" in last_msg or "anomalía" in last_msg or "alerta" in last_msg:
                estado_visual = "ausente"
                if "distraido" in last_msg or "distraído" in last_msg:
                    estado_visual = "distraído"

                duracion = 20
                for i, word in enumerate(words):
                    if word == "minutos" and i - 1 >= 0:
                        prev_word = words[i-1]
                        if prev_word.isdigit():
                            duracion = int(prev_word)
                            break

                tool_calls.append({
                    "name": "evaluar_anomalia",
                    "args": {"aula_id": aula_id, "estado_visual": estado_visual, "duracion_minutos": duracion},
                    "id": "call_anomalia",
                    "type": "tool_call"
                })

            elif "optimizar" in last_msg or "espacio" in last_msg or "ocupacion" in last_msg or "ocupación" in last_msg or "capacidad" in last_msg:
                ocupacion_actual = 8
                capacidad_maxima = 25
                for i, word in enumerate(words):
                    if (word == "ocupación" or word == "ocupacion") and i + 1 < len(words):
                        for next_w in words[i+1:]:
                            if next_w.isdigit():
                                ocupacion_actual = int(next_w)
                                break
                    if word == "capacidad" and i + 1 < len(words):
                        for next_w in words[i+1:]:
                            if next_w.isdigit():
                                capacidad_maxima = int(next_w)
                                break

                tool_calls.append({
                    "name": "optimizar_espacio",
                    "args": {"aula_id": aula_id, "ocupacion_actual": ocupacion_actual, "capacidad_maxima": capacidad_maxima},
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
    tool_calls = state.tool_calls_pendientes
    tool_map = {t.name: t for t in CATALOGO_DE_HERRAMIENTAS}
    new_messages = list(state.messages)

    for tool_call in tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call["id"]

        tool_func = tool_map.get(name)
        if tool_func:
            try:
                result = await tool_func.ainvoke(args)
                result_str = json.dumps(result)

                new_messages.append(
                    ToolMessage(
                        content=result_str,
                        name=name,
                        tool_call_id=call_id
                    )
                )

                state.registrar_ejecucion(
                    ToolExecutionRecord(
                        plugin_name=name,
                        arguments=args,
                        result=result,
                        success=True
                    )
                )
            except Exception as e:
                new_messages.append(
                    ToolMessage(
                        content=f"Error executing tool {name}: {str(e)}",
                        name=name,
                        tool_call_id=call_id
                    )
                )
                state.registrar_ejecucion(
                    ToolExecutionRecord(
                        plugin_name=name,
                        arguments=args,
                        result={},
                        success=False,
                        error_message=str(e)
                    )
                )
        else:
            err_msg = f"Tool {name} not found in catalog."
            new_messages.append(
                ToolMessage(
                    content=err_msg,
                    name=name,
                    tool_call_id=call_id
                )
            )
            state.registrar_ejecucion(
                ToolExecutionRecord(
                    plugin_name=name,
                    arguments=args,
                    result={},
                    success=False,
                    error_message=err_msg
                )
            )

    state.messages = new_messages
    state.tool_calls_pendientes = []
    return state


async def responder_node(state: AgentState) -> AgentState:
    llm = _build_llm()
    mensajes = [SystemMessage(content=_SYSTEM_PROMPT), *state.messages]
    respuesta = await llm.ainvoke(mensajes)
    state.respuesta_final = respuesta.content
    return state
