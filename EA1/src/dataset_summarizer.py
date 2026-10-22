"""
dataset_summarizer.py
=====================
Clase 2 de la actividad: resumir un DataFrame y exportar el resumen a .txt.

Recibe los datos ya cargados (la conexion con Hugging Face es responsabilidad
de ``HFDatasetLoader``) y describe su estructura: dimensiones, columnas, tipos,
valores nulos, duplicados y estadisticas basicas. El texto se puede imprimir en
el cuaderno y guardar en disco.

Autor: Jesus Gonzalez
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import REPORTS_DIR, SUMMARY_FILENAME

ANCHO_TOTAL = 88
MAX_EJEMPLO = 24
MAX_CATEGORIAS = 5


def _recortar(texto: str, limite: int = MAX_EJEMPLO) -> str:
    """Acorta un texto para que la tabla no se desborde."""
    limpio = " ".join(str(texto).split())
    return limpio if len(limpio) <= limite else limpio[: limite - 1] + "…"


def _tabla(encabezados: list[str], filas: list[list[str]], alineaciones: list[str] | None = None) -> str:
    """Construye una tabla de texto con columnas alineadas."""
    anchos = [len(encabezado) for encabezado in encabezados]
    for fila in filas:
        for posicion, celda in enumerate(fila):
            anchos[posicion] = max(anchos[posicion], len(celda))

    alineaciones = alineaciones or ["<"] * len(encabezados)
    formato = "  ".join(f"{{:{alineacion}{ancho}}}" for alineacion, ancho in zip(alineaciones, anchos))

    lineas = [formato.format(*encabezados)]
    lineas.append("  ".join("-" * ancho for ancho in anchos))
    lineas.extend(formato.format(*fila) for fila in filas)
    return "\n".join(lineas)


def _seccion(titulo: str) -> str:
    """Encabezado de seccion con una linea de separacion."""
    return f"\n{titulo}\n" + "-" * ANCHO_TOTAL


class DatasetSummarizer:
    """Genera un resumen legible de un DataFrame y lo exporta a un archivo .txt.

    Parameters
    ----------
    frame:
        Datos que se van a resumir. Debe ser un ``pandas.DataFrame`` no vacio.
    nombre:
        Nombre con el que aparece el dataset en el encabezado del resumen.
    origen:
        Descripcion del origen de los datos (por ejemplo el identificador del
        dataset en Hugging Face y el split).
    max_categorias:
        Cuantas categorias se listan por cada columna no numerica.
    ruta_salida:
        Archivo por defecto que usa :meth:`save`. Si no se indica, se escribe
        en ``reports/resumen_dataset_transformado.txt``.

    Examples
    --------
    >>> resumen = DatasetSummarizer(df, nombre="Iris transformado")
    >>> texto = resumen.to_text()
    >>> ruta = resumen.save()
    """

    def __init__(
        self,
        frame: pd.DataFrame,
        nombre: str = "dataset",
        origen: str | None = None,
        max_categorias: int = MAX_CATEGORIAS,
        ruta_salida: str | Path | None = None,
    ) -> None:
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"Se esperaba un DataFrame de pandas y se recibio {type(frame).__name__}")
        if frame.empty:
            raise ValueError("El DataFrame esta vacio: no hay nada que resumir")

        self.frame = frame
        self.nombre = nombre
        self.origen = origen
        self.max_categorias = max_categorias
        self.ruta_salida = Path(ruta_salida) if ruta_salida else REPORTS_DIR / SUMMARY_FILENAME

    # ------------------------------------------------------------------
    @property
    def numericas(self) -> pd.DataFrame:
        """Subconjunto de columnas numericas."""
        return self.frame.select_dtypes(include="number")

    @property
    def categoricas(self) -> pd.DataFrame:
        """Subconjunto de columnas no numericas (texto, categoria, fecha...)."""
        return self.frame.select_dtypes(exclude="number")

    def summary(self) -> dict[str, Any]:
        """Resumen estructurado, util para pruebas o para consumirlo por codigo."""
        frame = self.frame
        nulos = frame.isna().sum()
        memoria_kb = float(frame.memory_usage(deep=True).sum()) / 1024
        duplicados = int(frame.duplicated().sum())

        columnas: list[dict[str, Any]] = []
        for nombre in frame.columns:
            serie = frame[nombre]
            nulos_columna = int(nulos[nombre])
            ejemplo = serie.dropna()
            columnas.append(
                {
                    "columna": str(nombre),
                    "tipo": str(serie.dtype),
                    "no_nulos": int(serie.notna().sum()),
                    "nulos": nulos_columna,
                    "nulos_pct": (nulos_columna / len(frame) * 100) if len(frame) else 0.0,
                    "unicos": int(serie.nunique(dropna=True)),
                    "ejemplo": _recortar(ejemplo.iloc[0]) if not ejemplo.empty else "-",
                }
            )

        return {
            "nombre": self.nombre,
            "origen": self.origen,
            "filas": int(frame.shape[0]),
            "columnas": int(frame.shape[1]),
            "memoria_kb": memoria_kb,
            "duplicados": duplicados,
            "duplicados_pct": (duplicados / len(frame) * 100) if len(frame) else 0.0,
            "columnas_detalle": columnas,
            "columnas_con_nulos": [detalle["columna"] for detalle in columnas if detalle["nulos"] > 0],
            "numericas": [str(columna) for columna in self.numericas.columns],
            "categoricas": [str(columna) for columna in self.categoricas.columns],
        }

    # ------------------------------------------------------------------
    def to_text(self) -> str:
        """Devuelve el resumen completo como texto plano."""
        resumen = self.summary()
        lineas: list[str] = []

        # --- Encabezado -------------------------------------------------
        lineas.append("=" * ANCHO_TOTAL)
        lineas.append("RESUMEN DEL DATASET".center(ANCHO_TOTAL))
        lineas.append("=" * ANCHO_TOTAL)
        lineas.append(f"Nombre    : {resumen['nombre']}")
        lineas.append(f"Generado  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if resumen["origen"]:
            lineas.append(f"Origen    : {resumen['origen']}")

        # --- Dimensiones ------------------------------------------------
        lineas.append(_seccion("1. DIMENSIONES"))
        lineas.append(f"Filas      : {resumen['filas']}")
        lineas.append(f"Columnas   : {resumen['columnas']}")
        lineas.append(f"Memoria    : {resumen['memoria_kb']:.1f} KB")
        lineas.append(f"Duplicados : {resumen['duplicados']} filas ({resumen['duplicados_pct']:.2f} %)")

        # --- Columnas y tipos -------------------------------------------
        lineas.append(_seccion("2. COLUMNAS Y TIPOS"))
        filas_tabla = [
            [
                str(posicion),
                detalle["columna"],
                detalle["tipo"],
                str(detalle["no_nulos"]),
                str(detalle["nulos"]),
                f"{detalle['nulos_pct']:.1f}",
                str(detalle["unicos"]),
                detalle["ejemplo"],
            ]
            for posicion, detalle in enumerate(resumen["columnas_detalle"], start=1)
        ]
        lineas.append(
            _tabla(
                ["#", "columna", "tipo", "no_nulos", "nulos", "nulos_%", "unicos", "ejemplo"],
                filas_tabla,
                alineaciones=[">", "<", "<", ">", ">", ">", ">", "<"],
            )
        )

        # --- Valores nulos ----------------------------------------------
        lineas.append(_seccion("3. VALORES NULOS"))
        if resumen["columnas_con_nulos"]:
            filas_nulos = [
                [detalle["columna"], str(detalle["nulos"]), f"{detalle['nulos_pct']:.2f} %"]
                for detalle in resumen["columnas_detalle"]
                if detalle["nulos"] > 0
            ]
            lineas.append(_tabla(["columna", "nulos", "porcentaje"], filas_nulos, [">", ">", ">"]))
        else:
            lineas.append("Sin valores nulos: todas las columnas estan completas.")

        # --- Estadisticas descriptivas ----------------------------------
        lineas.append(_seccion("4. ESTADISTICAS DESCRIPTIVAS (COLUMNAS NUMERICAS)"))
        if resumen["numericas"]:
            descripcion = self.numericas.describe().T
            filas_stats = [
                [
                    str(columna),
                    f"{fila['count']:.0f}",
                    f"{fila['mean']:.2f}",
                    f"{fila['std']:.2f}",
                    f"{fila['min']:.2f}",
                    f"{fila['50%']:.2f}",
                    f"{fila['max']:.2f}",
                ]
                for columna, fila in descripcion.iterrows()
            ]
            lineas.append(
                _tabla(
                    ["columna", "n", "media", "desv_est", "min", "mediana", "max"],
                    filas_stats,
                    ["<", ">", ">", ">", ">", ">", ">"],
                )
            )
        else:
            lineas.append("El DataFrame no tiene columnas numericas.")

        # --- Variables categoricas --------------------------------------
        lineas.append(_seccion("5. VARIABLES CATEGORICAS"))
        if resumen["categoricas"]:
            for columna in resumen["categoricas"]:
                serie = self.frame[columna].dropna()
                conteo = serie.value_counts().head(self.max_categorias)
                detalle = ", ".join(f"{valor} ({cantidad})" for valor, cantidad in conteo.items())
                restantes = serie.nunique() - len(conteo)
                sufijo = f" y {restantes} mas" if restantes > 0 else ""
                lineas.append(f"{columna} ({serie.nunique()} categorias): {detalle}{sufijo}")
        else:
            lineas.append("El DataFrame no tiene columnas categoricas.")

        # --- Cierre -----------------------------------------------------
        lineas.append("")
        lineas.append("=" * ANCHO_TOTAL)
        lineas.append("Fin del resumen".center(ANCHO_TOTAL))
        lineas.append("=" * ANCHO_TOTAL)

        # sin espacios sobrantes al final de cada linea
        return "\n".join(linea.rstrip() for linea in "\n".join(lineas).splitlines()) + "\n"

    # ------------------------------------------------------------------
    def save(self, ruta: str | Path | None = None) -> Path:
        """Escribe el resumen en un archivo .txt y devuelve la ruta final."""
        destino = Path(ruta) if ruta is not None else self.ruta_salida
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(self.to_text(), encoding="utf-8", newline="\n")
        return destino

    def __repr__(self) -> str:
        return (
            f"DatasetSummarizer(nombre={self.nombre!r}, "
            f"filas={self.frame.shape[0]}, columnas={self.frame.shape[1]})"
        )
