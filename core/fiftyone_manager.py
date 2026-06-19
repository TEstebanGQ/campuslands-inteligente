from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import fiftyone as fo
import numpy as np

from shared.config import get_settings
from shared.enums import AulaEstado
from shared.schemas import VisionEvent

logger = logging.getLogger("campuslands.fiftyone_manager")


class FiftyOneDatasetManager:
    """
    Encapsula la creación, persistencia y exposición del dataset de
    FiftyOne usado como dashboard de auditoría visual por el administrador.

    Esta clase se instancia una única vez como singleton durante el
    startup de FastAPI y se inyecta donde se necesite vía `api/deps.py`.
    """

    DATASET_NAME = "campuslands_aulas"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._dataset: Optional[fo.Dataset] = None
        self._session: Optional[fo.Session] = None
        self._write_lock = asyncio.Lock()

    def _get_or_create_dataset(self) -> fo.Dataset:
        if fo.dataset_exists(self.DATASET_NAME):
            dataset = fo.load_dataset(self.DATASET_NAME)
        else:
            dataset = fo.Dataset(self.DATASET_NAME)
            dataset.persistent = True
        return dataset

    async def startup(self) -> None:
        """
        Debe invocarse desde el evento de lifespan de FastAPI.

        Lanza la app de FiftyOne en modo NO bloqueante: `auto=False`
        evita que FiftyOne intente abrir un navegador y, sobre todo,
        evita cualquier llamada interna equivalente a `session.wait(-1)`.
        El control regresa de inmediato al event loop de FastAPI.
        """
        loop = asyncio.get_running_loop()

        def _init_sync() -> tuple[fo.Dataset, fo.Session]:
            dataset = self._get_or_create_dataset()
            session = fo.launch_app(
                dataset,
                port=self._settings.fiftyone_port,
                address=self._settings.fiftyone_host,
                auto=False,
            )
            return dataset, session

        self._dataset, self._session = await loop.run_in_executor(None, _init_sync)
        logger.info(
            "FiftyOne dataset '%s' listo en puerto %s (modo no bloqueante)",
            self.DATASET_NAME,
            self._settings.fiftyone_port,
        )

    async def shutdown(self) -> None:
        """Cierre ordenado de la sesión de FiftyOne durante el shutdown de FastAPI."""
        if self._session is not None:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._session.close)
            logger.info("Sesión de FiftyOne cerrada correctamente")

    async def persist_frame(
        self,
        *,
        frame_path: str,
        embedding: np.ndarray,
        estado: AulaEstado,
        confidence: float,
        aula_id: str,
        captured_at: Optional[datetime] = None,
    ) -> str:
        """
        Persiste un frame clasificado en el dataset, protegido con un
        lock asíncrono para evitar condiciones de carrera si múltiples
        frames se procesan concurrentemente.

        Retorna el `sample_id` generado por FiftyOne.
        """
        captured_at = captured_at or datetime.now(timezone.utc)

        async with self._write_lock:
            loop = asyncio.get_running_loop()

            def _add_sample_sync() -> str:
                sample = fo.Sample(filepath=frame_path)
                sample["aula_id"] = aula_id
                sample["estado"] = estado.value
                sample["confidence"] = float(confidence)
                sample["captured_at"] = captured_at.isoformat()
                sample["embedding"] = embedding.tolist()
                self._dataset.add_sample(sample)
                self._dataset.save()
                return sample.id

            sample_id = await loop.run_in_executor(None, _add_sample_sync)

        logger.debug(
            "Frame persistido en FiftyOne: aula=%s estado=%s confidence=%.3f sample_id=%s",
            aula_id,
            estado.value,
            confidence,
            sample_id,
        )
        return sample_id

    def get_dataset_summary(self) -> dict:
        """
        Resumen agregado del dataset para exponer en `/api/v1/admin/dashboard`.
        Operación de solo lectura, segura de invocar sin lock.
        """
        if self._dataset is None:
            return {"total_samples": 0, "por_estado": {}}

        counts = self._dataset.count_values("estado")
        return {
            "total_samples": len(self._dataset),
            "por_estado": counts,
            "app_url": self._session.url if self._session else None,
        }


_manager_singleton: Optional[FiftyOneDatasetManager] = None


def get_fiftyone_manager() -> FiftyOneDatasetManager:
    """Provee el singleton del manager para inyección de dependencias en FastAPI."""
    global _manager_singleton
    if _manager_singleton is None:
        _manager_singleton = FiftyOneDatasetManager()
    return _manager_singleton
