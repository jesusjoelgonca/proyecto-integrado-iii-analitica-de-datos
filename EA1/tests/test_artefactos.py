"""
test_artefactos.py
==================
Pruebas de los entregables: el resumen .txt debe corresponder al DataFrame
transformado y el cuaderno debe estar ejecutado y sin errores.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.config import SUMMARY_FILENAME, TARGET  # noqa: E402
from src.dataset_summarizer import DatasetSummarizer  # noqa: E402
from src.hf_loader import HFDatasetLoader  # noqa: E402

RESUMEN = RAIZ / "reports" / SUMMARY_FILENAME
CUADERNO = RAIZ / "Gonzalez_Jesus_EA1.ipynb"

# Columnas que solo existen despues de las transformaciones del cuaderno
COLUMNAS_TRANSFORMADAS = (
    "largo_sepalo_cm",
    "ancho_sepalo_cm",
    "largo_petalo_cm",
    "ancho_petalo_cm",
    "especie",
    "area_petalo_cm2",
    "ratio_petalo",
    "area_media_especie",
)


class ResumenTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(RESUMEN.exists(), f"falta el resumen generado: {RESUMEN}")
        self.texto = RESUMEN.read_text(encoding="utf-8")

    def test_el_resumen_no_esta_vacio(self):
        self.assertGreater(RESUMEN.stat().st_size, 800)
        self.assertIn("RESUMEN DEL DATASET", self.texto)

    def test_resume_el_dataframe_transformado(self):
        for columna in COLUMNAS_TRANSFORMADAS:
            self.assertIn(columna, self.texto, f"el resumen no menciona la columna {columna}")

    def test_no_conserva_los_nombres_originales(self):
        for original in ("SepalLengthCm", "PetalWidthCm", "Iris-setosa"):
            self.assertNotIn(original, self.texto, f"el resumen parece describir los datos sin transformar ({original})")

    def test_reporta_menos_filas_que_el_dataset_original(self):
        coincidencia = re.search(r"Filas\s*:\s*(\d+)", self.texto)
        self.assertIsNotNone(coincidencia, "el resumen debe indicar el numero de filas")

        filas = int(coincidencia.group(1))
        self.assertGreater(filas, 0)
        self.assertLess(filas, 150, "el filtro del cuaderno debe reducir las filas del dataset original")

    def test_incluye_la_seccion_de_nulos(self):
        self.assertIn("3. VALORES NULOS", self.texto)


class CuadernoTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CUADERNO.exists(), f"falta el cuaderno: {CUADERNO}")
        self.nb = json.loads(CUADERNO.read_text(encoding="utf-8"))
        self.codigo = [celda for celda in self.nb["cells"] if celda["cell_type"] == "code"]

    def test_el_cuaderno_es_json_valido(self):
        self.assertIn("cells", self.nb)
        self.assertIn("metadata", self.nb)

    def test_tiene_celdas_de_codigo_suficientes(self):
        self.assertGreaterEqual(len(self.codigo), 10)

    def test_no_tiene_errores(self):
        errores = [
            salida.get("ename")
            for celda in self.codigo
            for salida in celda.get("outputs", [])
            if salida.get("output_type") == "error"
        ]
        self.assertEqual(errores, [], f"el cuaderno tiene errores: {errores}")

    def test_todas_las_celdas_estan_ejecutadas(self):
        sin_ejecutar = [
            posicion
            for posicion, celda in enumerate(self.codigo, start=1)
            if celda.get("execution_count") is None
        ]
        self.assertEqual(sin_ejecutar, [], f"celdas sin ejecutar: {sin_ejecutar}")

    def test_aplica_al_menos_cuatro_transformaciones(self):
        fuentes = "\n".join("".join(celda["source"]) for celda in self.codigo)
        transformaciones = re.findall(r"^df[1-9]\s*=", fuentes, flags=re.MULTILINE)

        self.assertGreaterEqual(len(transformaciones), 4, "la rubrica pide al menos cuatro transformaciones")
        self.assertIn("df_transformado", fuentes)


class ClasesTest(unittest.TestCase):
    def test_las_dos_clases_existen_y_son_clases(self):
        self.assertTrue(isinstance(HFDatasetLoader, type))
        self.assertTrue(isinstance(DatasetSummarizer, type))

    def test_el_objetivo_apunta_a_hugging_face(self):
        self.assertIn("/", TARGET.dataset_id)
        self.assertTrue(TARGET.split)


if __name__ == "__main__":
    unittest.main()
