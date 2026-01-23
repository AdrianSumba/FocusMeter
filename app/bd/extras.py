from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd

from bd import mongo


_DIAS_EN = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miercoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sabado",
    "Sunday": "Domingo",
}

_DIAS_ORDEN_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


def _parse_hora(hora: Optional[str]) -> str:
    if not hora:
        return "00:00:00"
    h = str(hora).strip()
    if len(h) == 5:  # HH:MM
        return h + ":00"
    return h


def _parse_timestamp(fecha: Optional[str], hora: Optional[str]) -> Optional[datetime]:
    if not fecha:
        return None
    h = _parse_hora(hora)
    s = f"{fecha} {h}"
    # Intentos robustos
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def listar_carreras(periodo_academico: Optional[str] = None):
    return mongo.listar_carreras(periodo_academico=periodo_academico)


def obtener_registros_enriquecidos(
    carrera_id: Optional[str] = None,
    periodo_academico: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limite: Optional[int] = None,
) -> List[Dict[str, Any]]:

    return mongo.obtener_registros_atencion_enriquecidos(
        carrera_id=carrera_id,
        periodo_academico=periodo_academico,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limite=limite,
    )


def obtener_registros_df(
    carrera_id: Optional[str] = None,
    periodo_academico: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limite: Optional[int] = None,
) -> pd.DataFrame:

    registros = obtener_registros_enriquecidos(
        carrera_id=carrera_id,
        periodo_academico=periodo_academico,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limite=limite,
    )

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    df["num_estudiantes_detectados"] = pd.to_numeric(
        df.get("num_estudiantes_detectados", 0), errors="coerce"
    ).fillna(0)

    df["porcentaje_estimado_atencion"] = pd.to_numeric(
        df.get("porcentaje_estimado_atencion", 0), errors="coerce"
    ).fillna(0)

    df["timestamp"] = df.apply(
        lambda r: _parse_timestamp(r.get("fecha_deteccion"), r.get("hora_detecccion")),
        axis=1,
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()

    df["fecha"] = df["timestamp"].dt.date
    df["hora"] = df["timestamp"].dt.hour

    df["dia_semana"] = df["timestamp"].dt.day_name()
    df["dia_semana"] = df["dia_semana"].map(lambda x: _DIAS_EN.get(x, x))

    df["dia_semana"] = pd.Categorical(df["dia_semana"], categories=_DIAS_ORDEN_ES, ordered=True)

    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
