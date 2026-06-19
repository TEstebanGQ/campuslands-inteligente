from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """
    Contrato mínimo de un plugin de negocio.

    Cada plugin es responsable de:
    - Validar sus propios argumentos de entrada.
    - Ejecutar su lógica de negocio de forma idempotente cuando aplique.
    - Persistir o leer su propio estado (SQLite in-memory o dict global
      con asyncio.Lock), sin depender del estado interno de otro plugin.
    - Retornar siempre un diccionario serializable a JSON.
    """

    #: Nombre identificador único del plugin, usado en logs y trazas.
    name: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Punto de entrada único de ejecución del plugin.
        Debe ser async para no bloquear el event loop de FastAPI,
        incluso si la lógica interna es trivial.
        """
        raise NotImplementedError

    async def health_check(self) -> bool:
        """
        Verificación rápida de que el plugin está operativo
        (por ejemplo, que su conexión SQLite in-memory responde).
        Por defecto se asume saludable; los plugins pueden sobreescribirlo.
        """
        return True
