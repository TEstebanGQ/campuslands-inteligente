from __future__ import annotations

import pytest

from core.persistence import InMemoryKeyValueStore
from plugins.space_optimizer import SpaceOptimizerPlugin


@pytest.mark.asyncio
async def test_space_optimizer_uses_accumulated_average_for_recommendation() -> None:
    plugin = SpaceOptimizerPlugin()
    aula_id = "space_optimizer_average_1"

    await InMemoryKeyValueStore.set("ocupacion_historica", aula_id, {"tasas": []})

    first_result = await plugin.execute(
        aula_id=aula_id,
        ocupacion_actual=2,
        capacidad_maxima=20,
    )
    second_result = await plugin.execute(
        aula_id=aula_id,
        ocupacion_actual=20,
        capacidad_maxima=20,
    )

    history = await InMemoryKeyValueStore.get("ocupacion_historica", aula_id)

    assert first_result["recomendacion"] == "reasignar_espacio_menor"
    assert second_result["tasa_actual"] == 1.0
    assert second_result["tasa_utilizacion"] == 0.55
    assert second_result["recomendacion"] == "sin_accion_requerida"
    assert history == {"tasas": [0.1, 1.0]}
