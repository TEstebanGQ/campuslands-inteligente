from core.fiftyone_manager import get_fiftyone_manager, FiftyOneDatasetManager
from core.event_bus import get_event_bus, EventBus
from core.persistence import get_sqlite_engine
from sqlalchemy.ext.asyncio import AsyncEngine

def get_fo_manager_dep() -> FiftyOneDatasetManager:
    return get_fiftyone_manager()

def get_event_bus_dep() -> EventBus:
    return get_event_bus()

def get_db_dep() -> AsyncEngine:
    return get_sqlite_engine()
