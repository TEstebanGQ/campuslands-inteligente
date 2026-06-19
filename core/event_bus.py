import asyncio
from typing import AsyncGenerator, Set, Optional
from shared.schemas import VisionEvent

class EventBus:
    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()

    async def publish(self, event: VisionEvent) -> None:
        for queue in list(self._subscribers):
            await queue.put(event)

    async def subscribe(self) -> AsyncGenerator[VisionEvent, None]:
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._subscribers.remove(queue)

_event_bus_singleton: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    global _event_bus_singleton
    if _event_bus_singleton is None:
        _event_bus_singleton = EventBus()
    return _event_bus_singleton
