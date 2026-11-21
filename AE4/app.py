"""Aplicación Streamlit del proyecto integrador: métricas y visualización de datos.

Sirve los resultados del proyecto sobre el dataset de iris: la necesidad y las
preguntas de negocio, una sección por pregunta con su métrica, su gráfico y su
interpretación, y el cierre con conclusiones, recomendaciones y limitaciones.

Los datos no se copian aquí: la aplicación carga el dataset preparado y las
tablas de resultados que el cuaderno de la AE3 exporta en `AE3/datos` y
`AE3/resultados`, y verifica en pantalla que las cifras coincidan. Una sola
fuente de verdad: si el cuaderno se vuelve a ejecutar, la app se actualiza.

Ejecución:
    streamlit run AE4/app.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
DATASET = RAIZ / "AE3" / "datos" / "dataset_preparado.csv"
RESULTADOS = RAIZ / "AE3" / "resultados"

MEDIDAS = ("largo_sepalo_cm", "ancho_sepalo_cm", "largo_petalo_cm", "ancho_petalo_cm")
ETIQUETAS_MEDIDA = {
    "largo_sepalo_cm": "Largo del sépalo (cm)",
    "ancho_sepalo_cm": "Ancho del sépalo (cm)",
    "largo_petalo_cm": "Largo del pétalo (cm)",
    "ancho_petalo_cm": "Ancho del pétalo (cm)",
}
COLORES = {"setosa": "#55A868", "versicolor": "#4C72B0", "virginica": "#C44E52"}
plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold"})

st.set_page_config(
    page_title="Proyecto integrador · Iris",
    page_icon="🌷",
    layout="wide",
)


@st.cache_data
def cargar_datos():
    dataset = pd.read_csv(DATASET)
    tablas = {
        "p1": pd.read_csv(RESULTADOS / "tabla_p1_perfil_especies.csv"),
        "p2": pd.read_csv(RESULTADOS / "tabla_p2_variacion_medidas.csv"),
        "p3": pd.read_csv(RESULTADOS / "tabla_p3_correlaciones.csv"),
        "p4": pd.read_csv(RESULTADOS / "tabla_p4_categorias_tamano.csv"),
        "p4_cruce": pd.read_csv(RESULTADOS / "tabla_p4_cruce_especie_tamano.csv"),
    }
    return dataset, tablas


@st.cache_data
def verificar_cifras(dataset: pd.DataFrame, tablas: dict) -> list[str]:
    """Compara lo calculado en vivo contra las tablas del cuaderno."""
    avisos = []
    perfil = (
        dataset.melt(id_vars=["especie"], value_vars=list(MEDIDAS), var_name="medida")
        .groupby(["especie", "medida"])["value"]
        .agg(["mean", "median", "std"])
        .round(4)
    )
    for _, fila in tablas["p1"].iterrows():
        calculado = perfil.loc[(fila["especie"], fila["medida"])]
        for columna, esperado in (("mean", fila["media_cm"]), ("median", fila["mediana_cm"]),
                                  ("std", fila["desviacion_cm"])):
            # Las tablas del cuaderno traen dos decimales: la tolerancia es media
            # unidad del último decimal registrado.
            if abs(calculado[columna] - esperado) > 0.0051:
                avisos.append(f"P1: {fila['especie']} / {fila['medida']} / {columna}")
    tramos = dataset["tamano_flor"].value_counts().sort_index()
    for _, fila in tablas["p4"].iterrows():
        if tramos.get(fila["tamano_flor"], 0) != fila["flores"]:
            avisos.append(f"P4: conteo de {fila['tamano_flor']}")
    cruce = pd.crosstab(dataset["especie"], dataset["tamano_flor"])
    for _, fila in tablas["p4_cruce"].iterrows():
        for tamano in ("Pequeña", "Media", "Grande"):
            if cruce.loc[fila["especie"], tamano] != int(fila[tamano].split()[0]):
                avisos.append(f"P4 cruce: {fila['especie']} / {tamano}")
    return avisos


def grafico_perfil(tablas: dict) -> plt.Figure:
    """Barras agrupadas: media de cada medida por especie."""
    perfil = tablas["p1"].pivot(index="medida", columns="especie", values="media_cm")
    perfil = perfil.reindex(list(MEDIDAS))
    x = range(len(perfil.index))
    ancho = 0.26
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    for i, especie in enumerate(perfil.columns):
        barras = ax.bar(
            [p + (i - 1) * ancho for p in x],
            perfil[especie],
            width=ancho,
            color=COLORES[especie],
            label=especie.capitalize(),
        )
        ax.bar_label(barras, fmt="%.1f", fontsize=8, padding=2)
    ax.set_xticks(list(x))
    ax.set_xticklabels([ETIQUETAS_MEDIDA[m] for m in perfil.index], fontsize=9)
    ax.set_ylabel("Media (cm)")
    ax.set_title("Media de cada medida morfológica por especie")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_variacion(tablas: dict) -> plt.Figure:
    """Barras agrupadas: coeficiente de variación de cada medida por especie."""
    p2 = tablas["p2"].copy()
    p2["medida"] = p2.index.map(lambda i: ETIQUETAS_MEDIDA[MEDIDAS[i]])
    x = range(len(MEDIDAS))
    ancho = 0.26
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    for i, especie in enumerate(("setosa", "versicolor", "virginica")):
        barras = ax.bar(
            [p + (i - 1) * ancho for p in x],
            p2[f"cv_{especie}_pct"],
            width=ancho,
            color=COLORES[especie],
            label=especie.capitalize(),
        )
        ax.bar_label(barras, fmt="%.1f", fontsize=8, padding=2)
    ax.set_xticks(list(x))
    ax.set_xticklabels([ETIQUETAS_MEDIDA[m] for m in MEDIDAS], fontsize=9)
    ax.set_ylabel("Coeficiente de variación (%)")
    ax.set_title("Variabilidad relativa dentro de cada especie")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_correlacion(dataset: pd.DataFrame) -> plt.Figure:
    """Dispersión de largo de sépalo contra largo de pétalo, por especie."""
    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    for especie, color in COLORES.items():
        subset = dataset[dataset["especie"] == especie]
        ax.scatter(
            subset["largo_sepalo_cm"],
            subset["largo_petalo_cm"],
            s=28,
            alpha=0.75,
            color=color,
            label=especie.capitalize(),
        )
    ax.set_xlabel("Largo del sépalo (cm)")
    ax.set_ylabel("Largo del pétalo (cm)")
    ax.set_title("Largo del pétalo contra largo del sépalo, por especie")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_tamanos(tablas: dict) -> plt.Figure:
    """Barras apiladas horizontales: tamaño de flor por especie."""
    cruce = tablas["p4_cruce"].copy().set_index("especie")
    orden = ("setosa", "versicolor", "virginica")
    cruce = cruce.reindex(orden)
    # Las celdas del CSV traen "47 flores (94.0 %)": quedarse con el conteo.
    valores = cruce[[c for c in ("Pequeña", "Media", "Grande") if c in cruce.columns]].apply(
        lambda col: col.str.split().str[0].astype(int)
    )
    porcentaje = valores.div(valores.sum(axis=1), axis=0) * 100
    colores_tamano = {"Pequeña": "#9CC2CB", "Media": "#4C72B0", "Grande": "#31445C"}
    fig, ax = plt.subplots(figsize=(8.4, 2.9))
    izquierda = pd.Series(0.0, index=porcentaje.index)
    for tamano in porcentaje.columns:
        ax.barh(
            porcentaje.index,
            porcentaje[tamano],
            left=izquierda,
            color=colores_tamano.get(tamano, "#888888"),
            label=tamano,
        )
        for y, (valor, ini) in enumerate(zip(porcentaje[tamano], izquierda)):
            if valor >= 5:
                ax.text(ini + valor / 2, y, f"{valor:.0f}%", ha="center", va="center",
                        color="white", fontsize=9)
        izquierda = izquierda + porcentaje[tamano]
    ax.set_xlim(0, 100)
    ax.set_xlabel("Participación (%)")
    ax.set_ylabel("")
    ax.set_title("Categoría de tamaño de flor dentro de cada especie")
    ax.legend(frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def metrica_y_grafico():
    """Encabezado común de las secciones de pregunta."""
    return None


dataset, tablas = cargar_datos()
avisos = verificar_cifras(dataset, tablas)

with st.sidebar:
    st.header("Proyecto integrador")
    st.caption("Métricas y visualización de datos · dataset iris")
    seccion = st.radio(
        "Contenido",
        (
            "Inicio · necesidad y datos",
            "P1 · Perfil por especie",
            "P2 · Sépalo o pétalo",
            "P3 · Relación sépalo-pétalo",
            "P4 · Tamaño de la flor",
            "Conclusiones y limitaciones",
        ),
    )
    st.divider()
    st.markdown(
        """
        **Fuente de los datos**

        `scikit-learn/iris` (Hugging Face), 150 flores de tres especies.
        La app carga el dataset preparado por el cuaderno de la AE3
        (`150 × 9`) y sus tablas de resultados exportadas.
        """
    )
    if avisos:
        st.error("Desajustes entre tablas y datos: " + "; ".join(avisos))
    else:
        st.success("Cifras verificadas contra el cuaderno")

# ---------------------------------------------------------------- Inicio
if seccion.startswith("Inicio"):
    st.title("Caracterización morfológica de tres especies de iris")
    st.markdown(
        """
        **La necesidad del proyecto.** Conocer cómo se caracterizan las tres especies
        de iris a partir de sus medidas morfológicas, de forma descriptiva y
        reproducible, con datos preparados y verificados. Las medidas que alguien
        registra en campo o en laboratorio pueden clasificarse y compararse solo si
        se entiende qué distingue a cada especie y cuánto varía esa distinción.
        """
    )
    st.subheader("Preguntas de negocio")
    st.markdown(
        """
        | # | Pregunta | Sección |
        |---|----------|---------|
        | P1 | ¿Cómo se caracteriza morfológicamente cada especie? | Perfil por especie |
        | P2 | ¿Las especies se diferencian más por el sépalo o por el pétalo? | Sépalo o pétalo |
        | P3 | ¿Qué relación existe entre las medidas del sépalo y las del pétalo? | Relación sépalo-pétalo |
        | P4 | ¿Cómo se distribuyen los ejemplares según el tamaño de la flor? | Tamaño de la flor |
        """
    )
    st.subheader("El dataset")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Flores registradas", len(dataset))
    m2.metric("Especies", dataset["especie"].nunique())
    m3.metric("Variables morfológicas", len(MEDIDAS))
    m4.metric("Variables derivadas", 4)
    st.caption(
        "Columnas: largo y ancho de sépalo y de pétalo (cm), especie, áreas calculadas "
        "de sépalo y pétalo (cm²), ratio del pétalo y categoría de tamaño "
        "(terciles del área del pétalo: cortes en 2,52 y 7,71 cm²). "
        "Sin valores faltantes; dos grupos de medidas idénticas entre especies "
        "distintas se conservan porque son ejemplares distintos."
    )
    st.dataframe(dataset.head(10), width="stretch", hide_index=True)

# ---------------------------------------------------------------- P1
elif seccion.startswith("P1"):
    st.title("P1 · ¿Cómo se caracteriza morfológicamente cada especie?")
    st.markdown(
        """
        **Métrica:** media, mediana y desviación estándar de cada una de las cuatro
        medidas morfológicas por especie, en centímetros. Calculadas sobre las 150
        flores del dataset preparado y exportadas por el cuaderno en
        `tabla_p1_perfil_especies.csv`.
        """
    )
    col_graf, col_tabla = st.columns([3, 2])
    with col_graf:
        st.pyplot(grafico_perfil(tablas), width="stretch")
    with col_tabla:
        st.dataframe(tablas["p1"], width="stretch", hide_index=True)
    st.markdown(
        """
        **Qué muestran los datos.** Las especies se ordenan de forma consistente:
        *setosa* tiene los pétalos más pequeños (media de 1,46 cm de largo frente a
        4,26 y 5,55 en las otras dos), *virginica* la mayor en todas las medidas y
        *versicolor* queda en el medio. El ancho del sépalo es la excepción:
        *setosa* es la más ancha (3,42 cm).

        **Qué decisión podrían apoyar.** El largo y el ancho del pétalo separan a
        *setosa* del resto con claridad, por lo que una regla sencilla de
        identificación en campo puede apoyarse en el pétalo antes que en el sépalo.

        **Limitación.** Son promedios de una muestra de 50 flores por especie del
        conjunto clásico de Fisher (1936); no describen otras poblaciones ni épocas
        del año, y la media sola no captura la forma de la distribución.
        """
    )

# ---------------------------------------------------------------- P2
elif seccion.startswith("P2"):
    st.title("P2 · ¿Las especies se diferencian más por el sépalo o por el pétalo?")
    st.markdown(
        """
        **Métrica:** dos medidas comparables de distancia. Dentro de cada especie,
        el coeficiente de variación (desviación estándar relativa a la media, en %),
        que indica cuánto se solapan las especies. Entre especies, el rango de las
        medias de cada medida y su diferencia relativa (rango sobre la media global,
        en %). Tablas exportadas en `tabla_p2_variacion_medidas.csv`.
        """
    )
    st.pyplot(grafico_variacion(tablas), width="stretch")
    p2 = tablas["p2"].copy()
    p2.insert(0, "medida", [ETIQUETAS_MEDIDA[m] for m in MEDIDAS])
    st.dataframe(p2, width="stretch", hide_index=True)
    st.markdown(
        """
        **Qué muestran los datos.** En el pétalo las medias de las tres especies se
        separan mucho más: el largo del pétalo abarca 4,09 cm entre la media mínima
        y la máxima (diferencia relativa del 108,8 %), frente a 1,58 cm del largo
        del sépalo (27,1 %). Además, el ancho del pétalo de *setosa* varía un 43,9 %
        dentro de su especie, pero como su media está tan lejos de las otras dos,
        el solapamiento sigue siendo bajo.

        **Qué decisión podrían apoyar.** Si se diseña una clave de identificación o
        un modelo de clasificación, las medidas del pétalo aportan más separación
        entre especies que las del sépalo, y deberían pesar más.

        **Limitación.** El coeficiente de variación asume escalas comparables; aquí
        todas las medidas están en centímetros y el cálculo es legítimo, pero una
        distancia relativa no sustituye a una prueba de hipótesis para afirmar que
        la diferencia es estadísticamente significativa.
        """
    )

# ---------------------------------------------------------------- P3
elif seccion.startswith("P3"):
    st.title("P3 · ¿Qué relación existe entre las medidas del sépalo y las del pétalo?")
    st.markdown(
        """
        **Métrica:** coeficiente de correlación de Pearson entre cada par de medidas
        (sépalo contra pétalo), calculado globalmente (n = 150) y por especie
        (n = 50 cada una). Sin unidades: va de -1 a +1. Tabla exportada en
        `tabla_p3_correlaciones.csv`.
        """
    )
    col_graf, col_tabla = st.columns([3, 2])
    with col_graf:
        st.pyplot(grafico_correlacion(dataset), width="stretch")
    with col_tabla:
        st.dataframe(tablas["p3"], width="stretch", hide_index=True)
    st.markdown(
        """
        **Qué muestran los datos.** Globalmente, el largo del sépalo y el largo del
        pétalo se mueven juntos (r = 0,87). Pero al separar por especie la fuerza
        cambia: 0,86 en *virginica*, 0,75 en *versicolor* y solo 0,26 en *setosa*.
        La relación global está dominada por la distancia entre especies, no por una
        ley común dentro de cada una: flores de especie con pétalos grandes tienden
        a tener sépalos largos, pero dentro de *setosa* un sépalo más largo casi no
        predice un pétalo más largo.

        **Qué decisión podrían apoyar.** Para una regla de identificación conviene
        usar la combinación de medidas por especie, no una relación global: una
        correlación fuerte entre dos variables no permite deducir una de la otra
        dentro de todas las especies.

        **Limitación.** Correlación no es causalidad: nada aquí demuestra que el
        sépalo determine el pétalo o al revés; ambas crecen con la especie, que es
        la variable que este análisis no modela explícitamente. Con n = 50 por
        especie, los coeficientes tienen incertidumbre no despreciable.
        """
    )

# ---------------------------------------------------------------- P4
elif seccion.startswith("P4"):
    st.title("P4 · ¿Cómo se distribuyen los ejemplares según el tamaño de la flor?")
    st.markdown(
        """
        **Métrica:** categoría de tamaño de flor (`tamano_flor`), definida por
        terciles del área del pétalo calculada (cortes en 2,52 y 7,71 cm²), con lo
        cual cada categoría reúne cerca de un tercio de las 150 flores. La tabla de
        participación está en `tabla_p4_categorias_tamano.csv` y el cruce por
        especie en `tabla_p4_cruce_especie_tamano.csv`.
        """
    )
    col_graf, col_tabla = st.columns([3, 2])
    with col_graf:
        st.pyplot(grafico_tamanos(tablas), width="stretch")
    with col_tabla:
        st.dataframe(tablas["p4_cruce"], width="stretch", hide_index=True)
    st.markdown(
        """
        **Qué muestran los datos.** La categoría de tamaño coincide casi por completo
        con la especie: la totalidad de *setosa* es de flor pequeña, y *versicolor*
        y *virginica* se reparten entre media y grande con un 94 % en su categoría
        dominante y solo el 6 % en la otra. La variable derivada no agrega
        información que el pétalo ya no contuviera, pero traduce una medida continua
        a tres categorías directamente comunicables.

        **Qué decisión podrían apoyar.** "Tamaño de flor" es una etiqueta útil para
        segmentar inventarios o reportes por especie sin exponer decimales, aunque
        para clasificar una flor nueva conviene más la medición directa del pétalo.

        **Limitación.** Los cortes son terciles de esta muestra: si llegan flores de
        otra población, los límites 2,52 y 7,71 cm² no necesariamente los clasifican
        bien. La aparente coincidencia total entre especie y tamaño es una propiedad
        de estos datos, no una ley general.
        """
    )

# ---------------------------------------------------------------- Cierre
else:
    st.title("Conclusiones, recomendaciones y limitaciones")
    st.subheader("Conclusiones")
    st.markdown(
        """
        1. Las tres especies se ordenan de forma consistente en todas las medidas del
           pétalo: *setosa* (menor), *versicolor* (media) y *virginica* (mayor).
        2. El pétalo separa mejor las especies que el sépalo: el largo del pétalo
           varía un 108,8 % entre medias de especies, más del triple que el largo del
           sépalo (27,1 %).
        3. La correlación sépalo-pétalo es fuerte globalmente (r = 0,87) pero débil
           dentro de *setosa* (r = 0,26): la relación pertenece a la comparación entre
           especies, no a cada una por separado.
        4. La categoría de tamaño coincide casi por completo con la especie, un
           resultado derivado del propio pétalo.
        """
    )
    st.subheader("Recomendaciones")
    st.markdown(
        """
        - Para identificadores o clasificadores futuros, priorizar el largo y el
          ancho del pétalo sobre las medidas del sépalo.
        - No usar correlaciones globales para predecir dentro de una especie:
          calcularlas por especie, como hace esta sección.
        - Si se necesitan límites de tamaño para otras poblaciones, recalcular los
          terciles con datos de la población objetivo.
        """
    )
    st.subheader("Limitaciones del análisis")
    st.markdown(
        """
        - El análisis es descriptivo: ninguna cifra prueba causalidad ni diferencias
          estadísticamente significativas; para eso harían falta pruebas de hipótesis.
        - Los datos provienen del conjunto clásico de iris (Fisher, 1936) publicado
          en Hugging Face por scikit-learn: 150 flores de una región y época
          determinadas. Extrapolaciones a otras poblaciones no están sustentadas.
        - Dos grupos de flores comparten medidas idénticas entre especies distintas
          y cuatro anchos de sépalo quedaron fuera de la regla 1,5 × RIC; ambos casos
          se revisaron y se conservaron, pero conviene recordarlos al leer cifras
          extremas.
        - Las variables derivadas (áreas, ratio y tamaño) son calculadas, no
          medidas: heredan cualquier error de las columnas originales.
        """
    )
    st.divider()
    st.caption(
        "Proyecto Integrado III · Analítica de Datos (PREICA2602B020038) · Jesus Gonzalez · "
        "Datos y tablas generados por el cuaderno de la AE3 del repositorio."
    )
