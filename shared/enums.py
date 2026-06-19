"""
shared/enums.py

Enumeraciones compartidas por todo el sistema. Congelado en la Hora 0.
Ningún módulo redefine estos valores localmente.
"""

from __future__ import annotations

from enum import Enum


class AulaEstado(str, Enum):
    ATENTO = "atento"
    DISTRAIDO = "distraído"
    AUSENTE = "ausente"


class OrigenEntrada(str, Enum):
    CHAT_ESTUDIANTE = "chat_estudiante"
    CHAT_ADMIN = "chat_admin"
    VISION_EVENT = "vision_event"


class NivelRiesgo(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class TendenciaAcademica(str, Enum):
    MEJORA = "mejora"
    ESTABLE = "estable"
    DECLIVE = "declive"


class TipoAlerta(str, Enum):
    POSIBLE_DESERCION_SESION = "posible_desercion_sesion"
    BAJA_ATENCION_GRUPAL = "baja_atencion_grupal"


class RolUsuario(str, Enum):
    ESTUDIANTE = "estudiante"
    ADMINISTRADOR = "administrador"