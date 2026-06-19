# test_pipeline.py
import asyncio
from agents.vision.pipeline import VisionPipeline
from core.fiftyone_manager import get_fiftyone_manager

async def main():
    # Primero inicializar FiftyOne
    fo_manager = get_fiftyone_manager()
    await fo_manager.startup()
    print("✅ FiftyOne iniciado")

    pipeline = VisionPipeline()
    
    frames = [
        ("simulation/frames/atento_aula_304.jpg", "aula_304"),
        ("simulation/frames/ausente_aula_304.jpg", "aula_304"),
        ("simulation/frames/distraido_aula_304.jpg", "aula_304"),
    ]
    
    for frame_path, aula_id in frames:
        event = await pipeline.process_frame(frame_path=frame_path, aula_id=aula_id)
        print(f"🖼️  Frame: {frame_path}")
        print(f"   ✅ Estado: {event.estado}")
        print(f"   ✅ Confidence: {event.confidence:.3f}")
        print(f"   ✅ Event ID: {event.id}")
        print()

asyncio.run(main())