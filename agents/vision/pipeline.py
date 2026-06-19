from __future__ import annotations

import uuid
from datetime import datetime, timezone
from shared.schemas import VisionEvent
from agents.vision.embedding_engine import EmbeddingEngine
from agents.vision.classifier import LightweightStateClassifier
from core.fiftyone_manager import get_fiftyone_manager
from core.event_bus import get_event_bus

class VisionPipeline:
    """
    Orquesta el flujo del Agente 1 (Vision & Data Curator):
    Recibe un frame, genera su embedding, clasifica el estado,
    lo registra en FiftyOne y publica el evento correspondiente.
    """

    def __init__(self) -> None:
        self.embedding_engine = EmbeddingEngine()
        self.classifier = LightweightStateClassifier()
        self.fiftyone_manager = get_fiftyone_manager()
        self.event_bus = get_event_bus()

    async def process_frame(
        self, frame_path: str, aula_id: str, estudiante_id: str | None = None
    ) -> VisionEvent:
        # 1. Generación de embedding
        embedding = self.embedding_engine.get_embedding(frame_path)

        # 2. Clasificación contra centroides
        estado, confidence = self.classifier.classify(embedding)

        # 3. Persistencia en FiftyOne (Dashboard Administrador)
        await self.fiftyone_manager.persist_frame(
            frame_path=frame_path,
            embedding=embedding,
            estado=estado,
            confidence=confidence,
            aula_id=aula_id
        )

        # 4. Publicación en el bus de eventos in-process
        event = VisionEvent(
            id=str(uuid.uuid4()),
            aula_id=aula_id,
            estado=estado,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
            estudiante_id=estudiante_id,
        )
        await self.event_bus.publish(event)

        return event
