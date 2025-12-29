import streamlit as st
import pandas as pd
from db.mongo import get_mongo_client

# =============================
# CONFIGURACIÓN DE PÁGINA
# =============================
st.set_page_config(page_title="Análisis de Atención", layout="wide")

st.title("📊 Análisis del Nivel de Atención Estudiantil")

st.markdown(
    """
    Este módulo presenta un análisis estadístico descriptivo de los registros
    obtenidos por el sistema de monitoreo de atención en el aula, integrando
    información académica como horarios, asignaturas y carreras.
    """
)

st.divider()

# =============================
# CONEXIÓN A MONGODB
# =============================
try:
    client = get_mongo_client(modo="atlas")
    db = client["FocusMeter"]

    st.success("✅ Conectado a MongoDB Atlas")

except Exception as e:
    st.error("❌ Error al conectar con MongoDB")
    st.exception(e)
    st.stop()

# =============================
# PIPELINE DE AGREGACIÓN (JOIN REAL)
# =============================
pipeline = [
    # JOIN con horarios
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

    # JOIN con asignaturas
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

    # JOIN con carreras
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

    # PROYECCIÓN FINAL
    {
        "$project": {
            "_id": 0,
            "fecha_deteccion": 1,
            "hora_deteccion": 1,
            "num_estudiantes_detectados": 1,
            "porcentaje_estimado_atencion": 1,
            "nombre_asignatura": "$asignatura.nombre_asignatura",
            "periodo_academico": "$asignatura.periodo_academico",
            "num_ciclo": "$asignatura.num_ciclo",
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
    st.warning("⚠️ No existen registros válidos para el análisis.")
    st.stop()

df = pd.DataFrame(data)

# Conversión de fechas y horas
df["fecha_deteccion"] = pd.to_datetime(df["fecha_deteccion"])
df["hora_deteccion"] = pd.to_datetime(df["hora_deteccion"], format="%H:%M:%S").dt.time

st.divider()

# =============================
# KPIs GENERALES
# =============================
st.subheader("📌 Indicadores Generales")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Nivel promedio de atención (%)",
    f"{df['porcentaje_estimado_atencion'].mean():.2f}"
)

col2.metric(
    "Total de registros",
    len(df)
)

col3.metric(
    "Promedio de estudiantes detectados",
    f"{df['num_estudiantes_detectados'].mean():.0f}"
)

st.divider()

# =============================
# DISTRIBUCIÓN DE ATENCIÓN
# =============================
st.subheader("📊 Distribución del Nivel de Atención")

st.bar_chart(
    df["porcentaje_estimado_atencion"],
    height=300
)

st.caption("Distribución de los porcentajes de atención detectados.")

st.divider()

# =============================
# EVOLUCIÓN TEMPORAL
# =============================
st.subheader("⏱️ Evolución del Nivel de Atención en el Tiempo")

df_time = (
    df.set_index("fecha_deteccion")
      .resample("D")
      .mean(numeric_only=True)
)

st.line_chart(
    df_time["porcentaje_estimado_atencion"],
    height=300
)

st.caption("Promedio diario del nivel de atención.")

st.divider()

# =============================
# ANÁLISIS POR ASIGNATURA
# =============================
st.subheader("📚 Nivel de Atención por Asignatura")

df_asignatura = (
    df.groupby("nombre_asignatura")["porcentaje_estimado_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_asignatura)

st.divider()

# =============================
# ANÁLISIS POR CARRERA
# =============================
st.subheader("🎓 Nivel de Atención por Carrera")

df_carrera = (
    df.groupby("nombre_carrera")["porcentaje_estimado_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_carrera)

st.caption(
    "Comparación del nivel promedio de atención entre carreras académicas."
)

st.divider()

# =============================
# TABLA FINAL
# =============================
st.subheader("📋 Registros Consolidados")

st.dataframe(
    df.sort_values("fecha_deteccion", ascending=False),
    use_container_width=True
)
