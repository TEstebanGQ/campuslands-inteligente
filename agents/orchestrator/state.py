from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field


class OrigenEntrada(str, Enum):
    CHAT_ESTUDIANTE = "chat_estudiante"
    CHAT_ADMIN = "chat_admin"
    VISION_EVENT = "vision_event"


class ToolExecutionRecord(BaseModel):
    """Traza de cada invocación de plugin dentro de un turno del grafo."""

    model_config = ConfigDict(frozen=True)

    plugin_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error_message: Optional[str] = None


class AgentState(BaseModel):
    """
    Estado completo que fluye a través del StateGraph de LangGraph.

    `messages` usa el reducer `add_messages` de LangGraph para
    acumular el historial de la conversación turno a turno, en lugar
    de sobreescribirlo en cada nodo.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- Identificación del turno ---
    session_id: str
    origen: OrigenEntrada

    # --- Contexto del solicitante (si aplica) ---
    usuario_id: Optional[str] = None
    rol: Optional[str] = None  # "estudiante" | "administrador"

    # --- Contexto del evento de visión (si aplica) ---
    vision_event_id: Optional[str] = None
    aula_id: Optional[str] = None

    # --- Conversación (historial acumulativo vía reducer) ---
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)

    # --- Resultado del enrutamiento de herramientas ---
    tool_calls_pendientes: list[dict[str, Any]] = Field(default_factory=list)
    tool_executions: list[ToolExecutionRecord] = Field(default_factory=list)

    # --- Salida final del turno ---
    respuesta_final: Optional[str] = None
    requiere_notificacion_proactiva: bool = False

    def registrar_ejecucion(self, record: ToolExecutionRecord) -> None:
        self.tool_executions.append(record)
