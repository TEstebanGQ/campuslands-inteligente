from __future__ import annotations

import os
import hashlib
import numpy as np

class EmbeddingEngine:
    """
    Genera embeddings deterministas para imágenes.
    Para la simulación, si el nombre del archivo contiene palabras clave
    como 'concentrado' / 'atento', 'break' / 'distraído', o 'ausente',
    genera un vector muy cercano a los centroides correspondientes para
    garantizar reproducibilidad.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def get_embedding(self, image_path: str) -> np.ndarray:
        filename = os.path.basename(image_path).lower()

        # Determinar el seed base según el estado indicado en el nombre de archivo
        if "concentrado" in filename or "atento" in filename:
            seed = 100
        elif "break" in filename or "distraido" in filename or "distraído" in filename:
            seed = 200
        elif "ausente" in filename:
            seed = 300
        else:
            # Si no tiene palabra clave, usar un hash del nombre del archivo
            hasher = hashlib.md5(filename.encode("utf-8"))
            seed = int(hasher.hexdigest(), 16) % 1000

        # Generar un vector unitario usando el seed determinado
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(self.dimension).astype(np.float32)
        
        # Añadir un leve ruido si es un archivo de frame específico para simular variación
        file_hash = int(hashlib.md5(image_path.encode("utf-8")).hexdigest(), 16) % 100
        rng_noise = np.random.default_rng(file_hash)
        noise = rng_noise.standard_normal(self.dimension).astype(np.float32) * 0.05
        
        vector = vector + noise
        
        # Normalizar
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector
