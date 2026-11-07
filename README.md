# Proyecto Integrado III — Analítica de Datos

[![CI](https://github.com/jesusjoelgonca/proyecto-integrado-iii-analitica-de-datos/actions/workflows/ci.yml/badge.svg)](https://github.com/jesusjoelgonca/proyecto-integrado-iii-analitica-de-datos/actions/workflows/ci.yml)

**Profesor:** Andrés Felipe Callejas — PREICA2602B020038
**Estudiante:** Jesús González

Repositorio de trabajo del curso. Cada evidencia de aprendizaje vive en su propia
carpeta (`EA1/`, `EA2/`, …) y comparte las dependencias de la raíz.

## Contenido

```
.
├── .github/workflows/ci.yml     Integración continua (Linux y Windows)
├── requirements.txt             Dependencias del curso
├── EA1/                         Carga y creación de dataset
│   ├── Gonzalez_Jesus_EA1.ipynb Cuaderno que coordina el flujo
│   ├── src/
│   │   ├── config.py            Dataset, split y rutas
│   │   ├── hf_loader.py         Clase HFDatasetLoader
│   │   └── dataset_summarizer.py Clase DatasetSummarizer
│   ├── tests/                   Pruebas de las clases y de los entregables
│   └── reports/
│       └── resumen_dataset_transformado.txt
└── AE3/                         Transformación y enriquecimiento de datos
    ├── Gonzalez_Jesus_AE3.ipynb Cuaderno de la etapa (ejecutado)
    ├── src/                     Clases reutilizadas de EA1
    ├── datos/
    │   └── dataset_preparado.csv
    ├── resultados/              Tablas de resultados (.csv) y resumen (.txt)
    └── doc/
        └── Gonzalez_Jesus_AE3.docx  Documento de avance
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cómo ejecutar

```bash
# Pruebas (no necesitan conexión: el acceso a Hugging Face está simulado)
cd EA1 && python -m unittest discover -s tests -v

# Regenerar el resumen ejecutando el cuaderno de principio a fin
cd EA1 && jupyter nbconvert --to notebook --execute --inplace Gonzalez_Jesus_EA1.ipynb
```

También se puede abrir `EA1/Gonzalez_Jesus_EA1.ipynb` y usar *Run All*. El cuaderno
descarga el dataset de Hugging Face la primera vez y luego trabaja con la caché
local del Hub.

---

# EA1 — Carga y creación de dataset

Obtener un dataset desde Hugging Face, resumirlo en un `.txt` y coordinar ambas
clases desde un cuaderno, aplicando transformaciones y registrando los avances
en GitHub.

## Dataset

`scikit-learn/iris` (split `train`): 150 filas y 6 columnas con las medidas
morfológicas de tres especies de flor. Se eligió por ser pequeño, estable y
suficientemente variado para mostrar transformaciones de tipos numéricos y
categóricos. El identificador y el split se configuran en `src/config.py`.

## Las dos clases

**`HFDatasetLoader`** (`src/hf_loader.py`) — recibe el identificador del dataset
y, opcionalmente, el split y la configuración; hace la conexión y la descarga
dentro de la clase y devuelve un `DataFrame` de pandas. Expone `info` con los
metadatos de la carga y descarga una sola vez (las llamadas siguientes usan el
`DataFrame` ya cargado). Los errores de red o de identificador se envuelven en
`DatasetLoadError` con un mensaje útil.

**`DatasetSummarizer`** (`src/dataset_summarizer.py`) — recibe un `DataFrame` ya
cargado y genera un resumen en texto: dimensiones, columnas y tipos, valores
nulos con porcentaje, duplicados, memoria y estadísticas descriptivas, además de
las categorías de las variables no numéricas. `save()` lo escribe en
`reports/resumen_dataset_transformado.txt`.

## Transformaciones del cuaderno

Se aplican siete transformaciones distintas, cada una sobre una copia, mostrando
su resultado:

| # | Transformación | Operación |
| --- | --- | --- |
| 1 | Renombrar columnas al español | `rename` |
| 2 | Normalizar la etiqueta de especie | manipulación de texto |
| 3 | Seleccionar columnas de análisis | selección |
| 4 | Crear `area_petalo_cm2` y `ratio_petalo` | columnas derivadas |
| 5 | Filtrar flores con área sobre la mediana | filtrado de filas |
| 6 | Añadir la media de área por especie | agregación por grupo |
| 7 | Ordenar por área de pétalo | ordenamiento |

El resultado pasa a `DatasetSummarizer`, de modo que el `.txt` describe los datos
**transformados**: 75 filas y 8 columnas, con las columnas ya en español y las
dos derivadas.

## Resultados

- Dataset original: 150 filas × 6 columnas.
- DataFrame transformado: 75 filas × 8 columnas (el filtro por mediana deja fuera
  las flores *setosa*, cuyo pétalo es el más pequeño).
- Sin valores nulos. Aparece 1 fila duplicada (1,33 %) al descartar el
  identificador: dos flores con las mismas cuatro medidas.
- 29 pruebas automatizadas, todas en verde en Linux y Windows.

## Evidencias de ejecución

Comprobado sobre un clon limpio del repositorio y borrando antes el `.txt`, para
verificar que lo genera la ejecución y no está copiado a mano:

| Evidencia | Resultado |
| --- | --- |
| Carga desde Hugging Face | `scikit-learn/iris`, split `train`, 150 filas × 6 columnas |
| Cuaderno | 25 celdas (11 de código), todas ejecutadas, sin errores |
| Resultados mostrados | 9 tablas: una por transformación más la de verificación |
| Comprobaciones del cuaderno | 10 de 10 superadas |
| Archivo generado | `reports/resumen_dataset_transformado.txt` (2 638 bytes) |
| Pruebas automatizadas | `Ran 29 tests … OK` |
| Integración continua | En verde en `ubuntu-latest` y `windows-latest` |

Salida de la celda de verificación del cuaderno:

```
10 comprobaciones superadas · resumen_dataset_transformado.txt: 2638 bytes
```

Salida de la suite de pruebas:

```
Ran 29 tests in 0.104s

OK
```

El resumen regenerado es idéntico al versionado salvo la línea `Generado`, que
contiene la marca de tiempo de la ejecución.

## Relación con la rúbrica

| Criterio | Pts | Dónde se evidencia |
| --- | --- | --- |
| Puntualidad y enlace de entrega | 10 | Enlace de este repositorio en la plataforma |
| Código versionado en GitHub | 10 | Historial de commits + archivos `.py` y `.ipynb` |
| Clase para generar un DataFrame | 25 | `src/hf_loader.py` |
| Clase para resumir y exportar | 20 | `src/dataset_summarizer.py` + `reports/*.txt` |
| Transformaciones en Jupyter | 10 | Siete transformaciones en el cuaderno, con resultados visibles |
| Funcionamiento y evidencias | 25 | Cuaderno ejecutado sin errores, 29 pruebas y CI en verde |

---

# AE3 — Transformación y enriquecimiento de datos

Segunda etapa del proyecto integrador sobre el mismo dataset (`scikit-learn/iris`,
cargado desde Hugging Face con la clase de EA1). El cuaderno
`AE3/Gonzalez_Jesus_AE3.ipynb` transforma los datos, los enriquece con variables
calculadas y responde cuatro preguntas de negocio con tablas exportadas.

## Necesidad y preguntas de negocio

La etapa anterior no había formalizado las preguntas del proyecto, así que esta
las define y las deja registradas (ajuste documentado en el cuaderno y en el
documento de avance). La necesidad es una caracterización descriptiva de las tres
especies a partir de sus medidas morfológicas.

| # | Pregunta | Tabla de resultados |
| --- | --- | --- |
| P1 | ¿Cómo se caracteriza morfológicamente cada especie? | `resultados/tabla_p1_perfil_especies.csv` |
| P2 | ¿Las especies se diferencian más por el sépalo o por el pétalo? | `resultados/tabla_p2_variacion_medidas.csv` |
| P3 | ¿Qué relación existe entre las medidas del sépalo y las del pétalo? | `resultados/tabla_p3_correlaciones.csv` |
| P4 | ¿Cómo se distribuyen los ejemplares según el tamaño de la flor? | `resultados/tabla_p4_categorias_tamano.csv` y `tabla_p4_cruce_especie_tamano.csv` |

## Transformaciones aplicadas

1. Verificación de tipos contra los documentados por el dataset (sin desajustes).
2. Renombrar las seis columnas al español con la unidad en el nombre.
3. Normalizar la especie: quitar el prefijo `Iris-` y pasar a minúscula (150 valores).
4. Control de valores faltantes: ninguno detectado, sin tratamiento.
5. Control de duplicados: dos grupos con medidas idénticas (5 flores); se conservan porque son ejemplares distintos.
6. Control de atípicos con la regla 1,5 × RIC: 4 anchos de sépalo fuera del rango; se conservan tras revisarlos.
7. Descartar el identificador numérico; ninguna fila eliminada (150 en todo momento).

## Enriquecimiento

Cuatro variables calculadas sobre las medidas existentes (sin fuentes externas):
`area_sepalo_cm2`, `area_petalo_cm2`, `ratio_petalo` y `tamano_flor` (categoría
Pequeña / Media / Grande por terciles del área del pétalo, con cortes en 2,52 y
7,71 cm²).

## Ejecución y archivos generados

```bash
cd AE3 && jupyter nbconvert --to notebook --execute --inplace Gonzalez_Jesus_AE3.ipynb
```

O abrir el cuaderno y usar *Run All*. La ejecución regenera:

| Archivo | Contenido |
| --- | --- |
| `datos/dataset_preparado.csv` | DataFrame final: 150 filas × 9 columnas |
| `resultados/tabla_p1…p4_*.csv` | Cinco tablas de resultados, una o dos por pregunta |
| `resultados/resumen_dataset_ae3.txt` | Resumen descriptivo del DataFrame final, generado con `DatasetSummarizer` |

La integración continua del repositorio (`ci.yml`) ejecuta este cuaderno de
principio a fin en `ubuntu-latest` y `windows-latest` y comprueba que los
archivos se regeneren, así que la compatibilidad con Linux queda validada en
cada cambio.

El cuaderno termina con 7 comprobaciones automáticas (totales, porcentajes y
coincidencia de los CSV exportados con lo calculado), todas en verde en la
ejecución entregada.

## Documento de avance

`doc/Gonzalez_Jesus_AE3.docx` registra la metodología, las reglas de calidad, el
diccionario actualizado, los resultados con su discusión y las conclusiones del
avance. Su contenido coincide con el cuaderno y con los archivos exportados.
