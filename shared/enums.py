from enum import Enum

class AulaEstado(str, Enum):
    ATENTO = "atento"
    DISTRAIDO = "distraído"
    AUSENTE = "ausente"

class OrigenEntrada(str, Enum):
    CHAT_ESTUDIANTE = "chat_estudiante"
    CHAT_ADMIN = "chat_admin"
    VISION_EVENT = "vision_event"

class PluginBeneficiario(str, Enum):
    ESTUDIANTE = "estudiante"
    ADMINISTRADOR = "administrador"
    AMBOS = "ambos"
