from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from core.persistence import InMemoryKeyValueStore
from plugins.base import BasePlugin

class SpaceOptimizerPlugin(BasePlugin):
    name = "space_optimizer"

    async def execute(
        self, *, aula_id: str, ocupacion_actual: int, capacidad_maxima: int
    ) -> dict[str, Any]:
        if capacidad_maxima <= 0:
            capacidad_maxima = 1

        tasa_actual = ocupacion_actual / capacidad_maxima

        # Fetch historical readings for smoothing
        history_record = await InMemoryKeyValueStore.get("ocupacion_historica", aula_id)
        if history_record is None:
            readings = []
        else:
            readings = history_record.get("readings", [])

        # Add new reading and limit historical tracking to last 5 entries
        readings.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ocupacion": ocupacion_actual,
            "capacidad": capacidad_maxima,
            "tasa": tasa_actual
        })
        readings = readings[-5:]

        await InMemoryKeyValueStore.set("ocupacion_historica", aula_id, {"readings": readings})

        # Calculate average utilization
        avg_tasa = sum(r["tasa"] for r in readings) / len(readings)

        # Decide action based on thresholds
        requiere_accion = False
        if avg_tasa < 0.30:
            recomendacion = (
                f"La tasa de utilización promedio es de {avg_tasa * 100:.1f}%. "
                f"Se recomienda reasignar el aula {aula_id} a un grupo más pequeño o consolidar clases."
            )
            requiere_accion = True
        elif avg_tasa > 0.90:
            recomendacion = (
                f"La tasa de utilización promedio es de {avg_tasa * 100:.1f}%. "
                f"Se recomienda reubicar el grupo a un aula de mayor capacidad."
            )
            requiere_accion = True
        else:
            recomendacion = (
                f"La tasa de utilización promedio es de {avg_tasa * 100:.1f}%. "
                f"El espacio físico del aula {aula_id} está óptimamente utilizado."
            )

        return {
            "aula_id": aula_id,
            "tasa_utilizacion": round(avg_tasa, 3),
            "recomendacion": recomendacion,
            "requiere_accion": requiere_accion
        }
