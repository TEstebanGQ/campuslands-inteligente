from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, HTTPException
from shared.schemas import ChatRequest, ChatResponse
from agents.orchestrator.graph import get_orchestrator_graph
from agents.orchestrator.state import AgentState, OrigenEntrada
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Recibe un mensaje de chat, inicializa el estado del agente orquestador,
    ejecuta el grafo de LangGraph y retorna la respuesta final y las herramientas ejecutadas.
    """
    graph = get_orchestrator_graph()

    session_id = f"chat-{uuid.uuid4()}"
    origen = (
        OrigenEntrada.CHAT_ADMIN
        if request.rol == "administrador"
        else OrigenEntrada.CHAT_ESTUDIANTE
    )

    initial_state = AgentState(
        session_id=session_id,
        origen=origen,
        usuario_id=request.usuario_id,
        rol=request.rol,
        aula_id=request.aula_id,
        messages=[HumanMessage(content=request.message)],
    )

    try:
        # Ejecutar el grafo de orquestación cognitiva
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el mensaje en el orquestador: {str(e)}",
        )

    # Adaptar para manejar si final_state es un diccionario o el objeto de estado
    if isinstance(final_state, dict):
        respuesta = final_state.get("respuesta_final") or "No se obtuvo respuesta."
        tool_executions_list = final_state.get("tool_executions", [])
    else:
        respuesta = getattr(final_state, "respuesta_final", "No se obtuvo respuesta.")
        tool_executions_list = getattr(final_state, "tool_executions", [])

    # Formatear el historial de ejecuciones de herramientas
    executions = []
    for exec_record in tool_executions_list:
        executions.append({
            "plugin_name": getattr(exec_record, "plugin_name", exec_record.get("plugin_name") if isinstance(exec_record, dict) else "desconocido"),
            "success": getattr(exec_record, "success", exec_record.get("success") if isinstance(exec_record, dict) else True),
            "result": getattr(exec_record, "result", exec_record.get("result") if isinstance(exec_record, dict) else {}),
        })

    return ChatResponse(
        session_id=session_id,
        respuesta=respuesta,
        tool_executions=executions,
    )
