from enum import Enum

class AulaEstado(str, Enum):
    CONCENTRADO = "concentrado"
    BREAK = "break"
    AUSENTE = "ausente"

    # Compatibilidad con nombres usados antes de formalizar el dominio.
    ATENTO = "concentrado"
    DISTRAIDO = "break"

    @classmethod
    def _missing_(cls, value):
        aliases = {
            "atento": cls.CONCENTRADO,
            "distraido": cls.BREAK,
            "distraído": cls.BREAK,
            "descanso": cls.BREAK,
            "reposo": cls.AUSENTE,
        }
        if isinstance(value, str):
            return aliases.get(value.lower())
        return None

class OrigenEntrada(str, Enum):
    CHAT_ESTUDIANTE = "chat_estudiante"
    CHAT_ADMIN = "chat_admin"
    VISION_EVENT = "vision_event"

class PluginBeneficiario(str, Enum):
    ESTUDIANTE = "estudiante"
    ADMINISTRADOR = "administrador"
    AMBOS = "ambos"
