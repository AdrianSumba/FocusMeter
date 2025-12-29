import streamlit as st
import pandas as pd
import numpy as np
from db.mongo import get_mongo_client
from sklearn.linear_model import LinearRegression

# =============================
# CONFIGURACIÓN
# =============================
st.set_page_config(page_title="Proyección de Atención", layout="wide")

st.title("🔮 Proyecciones del Nivel de Atención Estudiantil")

st.markdown(
    """
    En esta sección se presentan proyecciones del nivel de atención estudiantil
    a partir de los registros históricos capturados por el sistema, utilizando
    un modelo de regresión lineal simple para estimar el comportamiento futuro.
    """
)

st.divider()

# =============================
# CONEXIÓN A MONGODB
# =============================
try:
    client = get_mongo_client(modo="atlas")
    db = client["FocusMeter"]
except Exception as e:
    st.error("❌ Error al conectar con MongoDB")
    st.exception(e)
    st.stop()

# =============================
# PIPELINE DE AGREGACIÓN (MISMA LÓGICA QUE ANÁLISIS)
# =============================
pipeline = [
    {
        "$lookup": {
            "from": "horarios",
            "let": {"id_h": "$id_horario"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$eq": ["$_id", {"$toObjectId": "$$id_h"}]
                        }
                    }
                }
            ],
            "as": "horario"
        }
    },
    {"$unwind": "$horario"},

    {
        "$lookup": {
            "from": "asignaturas",
            "let": {"id_asig": "$horario.id_asignatura"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$eq": ["$_id", {"$toObjectId": "$$id_asig"}]
                        }
                    }
                }
            ],
            "as": "asignatura"
        }
    },
    {"$unwind": "$asignatura"},

    {
        "$lookup": {
            "from": "carreras",
            "let": {"id_car": "$asignatura.id_carrera"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$eq": ["$_id", {"$toObjectId": "$$id_car"}]
                        }
                    }
                }
            ],
            "as": "carrera"
        }
    },
    {"$unwind": "$carrera"},

    {
        "$project": {
            "_id": 0,
            "fecha_deteccion": 1,
            "hora_deteccion": 1,
            "porcentaje_estimado_atencion": 1,
            "nombre_asignatura": "$asignatura.nombre_asignatura",
            "nombre_carrera": {
                "$ifNull": ["$carrera.nombre_carrera", "$carrera.nombre"]
            }
        }
    }
]

# =============================
# OBTENER DATOS
# =============================
data = list(db["registros_atencion"].aggregate(pipeline))

if len(data) < 10:
    st.warning("⚠️ No existen suficientes registros para generar proyecciones confiables.")
    st.stop()

df = pd.DataFrame(data)

# =============================
# CONSTRUCCIÓN DE TIMESTAMP REAL
# =============================
df["fecha_deteccion"] = pd.to_datetime(df["fecha_deteccion"])
df["hora_deteccion"] = pd.to_datetime(df["hora_deteccion"], format="%H:%M:%S").dt.time

df["timestamp"] = df.apply(
    lambda row: pd.Timestamp.combine(row["fecha_deteccion"], row["hora_deteccion"]),
    axis=1
)

df = df.sort_values("timestamp")

st.divider()

# =============================
# FILTROS OPCIONALES
# =============================
st.subheader("🎛️ Filtros")

carrera_sel = st.selectbox(
    "Seleccionar carrera",
    ["Todas"] + sorted(df["nombre_carrera"].unique().tolist())
)

if carrera_sel != "Todas":
    df = df[df["nombre_carrera"] == carrera_sel]

# =============================
# PREPARACIÓN DE DATOS
# =============================
df["tiempo"] = (df["timestamp"] - df["timestamp"].min()).dt.total_seconds()

X = df[["tiempo"]]
y = df["porcentaje_estimado_atencion"]

# =============================
# ENTRENAMIENTO DEL MODELO
# =============================
modelo = LinearRegression()
modelo.fit(X, y)

# =============================
# PROYECCIÓN FUTURA
# =============================
horizonte_min = st.slider(
    "Horizonte de proyección (minutos)",
    min_value=5,
    max_value=60,
    value=15,
    step=5
)

futuro_seg = np.arange(
    X["tiempo"].max(),
    X["tiempo"].max() + horizonte_min * 60,
    60
).reshape(-1, 1)

predicciones = modelo.predict(futuro_seg)

df_futuro = pd.DataFrame({
    "timestamp": pd.date_range(
        start=df["timestamp"].max(),
        periods=len(predicciones),
        freq="1min"
    ),
    "porcentaje_estimado_atencion": predicciones
})

st.divider()

# =============================
# VISUALIZACIÓN
# =============================
st.subheader("📉 Proyección del Nivel de Atención")

df_plot = pd.concat([
    df[["timestamp", "porcentaje_estimado_atencion"]],
    df_futuro
])

df_plot = df_plot.set_index("timestamp")

st.line_chart(
    df_plot,
    height=350
)

st.caption(
    "La proyección se basa en una regresión lineal simple aplicada a los datos históricos. "
    "Los valores futuros representan una estimación del comportamiento esperado del nivel de atención."
)

st.divider()

# =============================
# INTERPRETACIÓN
# =============================
st.subheader("🧠 Interpretación del Modelo")

st.write(
    f"""
    - Tendencia estimada: **{'creciente' if modelo.coef_[0] > 0 else 'decreciente'}**
    - Pendiente del modelo: **{modelo.coef_[0]:.6f}**
    - Nivel de atención esperado al final del horizonte:
      **{predicciones[-1]:.2f}%**
    """
)

st.info(
    "Estas proyecciones tienen un carácter orientativo y dependen de la cantidad, "
    "frecuencia y estabilidad de los datos históricos disponibles."
)
