# Hidden Gems EDA: Scouting Interactivo y Análisis de Mercado

Bienvenido a **Hidden Gems EDA**, un proyecto de Análisis Exploratorio de Datos (EDA) y aplicación interactiva diseñada para la dirección deportiva y el scouting moderno en el fútbol.

Este proyecto cruza datos de rendimiento táctico (FBref) con valoraciones económicas (Transfermarkt) para demostrar que, aplicando analítica avanzada y Machine Learning, es posible encontrar talento de alto rendimiento a bajo coste.

## Descripción del Proyecto

El mercado de fichajes actual sufre de una gran inflación, especialmente en perfiles ofensivos y en equipos de élite. **Hidden Gems EDA** proporciona un conjunto de herramientas interactivas para desmontar sesgos del mercado mediante cuatro módulos clave basados en nuestras hipótesis de investigación:

1. **Solidez y Eficiencia Defensiva:** Identificación de defensas y mediocentros en equipos de tabla media/baja cuyo rendimiento empírico (intercepciones, limpieza en el corte) supera al de jugadores de equipos Champions.

2. **Análisis de Sobreprecio:** Análisis comparativo del coste por demarcación y cuartil de mercado, evidenciando las asimetrías económicas entre posiciones ofensivas y defensivas.

3. **Producción Ofensiva vs Mercado:** Scouting de promesas (Sub-23, < 5M€) y ponderación de su rendimiento (Goles y Asistencias p/90 ajustados por coeficiente UEFA) para compararlos visualmente con los umbrales históricos de los cuartiles de élite.

4. **AI Scout Pro (Clones Estadísticos):** Un motor de Machine Learning que utiliza **Similitud del Coseno** y Z-Score sobre métricas normalizadas a 90 minutos para encontrar los 'clones estadísticos' exactos de cualquier jugador, eliminando el sesgo del sistema de juego o la posesión de su equipo.

> *"El mercado dicta el precio, pero los datos revelan el valor: el talento asequible existe para quienes saben **dónde, cómo y para qué buscar**."*

## Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

```
HiddenGemsEDA/
│
├── dataset_transfermarkt/       # Directorio con los CSVs extraídos y procesados
│
├── Hipotesis_1.ipynb            # Notebook EDA: Eficiencia Defensiva y Riesgo
├── Hipotesis_2.ipynb            # Notebook EDA: Sobreprecio por Demarcación
├── Hipotesis_3.ipynb            # Notebook EDA: Producción Ofensiva y AI Scout Pro
│
├── app.py                       # Aplicación interactiva principal en Streamlit
├── requirements.txt             # Dependencias del proyecto
├── README.md
└── .gitignore                   # Archivos ignorados por Git


```
## PRIMER PASO DESCARGAR DE LA CARPETA DE DRIVE DEL ENLACE Y DESCOMPRIMIRLA CON EL NOMBRE QUE TIENE PARA SU CORRECTA UTILIZACIÓN

** https://drive.google.com/drive/folders/1-0UaUF31vl0jIp71guBra3jBsIhe210N?usp=drive_link **

## Instalación y Uso

Para ejecutar este proyecto en tu entorno local, sigue estos pasos:

### 1. Clonar el repositorio

```
git clone https://github.com/tu-usuario/HiddenGemsEDA.git
cd HiddenGemsEDA


```

### 2. Instalar las dependencias

Asegúrate de tener Python 3.9+ instalado. Ejecuta el siguiente comando para instalar las librerías necesarias:

```
pip install -r requirements.txt


```

### 3. Descomprimir los datos (Opcional)

La aplicación `app.py` está configurada para descargar automáticamente los datos necesarios de Google Drive si no los encuentra. Sin embargo, si deseas usar los notebooks de Jupyter, asegúrate de descomprimir `transfermarkt_archive.zip` en la carpeta `dataset_transfermarkt/`.

### 4. Lanzar la aplicación

Ejecuta la app de Streamlit con el siguiente comando:

```
streamlit run app.py


```

Se abrirá automáticamente una pestaña en tu navegador web con el Dashboard interactivo.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3

* **Interfaz Interactiva:** [Streamlit](https://streamlit.io/)

* **Manipulación de Datos:** Pandas, NumPy

* **Motor SQL en Memoria:** [DuckDB](https://duckdb.org/)

* **Visualización de Datos:** Plotly (Express & Graph Objects), Seaborn, Matplotlib

* **Machine Learning:** Similitud del Coseno (Álgebra Lineal con NumPy)

* **Descarga de Datos:** gdown

## Fuentes de Datos

* **Transfermarkt Dataset:** Histórico de valoraciones de mercado, clubes, competiciones e información biográfica.

* **FBref (StatsBomb):** Estadísticas de rendimiento avanzado por jugador (90s, TklW, Int, Gls, Ast, xG, etc.) de la temporada 2025/2026.
