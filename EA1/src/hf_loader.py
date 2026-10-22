"""
hf_loader.py
============
Clase 1 de la actividad: obtener un dataset de Hugging Face como DataFrame.

La clase concentra la conexion y la carga: quien la usa solo indica el
identificador del dataset y, si hace falta, el split. El resultado es un
``pandas.DataFrame`` listo para trabajar desde el cuaderno.

Autor: Jesus Gonzalez
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import DatasetDict, load_dataset
from datasets.utils.logging import disable_progress_bar, enable_progress_bar


class DatasetLoadError(RuntimeError):
    """Error controlado cuando el dataset no se puede descargar ni convertir."""


@dataclass(frozen=True)
class DatasetInfo:
    """Metadatos de la carga, utiles para trazabilidad y para el informe."""

    dataset_id: str
    split: str
    config_name: str | None
    filas: int
    columnas: int
    nombres_columnas: tuple[str, ...]

    def __str__(self) -> str:
        origen = self.dataset_id
        if self.config_name:
            origen = f"{origen} ({self.config_name})"
        columnas = ", ".join(self.nombres_columnas)
        return (
            f"Origen     : Hugging Face · {origen}\n"
            f"Split      : {self.split}\n"
            f"Dimensiones: {self.filas} filas x {self.columnas} columnas\n"
            f"Columnas   : {columnas}"
        )


class HFDatasetLoader:
    """Carga un dataset de Hugging Face Hub y lo devuelve como DataFrame.

    Parameters
    ----------
    dataset_id:
        Identificador del dataset en el Hub, por ejemplo ``"scikit-learn/iris"``.
    split:
        Split que se quiere cargar (``"train"``, ``"test"``, ...). Si se pasa
        ``None``, se usa ``train`` cuando existe y, en su defecto, el primer
        split disponible del dataset.
    config_name:
        Nombre de la configuracion, solo para datasets que tienen varias.
    cache_dir:
        Carpeta de cache opcional. Por defecto se usa la de Hugging Face.
    token:
        Token de acceso, necesario unicamente para datasets privados o con
        limite de uso.
    mostrar_progreso:
        Si es ``True``, ``datasets`` dibuja su barra de descarga. Por defecto
        se silencia para no ensuciar la salida del cuaderno.
    **load_kwargs:
        Cualquier otro argumento se reenvia a ``datasets.load_dataset``.

    Examples
    --------
    >>> loader = HFDatasetLoader("scikit-learn/iris", split="train")
    >>> df = loader.load()
    >>> df.shape
    (150, 6)
    """

    def __init__(
        self,
        dataset_id: str,
        split: str | None = "train",
        config_name: str | None = None,
        cache_dir: str | Path | None = None,
        token: str | None = None,
        mostrar_progreso: bool = False,
        **load_kwargs: Any,
    ) -> None:
        if not dataset_id or not isinstance(dataset_id, str):
            raise ValueError("dataset_id debe ser una cadena no vacia, por ejemplo 'scikit-learn/iris'")

        self.dataset_id = dataset_id
        self.split = split
        self.config_name = config_name
        self.cache_dir = str(cache_dir) if cache_dir is not None else None
        self.token = token
        self.mostrar_progreso = mostrar_progreso
        self.load_kwargs = load_kwargs

        self._frame: pd.DataFrame | None = None
        self._split_efectivo: str | None = split

    # ------------------------------------------------------------------
    def load(self) -> pd.DataFrame:
        """Descarga el dataset y devuelve una copia del DataFrame.

        La descarga ocurre una sola vez: las llamadas siguientes devuelven el
        DataFrame ya cargado, de modo que el cuaderno puede invocar el metodo
        sin volver a golpear la red.
        """
        if self._frame is None:
            self._frame = self._descargar()
        return self._frame.copy()

    def _descargar(self) -> pd.DataFrame:
        """Realiza la conexion con el Hub y convierte el dataset a pandas."""
        if self.mostrar_progreso:
            enable_progress_bar()
        else:
            disable_progress_bar()

        try:
            cargado = load_dataset(
                self.dataset_id,
                name=self.config_name,
                split=self.split,
                cache_dir=self.cache_dir,
                token=self.token,
                **self.load_kwargs,
            )
        except Exception as error:  # la causa real se conserva en el encadenado
            raise DatasetLoadError(
                f"No se pudo cargar '{self.dataset_id}' desde Hugging Face. "
                f"Revisa el identificador, el split y la conexion. Detalle: {error}"
            ) from error

        # split=None devuelve un DatasetDict con todos los splits disponibles
        if isinstance(cargado, DatasetDict):
            self._split_efectivo = "train" if "train" in cargado else next(iter(cargado))
            cargado = cargado[self._split_efectivo]
        elif self._split_efectivo is None:
            self._split_efectivo = "train"

        try:
            frame = cargado.to_pandas()
        except Exception as error:
            raise DatasetLoadError(
                f"El dataset '{self.dataset_id}' se descargo pero no se pudo convertir "
                f"a DataFrame. Detalle: {error}"
            ) from error

        if frame.empty:
            raise DatasetLoadError(f"El dataset '{self.dataset_id}' no contiene filas en el split solicitado.")

        return frame

    # ------------------------------------------------------------------
    @property
    def frame(self) -> pd.DataFrame:
        """DataFrame cargado. Falla si todavia no se llamo a :meth:`load`."""
        if self._frame is None:
            raise DatasetLoadError("Todavia no hay datos: llama primero a load().")
        return self._frame

    @property
    def is_loaded(self) -> bool:
        """True si el dataset ya se descargo al menos una vez."""
        return self._frame is not None

    @property
    def info(self) -> DatasetInfo:
        """Metadatos de la carga (origen, split y dimensiones)."""
        frame = self.frame
        return DatasetInfo(
            dataset_id=self.dataset_id,
            split=self._split_efectivo or "train",
            config_name=self.config_name,
            filas=int(frame.shape[0]),
            columnas=int(frame.shape[1]),
            nombres_columnas=tuple(str(columna) for columna in frame.columns),
        )

    def __repr__(self) -> str:
        estado = "cargado" if self.is_loaded else "sin cargar"
        return f"HFDatasetLoader(dataset_id={self.dataset_id!r}, split={self.split!r}, estado={estado})"
