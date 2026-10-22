"""
test_hf_loader.py
=================
Pruebas de HFDatasetLoader.

No se conecta a Hugging Face: se sustituye `load_dataset` por un doble para
verificar la logica de la clase (paso de parametros, cache, conversion y
manejo de errores).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from datasets import Dataset, DatasetDict  # noqa: E402

from src.hf_loader import DatasetLoadError, HFDatasetLoader  # noqa: E402


class _DatasetFalso:
    """Imita a datasets.Dataset: la clase solo necesita to_pandas()."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self._frame = frame

    def to_pandas(self) -> pd.DataFrame:
        return self._frame.copy()


def _frame_ejemplo() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Id": [1, 2, 3],
            "Species": ["Iris-setosa", "Iris-versicolor", "Iris-virginica"],
        }
    )


class HFDatasetLoaderTest(unittest.TestCase):
    def test_load_devuelve_un_dataframe(self):
        with patch("src.hf_loader.load_dataset", return_value=_DatasetFalso(_frame_ejemplo())):
            df = HFDatasetLoader("scikit-learn/iris").load()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (3, 2))
        self.assertEqual(list(df.columns), ["Id", "Species"])

    def test_reenvia_identificador_y_split(self):
        with patch("src.hf_loader.load_dataset", return_value=_DatasetFalso(_frame_ejemplo())) as mock:
            HFDatasetLoader("scikit-learn/iris", split="test").load()

        _, kwargs = mock.call_args
        self.assertEqual(mock.call_args.args[0], "scikit-learn/iris")
        self.assertEqual(kwargs["split"], "test")

    def test_descarga_una_sola_vez(self):
        with patch("src.hf_loader.load_dataset", return_value=_DatasetFalso(_frame_ejemplo())) as mock:
            loader = HFDatasetLoader("scikit-learn/iris")
            primera = loader.load()
            segunda = loader.load()

        self.assertEqual(mock.call_count, 1)
        self.assertTrue(primera.equals(segunda))

    def test_devuelve_una_copia(self):
        with patch("src.hf_loader.load_dataset", return_value=_DatasetFalso(_frame_ejemplo())):
            loader = HFDatasetLoader("scikit-learn/iris")
            df = loader.load()
            df.drop(columns=["Id"], inplace=True)

        self.assertIn("Id", loader.frame.columns, "modificar el resultado no debe alterar el estado interno")

    def test_split_none_toma_train_del_datasetdict(self):
        conjunto = DatasetDict(
            {
                "train": Dataset.from_dict({"Id": [1, 2]}),
                "test": Dataset.from_dict({"Id": [3]}),
            }
        )
        with patch("src.hf_loader.load_dataset", return_value=conjunto):
            loader = HFDatasetLoader("scikit-learn/iris", split=None)
            df = loader.load()

        self.assertEqual(len(df), 2)
        self.assertEqual(loader.info.split, "train")

    def test_identificador_vacio_es_error(self):
        with self.assertRaises(ValueError):
            HFDatasetLoader("")

    def test_falla_de_red_se_envuelve(self):
        with patch("src.hf_loader.load_dataset", side_effect=ConnectionError("sin red")):
            with self.assertRaises(DatasetLoadError) as contexto:
                HFDatasetLoader("scikit-learn/iris").load()

        self.assertIn("scikit-learn/iris", str(contexto.exception))

    def test_frame_antes_de_load_es_error(self):
        with self.assertRaises(DatasetLoadError):
            _ = HFDatasetLoader("scikit-learn/iris").frame

    def test_info_refleja_dimensiones(self):
        with patch("src.hf_loader.load_dataset", return_value=_DatasetFalso(_frame_ejemplo())):
            loader = HFDatasetLoader("scikit-learn/iris")
            loader.load()
            info = loader.info

        self.assertEqual(info.filas, 3)
        self.assertEqual(info.columnas, 2)
        self.assertEqual(info.nombres_columnas, ("Id", "Species"))
        self.assertIn("scikit-learn/iris", str(info))


if __name__ == "__main__":
    unittest.main()
