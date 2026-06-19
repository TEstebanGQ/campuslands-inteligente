from __future__ import annotations

import imghdr
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from agents.vision.pipeline import VisionPipeline

router = APIRouter(prefix="/vision", tags=["vision"])

FRAMES_DIR = Path("simulation/frames")
_AULA_PATTERN = re.compile(r"aula_?(\d+)", re.IGNORECASE)


def _extraer_aula_id(filename: str) -> str:
    match = _AULA_PATTERN.search(filename)
    return match.group(1) if match else "desconocida"


@router.post("/process-frames")
async def process_frames() -> dict[str, Any]:
    """
    Procesa cada imagen en simulation/frames/ a través del VisionPipeline:
    genera embedding, clasifica el estado, persiste en FiftyOne y publica
    el VisionEvent resultante en el EventBus para que el orquestador reaccione.
    """
    if not FRAMES_DIR.exists():
        raise HTTPException(status_code=404, detail=f"No existe el directorio {FRAMES_DIR}")

    candidates = sorted(
        p for p in FRAMES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    frame_paths = [p for p in candidates if imghdr.what(p) in {"jpeg", "png"}]
    if not frame_paths:
        raise HTTPException(status_code=404, detail="No hay frames para procesar")

    pipeline = VisionPipeline()
    eventos = []
    for frame_path in frame_paths:
        aula_id = _extraer_aula_id(frame_path.name)
        event = await pipeline.process_frame(str(frame_path), aula_id)
        eventos.append({
            "id": event.id,
            "frame": frame_path.name,
            "aula_id": event.aula_id,
            "estado": event.estado,
            "confidence": round(event.confidence, 3),
            "timestamp": event.timestamp.isoformat(),
        })

    return {
        "total_procesados": len(eventos),
        "total_omitidos": len(candidates) - len(frame_paths),
        "eventos": eventos,
    }
