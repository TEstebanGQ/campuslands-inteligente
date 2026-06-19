from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shared.enums import AulaEstado
from agents.vision.pipeline import VisionPipeline

router = APIRouter(prefix="/simulate", tags=["simulation"])

FRAME_TEMPLATES = {
    AulaEstado.CONCENTRADO: "simulation/frames/atento_aula_304.png",
    AulaEstado.BREAK: "simulation/frames/distraido_aula305.jpg",
    AulaEstado.AUSENTE: "simulation/frames/ausente_aula_304.png",
}


class SimulationRequest(BaseModel):
    aula_id: str
    estado_visual: AulaEstado
    estudiante_id: str = "estudiante_1"


@router.post("")
async def run_simulation_event(request: SimulationRequest) -> dict:
    """
    Simula la captura física de una cámara de aula usando una de las tres
    imágenes válidas de referencia, ejecuta el Pipeline de Visión (Agente 1)
    y transmite el evento en el EventBus.
    """
    frame_path = FRAME_TEMPLATES[request.estado_visual]

    try:
        # Procesar en el Pipeline de Visión (Agente 1)
        pipeline = VisionPipeline()
        event = await pipeline.process_frame(
            frame_path, request.aula_id, estudiante_id=request.estudiante_id
        )

        return {
            "success": True,
            "event_id": event.id,
            "aula_id": event.aula_id,
            "estado": event.estado.value,
            "confidence": event.confidence,
            "frame": frame_path,
            "estudiante_id": event.estudiante_id,
            "message": f"Cámara de aula {request.aula_id} simulada exitosamente en estado de aula '{event.estado.value}'.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fallo en la simulación del frame: {str(e)}",
        )
