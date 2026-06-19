from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shared.enums import AulaEstado
from agents.vision.pipeline import VisionPipeline

router = APIRouter(prefix="/simulate", tags=["simulation"])


class SimulationRequest(BaseModel):
    aula_id: str
    estado_visual: AulaEstado
    estudiante_id: str = "estudiante_1"


@router.post("")
async def run_simulation_event(request: SimulationRequest) -> dict:
    """
    Simula la captura física de una cámara de aula. Crea una imagen simulada,
    ejecuta el Pipeline de Visión (Agente 1) y transmite el evento en el EventBus.
    """
    frames_dir = Path("simulation/frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Crear el archivo con el estado visual en el nombre para el motor de embeddings
    filename = f"{request.estado_visual.value}_aula_{request.aula_id}.jpg"
    frame_path = frames_dir / filename

    try:
        # Escribir contenido simulado
        frame_path.write_bytes(b"mock camera capture frame content")

        # Procesar en el Pipeline de Visión (Agente 1)
        pipeline = VisionPipeline()
        event = await pipeline.process_frame(str(frame_path), request.aula_id)

        return {
            "success": True,
            "event_id": event.id,
            "aula_id": event.aula_id,
            "estado": event.estado.value,
            "confidence": event.confidence,
            "message": f"Cámara de aula {request.aula_id} simulada exitosamente en estado '{request.estado_visual.value}'.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fallo en la simulación del frame: {str(e)}",
        )
