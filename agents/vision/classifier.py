from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from shared.enums import AulaEstado

CENTROIDS_PATH = Path("simulation/centroids/centroids.json")


class LightweightStateClassifier:
    """
    Carga centroides precalculados (uno por estado de aula) y clasifica
    embeddings entrantes contra ellos usando similitud de coseno.
    """

    def __init__(self, centroids_path: Path = CENTROIDS_PATH) -> None:
        if not centroids_path.exists():
            centroids_path.parent.mkdir(parents=True, exist_ok=True)
            # Generar vectores base deterministas de prueba (dimensión 128)
            rng_concentrado = np.random.default_rng(100)
            v_concentrado = rng_concentrado.standard_normal(128).astype(np.float32)
            v_concentrado = v_concentrado / np.linalg.norm(v_concentrado)

            rng_break = np.random.default_rng(200)
            v_break = rng_break.standard_normal(128).astype(np.float32)
            v_break = v_break / np.linalg.norm(v_break)

            rng_ausente = np.random.default_rng(300)
            v_ausente = rng_ausente.standard_normal(128).astype(np.float32)
            v_ausente = v_ausente / np.linalg.norm(v_ausente)

            centroids = {
                "concentrado": v_concentrado.tolist(),
                "break": v_break.tolist(),
                "ausente": v_ausente.tolist()
            }
            centroids_path.write_text(json.dumps(centroids, indent=2), encoding="utf-8")

        raw = json.loads(centroids_path.read_text(encoding="utf-8"))
        self._labels: list[AulaEstado] = []
        vectors: list[list[float]] = []
        for estado_str, vector in raw.items():
            self._labels.append(AulaEstado(estado_str))
            vectors.append(vector)
        self._centroids = np.array(vectors, dtype=np.float32)
        self._centroid_norms = np.linalg.norm(self._centroids, axis=1)

    def classify(self, embedding: np.ndarray) -> tuple[AulaEstado, float]:
        """
        Retorna (estado_clasificado, confianza) donde confianza está
        normalizada en [0, 1] a partir de la similitud de coseno con
        el centroide más cercano.
        """
        emb_norm = np.linalg.norm(embedding)
        if emb_norm == 0:
            return AulaEstado.AUSENTE, 0.0

        similarities = (self._centroids @ embedding) / (
            self._centroid_norms * emb_norm + 1e-8
        )
        best_idx = int(np.argmax(similarities))
        confidence = float((similarities[best_idx] + 1.0) / 2.0)  # mapea [-1,1] -> [0,1]
        return self._labels[best_idx], confidence
