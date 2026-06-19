from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.fiftyone_manager import get_fiftyone_manager
from core.event_bus import get_event_bus
from core.persistence import init_db
from agents.orchestrator.graph import start_event_listener
from api.routes import chat, admin, simulate
from fastapi.responses import FileResponse, HTMLResponse
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Inicializar las tablas de SQLite in-memory
    await init_db()

    # Iniciar FiftyOne de forma no bloqueante
    fo_manager = get_fiftyone_manager()
    await fo_manager.startup()

    # Suscribir el orquestador cognitivo al bus de eventos de visión
    event_bus = get_event_bus()
    listener_task = asyncio.create_task(start_event_listener(event_bus))

    yield

    # --- Shutdown ---
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    await fo_manager.shutdown()


app = FastAPI(title="Campuslands Inteligente", lifespan=lifespan)

# Incluir routers bajo el prefijo /api/v1
app.include_router(chat.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(simulate.router, prefix="/api/v1")


@app.get("/")
def read_root():
    static_file = "static/index.html"
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return HTMLResponse("<h1>Campuslands Inteligente</h1><p>Archivo static/index.html no encontrado.</p>")
