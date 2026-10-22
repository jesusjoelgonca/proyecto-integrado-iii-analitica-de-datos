"""
config.py
=========
Parametros de la Evidencia de Aprendizaje 1 en un unico lugar.

Todo el proyecto (cuaderno, pruebas y clases) lee de aqui: el identificador del
dataset, el split y las rutas de salida. Cambiar de dataset no requiere tocar
el codigo, solo este archivo.

Autor: Jesus Gonzalez
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --- Rutas ------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parents[1]  # carpeta EA1/
REPORTS_DIR = PROJECT_DIR / "reports"

# Nombre del archivo de resumen que produce DatasetSummarizer
SUMMARY_FILENAME = "resumen_dataset_transformado.txt"


# --- Origen de los datos ----------------------------------------------------
@dataclass(frozen=True)
class DatasetTarget:
    """Dataset de Hugging Face que se analiza en la actividad."""

    dataset_id: str = "scikit-learn/iris"
    split: str = "train"
    config_name: str | None = None
    descripcion: str = "Medidas morfologicas de 150 flores de tres especies de Iris."

    def __str__(self) -> str:
        origen = self.dataset_id
        if self.config_name:
            origen = f"{origen} ({self.config_name})"
        return f"{origen} · split={self.split}"


TARGET = DatasetTarget()
