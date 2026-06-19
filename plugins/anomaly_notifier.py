from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.persistence import InMemoryKeyValueStore
from plugins.base import BasePlugin

_COOLDOWN_MINUTOS = 10
_UMBRAL_AUSENCIA_MIN = 15
_UMBRAL_DISTRACCION_MIN = 20


class AnomalyNotifierPlugin(BasePlugin):
    name = "anomaly_notifier"

    async def execute(
        self, *, aula_id: str, estado_visual: str, duracion_minutos: int
    ) -> dict[str, Any]:
        tipo_alerta = self._evaluar_regla(estado_visual, duracion_minutos)

        if tipo_alerta is None:
            return {
                "alerta_generada": False,
                "tipo_alerta": None,
                "aula_id": aula_id,
                "mensaje": None,
            }

        if await self._en_cooldown(aula_id, tipo_alerta):
            return {
                "alerta_generada": False,
                "tipo_alerta": tipo_alerta,
                "aula_id": aula_id,
                "mensaje": "Alerta suprimida por cooldown activo",
            }

        mensaje = self._construir_mensaje(aula_id, tipo_alerta, duracion_minutos)
        await self._registrar_envio(aula_id, tipo_alerta)

        return {
            "alerta_generada": True,
            "tipo_alerta": tipo_alerta,
            "aula_id": aula_id,
            "mensaje": mensaje,
        }

    @staticmethod
    def _evaluar_regla(estado_visual: str, duracion_minutos: int) -> str | None:
        if estado_visual == "ausente" and duracion_minutos > _UMBRAL_AUSENCIA_MIN:
            return "posible_desercion_sesion"
        if estado_visual == "distraído" and duracion_minutos > _UMBRAL_DISTRACCION_MIN:
            return "baja_atencion_grupal"
        return None

    @staticmethod
    async def _en_cooldown(aula_id: str, tipo_alerta: str) -> bool:
        registro = await InMemoryKeyValueStore.get("anomalias", f"{aula_id}:{tipo_alerta}")
        if registro is None:
            return False
        ultimo_envio = datetime.fromisoformat(registro["enviado_en"])
        minutos_transcurridos = (datetime.now(timezone.utc) - ultimo_envio).total_seconds() / 60
        return minutos_transcurridos < _COOLDOWN_MINUTOS

    @staticmethod
    async def _registrar_envio(aula_id: str, tipo_alerta: str) -> None:
        await InMemoryKeyValueStore.set(
            "anomalias",
            f"{aula_id}:{tipo_alerta}",
            {"enviado_en": datetime.now(timezone.utc).isoformat()},
        )

    @staticmethod
    def _construir_mensaje(aula_id: str, tipo_alerta: str, duracion_minutos: int) -> str:
        if tipo_alerta == "posible_desercion_sesion":
            return (
                f"Aula {aula_id}: ausencia sostenida detectada durante "
                f"{duracion_minutos} minutos. Posible deserción de la sesión actual."
            )
        return (
            f"Aula {aula_id}: nivel de atención grupal bajo sostenido durante "
            f"{duracion_minutos} minutos."
        )
