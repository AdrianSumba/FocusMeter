import streamlit as st
import pandas as pd
from db.mongo import get_mongo_client

# =============================
# CONFIGURACIÓN
# =============================
st.set_page_config(page_title="Tendencias de Atención", layout="wide")

st.title("📈 Tendencias y Patrones del Nivel de Atención")

st.markdown(
    """
    En esta sección se analizan las tendencias temporales y patrones recurrentes
    del nivel de atención estudiantil, considerando la hora del día, el día de
    la semana y el contexto académico (asignatura y carrera).
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
# PIPELINE DE AGREGACIÓN (JOIN COMPLETO)
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

if not data:
    st.warning("⚠️ No existen registros suficientes para analizar tendencias.")
    st.stop()

df = pd.DataFrame(data)

# =============================
# CONSTRUCCIÓN DE TIMESTAMP
# =============================
df["fecha_deteccion"] = pd.to_datetime(df["fecha_deteccion"])
df["hora_deteccion"] = pd.to_datetime(
    df["hora_deteccion"], format="%H:%M:%S"
).dt.time

df["timestamp"] = df.apply(
    lambda row: pd.Timestamp.combine(row["fecha_deteccion"], row["hora_deteccion"]),
    axis=1
)

# =============================
# VARIABLES TEMPORALES
# =============================
df["hora"] = df["timestamp"].dt.hour
df["dia_semana"] = df["timestamp"].dt.day_name()

st.divider()

# =============================
# TENDENCIA POR HORA DEL DÍA
# =============================
st.subheader("⏰ Tendencia del Nivel de Atención por Hora")

df_hora = (
    df.groupby("hora")["porcentaje_estimado_atencion"]
      .mean()
)

st.line_chart(df_hora, height=300)

st.caption(
    "Promedio del nivel de atención según la hora del día, "
    "permitiendo identificar franjas horarias con mayor o menor concentración."
)

st.divider()

# =============================
# PATRÓN POR DÍA DE LA SEMANA
# =============================
st.subheader("📅 Patrón de Atención por Día de la Semana")

orden_dias = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

df_dia = (
    df.groupby("dia_semana")["porcentaje_estimado_atencion"]
      .mean()
      .reindex(orden_dias)
)

st.bar_chart(df_dia)

st.caption(
    "Comparación del nivel promedio de atención según el día de la semana."
)

st.divider()

# =============================
# PATRÓN POR ASIGNATURA
# =============================
st.subheader("📚 Patrón de Atención por Asignatura")

df_asignatura = (
    df.groupby("nombre_asignatura")["porcentaje_estimado_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_asignatura)

st.divider()

# =============================
# PATRÓN POR CARRERA
# =============================
st.subheader("🎓 Patrón de Atención por Carrera")

df_carrera = (
    df.groupby("nombre_carrera")["porcentaje_estimado_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_carrera)

st.divider()

# =============================
# TABLA COMBINADA ASIGNATURA - CARRERA
# =============================
st.subheader("📚🎓 Atención por Asignatura y Carrera")

df_combo = (
    df.groupby(
        ["nombre_asignatura", "nombre_carrera"]
    )["porcentaje_estimado_atencion"]
    .mean()
    .reset_index()
    .sort_values("porcentaje_estimado_atencion", ascending=False)
)

st.dataframe(
    df_combo,
    use_container_width=True
)

st.caption(
    "Tabla comparativa que permite identificar combinaciones de asignatura y carrera "
    "con mayores y menores niveles promedio de atención."
)
