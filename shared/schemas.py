"""
shared/schemas.py

Contratos de datos Pydantic v2 compartidos entre Agente 1 (Visión),
Agente 2 (Orquestador) y la capa de Plugins. Congelado en la Hora 0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional
from uuid import uuid4

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field

from shared.enums import AulaEstado, NivelRiesgo, OrigenEntrada, TendenciaAcademica


class VisionEvent(BaseModel):
    """Evento emitido por el Agente 1 hacia el EventBus tras clasificar un frame."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    aula_id: str
    estudiante_id: Optional[str] = None
    estado: AulaEstado
    confidence: float = Field(ge=0.0, le=1.0)
    frame_path: str
    sample_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudentProfile(BaseModel):
    """Representación canónica de un estudiante para cruce de datos."""

    model_config = ConfigDict(frozen=True)

    estudiante_id: str
    nombre: str
    promedio_notas_historico: list[float] = Field(default_factory=list)
    tendencia_declarada: TendenciaAcademica = TendenciaAcademica.ESTABLE
    porcentaje_asistencia: Optional[float] = None
    nivel_riesgo: Optional[NivelRiesgo] = None


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
    """Estado completo que fluye a través del StateGraph de LangGraph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    origen: OrigenEntrada

    usuario_id: Optional[str] = None
    rol: Optional[str] = None

    vision_event_id: Optional[str] = None
    aula_id: Optional[str] = None

    # Aquí es donde hacían falta AnyMessage y add_messages
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)

    tool_calls_pendientes: list[dict[str, Any]] = Field(default_factory=list)
    tool_executions: list[ToolExecutionRecord] = Field(default_factory=list)

    respuesta_final: Optional[str] = None
    requiere_notificacion_proactiva: bool = False

    def registrar_ejecucion(self, record: ToolExecutionRecord) -> None:
        self.tool_executions.append(record)