from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from shared.enums import AulaEstado, OrigenEntrada

class VisionEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique event identifier")
    aula_id: str = Field(..., description="Classroom identifier")
    estado: AulaEstado = Field(..., description="Classroom visual state")
    confidence: float = Field(..., description="Classification confidence (0 to 1)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estudiante_id: Optional[str] = Field(
        default=None,
        description="Student identifier associated with the visual event, when available",
    )

class ClassificationResult(BaseModel):
    estado: AulaEstado
    confidence: float

class ChatRequest(BaseModel):
    message: str
    usuario_id: Optional[str] = None
    rol: Optional[str] = "estudiante"  # "estudiante" | "administrador"
    aula_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    respuesta: str
    tool_executions: list[dict[str, Any]] = Field(default_factory=list)
