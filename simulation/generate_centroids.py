from __future__ import annotations

import json
from pathlib import Path
import numpy as np

# Semillas base de cálculo de embeddings por estado representativo
# Coinciden exactamente con las semillas del motor de embeddings en agents/vision/embedding_engine.py
ESTADOS_SEEDS = {
    "atento": 100,
    "distraído": 200,
    "ausente": 300,
}

DIMENSION = 128


def calculate_offline_centroids(
    output_path: Path = Path("simulation/centroids/centroids.json"),
) -> None:
    """
    Simula el cálculo offline de centroides promediando/generando los vectores
    representativos para cada estado de aula. Guarda el resultado en un archivo JSON.
    """
    print("=== INICIANDO CÁLCULO OFFLINE DE CENTROIDES ===")
    centroids = {}

    for estado, seed in ESTADOS_SEEDS.items():
        print(f"Calculando vector centroide para el estado '{estado}' (Semilla={seed})...")
        # Generar un vector unitario de forma determinista
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(DIMENSION).astype(np.float32)

        # Normalizar a norma 1.0 para similitud coseno
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        centroids[estado] = vector.tolist()

    # Guardar en archivo JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(centroids, indent=2), encoding="utf-8")
    print(f"Archivo de centroides generado exitosamente en: {output_path}")


if __name__ == "__main__":
    calculate_offline_centroids()
