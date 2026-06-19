from __future__ import annotations

from typing import Any
from core.persistence import InMemoryKeyValueStore
from plugins.base import BasePlugin

class SpaceOptimizerPlugin(BasePlugin):
    name = "space_optimizer"
    MAX_HISTORICAL_READINGS = 10

    async def execute(
        self, *, aula_id: str, ocupacion_actual: int, capacidad_maxima: int
    ) -> dict[str, Any]:
        if capacidad_maxima <= 0:
            capacidad_maxima = 1

        tasa_actual = ocupacion_actual / capacidad_maxima

        history_record = await InMemoryKeyValueStore.get("ocupacion_historica", aula_id)
        tasas = []
        if history_record is not None:
            tasas = history_record.get("tasas", [])

        tasas.append(tasa_actual)
        tasas = tasas[-self.MAX_HISTORICAL_READINGS:]

        await InMemoryKeyValueStore.set("ocupacion_historica", aula_id, {"tasas": tasas})

        promedio_tasa = sum(tasas) / len(tasas)

        if promedio_tasa < 0.30:
            recomendacion = "reasignar_espacio_menor"
        elif promedio_tasa > 0.90:
            recomendacion = "evaluar_reubicacion_mayor_capacidad"
        else:
            recomendacion = "sin_accion_requerida"

        return {
            "aula_id": aula_id,
            "tasa_utilizacion": round(promedio_tasa, 3),
            "tasa_actual": round(tasa_actual, 3),
            "lecturas_acumuladas": len(tasas),
            "recomendacion": recomendacion,
            "requiere_accion": recomendacion != "sin_accion_requerida"
        }
