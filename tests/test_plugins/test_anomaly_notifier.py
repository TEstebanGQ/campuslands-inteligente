from __future__ import annotations

import pytest
from core.persistence import InMemoryKeyValueStore
from plugins.anomaly_notifier import AnomalyNotifierPlugin


@pytest.mark.asyncio
async def test_anomaly_notifier_cooldown_and_thresholds():
    """
    Prueba que el plugin de notificaciones de anomalías:
    - No dispare alerta si no se supera el umbral de tiempo.
    - Genere alerta si se supera el umbral de tiempo.
    - Suprima alertas subsecuentes si se está dentro de la ventana de cooldown de 10 minutos.
    """
    # 1. Resetear el almacenamiento KV para el aula de prueba "999"
    await InMemoryKeyValueStore.set("anomalias", "999:posible_desercion_sesion", None)

    plugin = AnomalyNotifierPlugin()

    # 2. Probar bajo el umbral de ausencia (10 minutos < umbral de 15 minutos)
    res_bajo_umbral = await plugin.execute(
        aula_id="999", estado_visual="ausente", duracion_minutos=10
    )
    assert res_bajo_umbral["alerta_generada"] is False
    assert res_bajo_umbral["tipo_alerta"] is None

    # 3. Probar sobre el umbral (20 minutos > umbral de 15 minutos) -> Debe generar alerta
    res_alerta = await plugin.execute(
        aula_id="999", estado_visual="ausente", duracion_minutos=20
    )
    assert res_alerta["alerta_generada"] is True
    assert res_alerta["tipo_alerta"] == "posible_desercion_sesion"
    assert "posible deserción" in res_alerta["mensaje"].lower()

    # 4. Probar supresión por cooldown (segunda llamada idéntica de inmediato)
    res_suprimida = await plugin.execute(
        aula_id="999", estado_visual="ausente", duracion_minutos=20
    )
    assert res_suprimida["alerta_generada"] is False
    assert res_suprimida["tipo_alerta"] == "posible_desercion_sesion"
    assert "suprimida por cooldown activo" in res_suprimida["mensaje"].lower()
