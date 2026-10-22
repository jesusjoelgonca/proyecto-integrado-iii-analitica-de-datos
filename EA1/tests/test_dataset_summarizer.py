"""
test_dataset_summarizer.py
==========================
Pruebas de DatasetSummarizer con un DataFrame sintetico (sin red).
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.dataset_summarizer import DatasetSummarizer  # noqa: E402


def _frame_con_problemas() -> pd.DataFrame:
    """DataFrame con nulos, un duplicado y una columna de texto."""
    return pd.DataFrame(
        {
            "largo_petalo_cm": [1.4, 4.7, 4.7, None, 6.9],
            "ancho_petalo_cm": [0.2, 1.4, 1.4, 1.5, 2.5],
            "especie": ["setosa", "versicolor", "versicolor", "virginica", "virginica"],
        }
    )


class DatasetSummarizerTest(unittest.TestCase):
    def setUp(self):
        self.frame = _frame_con_problemas()
        self.resumen = DatasetSummarizer(self.frame, nombre="Prueba")

    def test_summary_cuenta_filas_y_columnas(self):
        datos = self.resumen.summary()

        self.assertEqual(datos["filas"], 5)
        self.assertEqual(datos["columnas"], 3)
        self.assertEqual(datos["duplicados"], 1)
        self.assertEqual(datos["columnas_con_nulos"], ["largo_petalo_cm"])

    def test_detalle_de_columnas_incluye_tipos_y_nulos(self):
        detalle = {columna["columna"]: columna for columna in self.resumen.summary()["columnas_detalle"]}

        self.assertEqual(detalle["largo_petalo_cm"]["nulos"], 1)
        self.assertEqual(detalle["largo_petalo_cm"]["no_nulos"], 4)
        self.assertAlmostEqual(detalle["largo_petalo_cm"]["nulos_pct"], 20.0)
        self.assertEqual(detalle["especie"]["tipo"], str(self.frame["especie"].dtype))

    def test_texto_contiene_las_secciones_esperadas(self):
        texto = self.resumen.to_text()

        for seccion in (
            "RESUMEN DEL DATASET",
            "1. DIMENSIONES",
            "2. COLUMNAS Y TIPOS",
            "3. VALORES NULOS",
            "4. ESTADISTICAS DESCRIPTIVAS",
            "5. VARIABLES CATEGORICAS",
        ):
            self.assertIn(seccion, texto)

        self.assertIn("largo_petalo_cm", texto)
        self.assertIn("20.00 %", texto)
        self.assertIn("setosa", texto)

    def test_texto_sin_nulos_lo_indica(self):
        limpio = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        texto = DatasetSummarizer(limpio).to_text()

        self.assertIn("Sin valores nulos", texto)

    def test_save_escribe_el_archivo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "sub" / "resumen.txt"
            ruta = self.resumen.save(destino)

            self.assertTrue(ruta.exists())
            self.assertEqual(ruta, destino)
            contenido = ruta.read_text(encoding="utf-8")
            self.assertIn("RESUMEN DEL DATASET", contenido)
            self.assertIn("Fin del resumen", contenido)

    def test_no_deja_espacios_al_final_de_linea(self):
        texto = self.resumen.to_text()

        for linea in texto.splitlines():
            self.assertEqual(linea, linea.rstrip(), f"linea con espacios finales: {linea!r}")

    def test_rechaza_lo_que_no_es_dataframe(self):
        with self.assertRaises(TypeError):
            DatasetSummarizer([1, 2, 3])

    def test_rechaza_dataframe_vacio(self):
        with self.assertRaises(ValueError):
            DatasetSummarizer(pd.DataFrame())


if __name__ == "__main__":
    unittest.main()
