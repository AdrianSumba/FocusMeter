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


# =============================================================================
#  EXTRA: Gestión Académica (Docentes / Carreras / Aulas / Asignaturas / Horarios)
#  Nota: Se agrega sin modificar la lógica existente.
# =============================================================================

from datetime import timedelta
import re
from bson import ObjectId


def _oid_from_str(value: Optional[str]) -> Optional[ObjectId]:
    try:
        if not value:
            return None
        return ObjectId(str(value))
    except Exception:
        return None


def _norm_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    # normaliza espacios; mantiene mayúsculas/minúsculas del usuario
    return re.sub(r"\s+", " ", str(s)).strip()


def listar_periodos_academicos() -> List[str]:
    """Retorna periodos académicos distintos presentes en asignaturas."""
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    periodos = db["asignaturas"].distinct("periodo_academico")
    periodos = [p for p in periodos if p]
    # ordena de forma natural (2025-2P > 2025-1P > 2024-2P ...)
    def _key(x: str):
        m = re.match(r"(\d{4})-(\d+)(.*)", str(x))
        if not m:
            return (0, 0, str(x))
        return (int(m.group(1)), int(m.group(2)), m.group(3))
    return sorted(periodos, key=_key, reverse=True)


def listar_docentes() -> List[Dict[str, str]]:
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    docs = list(db["docentes"].find({}, {"nombre": 1}))
    return [{"id": str(d["_id"]), "nombre": d.get("nombre", "")} for d in sorted(docs, key=lambda x: x.get("nombre", ""))]


def listar_aulas() -> List[Dict[str, str]]:
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    aulas = list(db["aulas"].find({}, {"nombre_aula": 1}))
    return [{"id": str(a["_id"]), "nombre": a.get("nombre_aula", "")} for a in sorted(aulas, key=lambda x: x.get("nombre_aula", ""))]


def listar_carreras_simple() -> List[Dict[str, str]]:
    """Lista todas las carreras (sin filtro por periodo)."""
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    carreras = list(db["carreras"].find({}, {"nombre_carrera": 1}))
    return [{"id": str(c["_id"]), "nombre": c.get("nombre_carrera", "")} for c in sorted(carreras, key=lambda x: x.get("nombre_carrera", ""))]


def listar_asignaturas(
    periodo_academico: Optional[str] = None,
    id_carrera: Optional[str] = None,
    id_docente: Optional[str] = None,
) -> List[Dict[str, Any]]:
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    q: Dict[str, Any] = {}
    if periodo_academico:
        q["periodo_academico"] = str(periodo_academico)
    if id_carrera:
        q["id_carrera"] = str(id_carrera)
    if id_docente:
        q["id_docente"] = str(id_docente)

    asigns = list(
        db["asignaturas"].find(
            q,
            {
                "nombre_asignatura": 1,
                "id_docente": 1,
                "id_carrera": 1,
                "periodo_academico": 1,
                "num_ciclo": 1,
            },
        )
    )
    asigns_sorted = sorted(
        asigns,
        key=lambda x: (
            str(x.get("periodo_academico", "")),
            int(x.get("num_ciclo") or 0),
            str(x.get("nombre_asignatura", "")),
        ),
        reverse=False,
    )
    return [
        {
            "id": str(a["_id"]),
            "nombre": a.get("nombre_asignatura", ""),
            "id_docente": a.get("id_docente", ""),
            "id_carrera": a.get("id_carrera", ""),
            "periodo_academico": a.get("periodo_academico", ""),
            "num_ciclo": a.get("num_ciclo", None),
        }
        for a in asigns_sorted
    ]


def _find_one_ci(col, field: str, value: str) -> Optional[Dict[str, Any]]:
    value_n = _norm_text(value)
    if not value_n:
        return None
    return col.find_one({field: {"$regex": f"^{re.escape(value_n)}$", "$options": "i"}})


def crear_docente_si_no_existe(nombre: str) -> Dict[str, Any]:
    """Crea docente si no existe (case-insensitive). Retorna {'id', 'created'}."""
    nombre_n = _norm_text(nombre)
    if not nombre_n:
        raise ValueError("Nombre de docente vacío.")
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    col = db["docentes"]
    ex = _find_one_ci(col, "nombre", nombre_n)
    if ex:
        return {"id": str(ex["_id"]), "created": False}
    res = col.insert_one({"nombre": nombre_n})
    return {"id": str(res.inserted_id), "created": True}


def crear_aula_si_no_existe(nombre_aula: str) -> Dict[str, Any]:
    nombre_n = _norm_text(nombre_aula)
    if not nombre_n:
        raise ValueError("Nombre de aula vacío.")
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    col = db["aulas"]
    ex = _find_one_ci(col, "nombre_aula", nombre_n)
    if ex:
        return {"id": str(ex["_id"]), "created": False}
    res = col.insert_one({"nombre_aula": nombre_n})
    return {"id": str(res.inserted_id), "created": True}


def crear_carrera_si_no_existe(nombre_carrera: str) -> Dict[str, Any]:
    nombre_n = _norm_text(nombre_carrera)
    if not nombre_n:
        raise ValueError("Nombre de carrera vacío.")
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    col = db["carreras"]
    ex = _find_one_ci(col, "nombre_carrera", nombre_n)
    if ex:
        return {"id": str(ex["_id"]), "created": False}
    res = col.insert_one({"nombre_carrera": nombre_n})
    return {"id": str(res.inserted_id), "created": True}


def crear_asignatura_si_no_existe(
    nombre_asignatura: str,
    id_docente: str,
    id_carrera: str,
    periodo_academico: str,
    num_ciclo: int,
) -> Dict[str, Any]:
    nombre_n = _norm_text(nombre_asignatura)
    periodo_n = _norm_text(periodo_academico)
    if not nombre_n:
        raise ValueError("Nombre de asignatura vacío.")
    if not id_docente or not id_carrera:
        raise ValueError("Debe seleccionar docente y carrera.")
    if not periodo_n:
        raise ValueError("Periodo académico vacío.")
    try:
        num_ciclo_int = int(num_ciclo)
    except Exception:
        raise ValueError("Número de ciclo inválido.")

    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]
    col = db["asignaturas"]

    # Búsqueda exacta (case-insensitive) por nombre + docente + carrera + periodo + ciclo
    q = {
        "id_docente": str(id_docente),
        "id_carrera": str(id_carrera),
        "periodo_academico": periodo_n,
        "num_ciclo": num_ciclo_int,
        "nombre_asignatura": {"$regex": f"^{re.escape(nombre_n)}$", "$options": "i"},
    }
    ex = col.find_one(q)
    if ex:
        return {"id": str(ex["_id"]), "created": False}

    doc = {
        "nombre_asignatura": nombre_n,
        "id_docente": str(id_docente),
        "id_carrera": str(id_carrera),
        "periodo_academico": periodo_n,
        "num_ciclo": num_ciclo_int,
    }
    res = col.insert_one(doc)
    return {"id": str(res.inserted_id), "created": True}


def obtener_horarios_enriquecidos(
    periodo_academico: Optional[str] = None,
    id_aula: Optional[str] = None,
    id_docente: Optional[str] = None,
    id_carrera: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Horarios con joins a asignatura, docente, carrera, aula."""
    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]

    pipeline: List[Dict[str, Any]] = []

    # Lookup asignatura
    pipeline.extend(
        [
            {
                "$addFields": {
                    "_asig_oid": {
                        "$convert": {
                            "input": "$id_asignatura",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    }
                }
            },
            {
                "$lookup": {
                    "from": "asignaturas",
                    "localField": "_asig_oid",
                    "foreignField": "_id",
                    "as": "asignatura",
                }
            },
            {"$unwind": {"path": "$asignatura", "preserveNullAndEmptyArrays": True}},
        ]
    )

    # Lookup docente, carrera y aula
    pipeline.extend(
        [
            {
                "$addFields": {
                    "_doc_oid": {
                        "$convert": {
                            "input": "$asignatura.id_docente",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                    "_car_oid": {
                        "$convert": {
                            "input": "$asignatura.id_carrera",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                    "_aula_oid": {
                        "$convert": {
                            "input": "$id_aula",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                }
            },
            {
                "$lookup": {
                    "from": "docentes",
                    "localField": "_doc_oid",
                    "foreignField": "_id",
                    "as": "docente",
                }
            },
            {"$unwind": {"path": "$docente", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "carreras",
                    "localField": "_car_oid",
                    "foreignField": "_id",
                    "as": "carrera",
                }
            },
            {"$unwind": {"path": "$carrera", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "aulas",
                    "localField": "_aula_oid",
                    "foreignField": "_id",
                    "as": "aula",
                }
            },
            {"$unwind": {"path": "$aula", "preserveNullAndEmptyArrays": True}},
        ]
    )

    match: Dict[str, Any] = {}
    if periodo_academico:
        match["asignatura.periodo_academico"] = str(periodo_academico)
    if id_aula:
        match["id_aula"] = str(id_aula)
    if id_docente:
        match["asignatura.id_docente"] = str(id_docente)
    if id_carrera:
        match["asignatura.id_carrera"] = str(id_carrera)
    if match:
        pipeline.append({"$match": match})

    pipeline.append(
        {
            "$project": {
                "_id": 1,
                "dia": 1,
                "hora_inicio": 1,
                "hora_fin": 1,
                "id_aula": 1,
                "id_asignatura": 1,
                "asignatura": {
                    "_id": "$asignatura._id",
                    "nombre_asignatura": "$asignatura.nombre_asignatura",
                    "periodo_academico": "$asignatura.periodo_academico",
                    "num_ciclo": "$asignatura.num_ciclo",
                    "id_docente": "$asignatura.id_docente",
                    "id_carrera": "$asignatura.id_carrera",
                },
                "docente": {"_id": "$docente._id", "nombre": "$docente.nombre"},
                "carrera": {"_id": "$carrera._id", "nombre_carrera": "$carrera.nombre_carrera"},
                "aula": {"_id": "$aula._id", "nombre_aula": "$aula.nombre_aula"},
            }
        }
    )

    res = list(db["horarios"].aggregate(pipeline))
    # Orden: día, hora_inicio
    orden_dia = {d: i for i, d in enumerate(_DIAS_ORDEN_ES)}
    res.sort(key=lambda r: (orden_dia.get(r.get("dia", ""), 99), r.get("hora_inicio", "00:00"), r.get("hora_fin", "00:00")))
    # a dict simple
    out = []
    for r in res:
        out.append(
            {
                "id": str(r.get("_id")),
                "dia": r.get("dia", ""),
                "hora_inicio": r.get("hora_inicio", ""),
                "hora_fin": r.get("hora_fin", ""),
                "aula": (r.get("aula") or {}).get("nombre_aula", ""),
                "id_aula": r.get("id_aula", ""),
                "asignatura": (r.get("asignatura") or {}).get("nombre_asignatura", ""),
                "id_asignatura": r.get("id_asignatura", ""),
                "docente": (r.get("docente") or {}).get("nombre", ""),
                "id_docente": (r.get("asignatura") or {}).get("id_docente", ""),
                "carrera": (r.get("carrera") or {}).get("nombre_carrera", ""),
                "id_carrera": (r.get("asignatura") or {}).get("id_carrera", ""),
                "periodo_academico": (r.get("asignatura") or {}).get("periodo_academico", ""),
                "num_ciclo": (r.get("asignatura") or {}).get("num_ciclo", None),
            }
        )
    return out


def verificar_solapamiento_horario(
    periodo_academico: str,
    dia: str,
    hora_inicio: str,
    hora_fin: str,
    id_aula: Optional[str] = None,
    id_docente: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Verifica solapamiento por:
      - Aula (si id_aula se provee)
      - Docente (si id_docente se provee)
    El filtro por periodo se realiza vía asignaturas.periodo_academico.
    """
    periodo_n = _norm_text(periodo_academico)
    dia_n = _norm_text(dia)

    if not periodo_n or not dia_n:
        return []

    # Regla de solapamiento: existente.inicio < nuevo.fin AND existente.fin > nuevo.inicio
    expr_overlap = {
        "$and": [
            {"$lt": ["$hora_inicio", str(hora_fin)]},
            {"$gt": ["$hora_fin", str(hora_inicio)]},
        ]
    }

    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]

    # Un pipeline enriquecido y filtrado
    pipeline: List[Dict[str, Any]] = []

    pipeline.extend(
        [
            {"$match": {"dia": dia_n}},
            {"$addFields": {"_asig_oid": {"$convert": {"input": "$id_asignatura", "to": "objectId", "onError": None, "onNull": None}}}},
            {"$lookup": {"from": "asignaturas", "localField": "_asig_oid", "foreignField": "_id", "as": "asignatura"}},
            {"$unwind": {"path": "$asignatura", "preserveNullAndEmptyArrays": False}},
            {"$match": {"asignatura.periodo_academico": periodo_n}},
            {"$match": {"$expr": expr_overlap}},
        ]
    )

    or_filters = []
    if id_aula:
        or_filters.append({"id_aula": str(id_aula)})
    if id_docente:
        or_filters.append({"asignatura.id_docente": str(id_docente)})

    if or_filters:
        pipeline.append({"$match": {"$or": or_filters}})
    else:
        return []

    # Lookup para nombres
    pipeline.extend(
        [
            {"$addFields": {
                "_doc_oid": {"$convert": {"input": "$asignatura.id_docente", "to": "objectId", "onError": None, "onNull": None}},
                "_car_oid": {"$convert": {"input": "$asignatura.id_carrera", "to": "objectId", "onError": None, "onNull": None}},
                "_aula_oid": {"$convert": {"input": "$id_aula", "to": "objectId", "onError": None, "onNull": None}},
            }},
            {"$lookup": {"from": "docentes", "localField": "_doc_oid", "foreignField": "_id", "as": "docente"}},
            {"$unwind": {"path": "$docente", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "carreras", "localField": "_car_oid", "foreignField": "_id", "as": "carrera"}},
            {"$unwind": {"path": "$carrera", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "aulas", "localField": "_aula_oid", "foreignField": "_id", "as": "aula"}},
            {"$unwind": {"path": "$aula", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 1,
                "dia": 1,
                "hora_inicio": 1,
                "hora_fin": 1,
                "id_aula": 1,
                "id_asignatura": 1,
                "asignatura": {"nombre_asignatura": "$asignatura.nombre_asignatura", "id_docente": "$asignatura.id_docente", "id_carrera": "$asignatura.id_carrera", "periodo_academico": "$asignatura.periodo_academico"},
                "docente": {"nombre": "$docente.nombre"},
                "carrera": {"nombre_carrera": "$carrera.nombre_carrera"},
                "aula": {"nombre_aula": "$aula.nombre_aula"},
            }},
        ]
    )

    conflicts = list(db["horarios"].aggregate(pipeline))
    out = []
    for c in conflicts:
        out.append(
            {
                "id": str(c.get("_id")),
                "dia": c.get("dia", ""),
                "hora_inicio": c.get("hora_inicio", ""),
                "hora_fin": c.get("hora_fin", ""),
                "aula": (c.get("aula") or {}).get("nombre_aula", ""),
                "docente": (c.get("docente") or {}).get("nombre", ""),
                "carrera": (c.get("carrera") or {}).get("nombre_carrera", ""),
                "asignatura": (c.get("asignatura") or {}).get("nombre_asignatura", ""),
                "periodo_academico": (c.get("asignatura") or {}).get("periodo_academico", ""),
                "match_aula": bool(id_aula and str(c.get("id_aula")) == str(id_aula)),
                "match_docente": bool(id_docente and (c.get("asignatura") or {}).get("id_docente") == str(id_docente)),
            }
        )
    return out


def crear_horario(
    id_asignatura: str,
    id_aula: str,
    dia: str,
    hora_inicio: str,
    hora_fin: str,
    periodo_academico: Optional[str] = None,
    id_docente: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inserta un horario si no hay solapamiento (aula/docente) para el mismo periodo.
    - periodo_academico: si se omite, se intenta deducir desde asignatura.
    - id_docente: opcional (si no se pasa, se deduce desde asignatura).
    """
    dia_n = _norm_text(dia)
    hi = _norm_text(hora_inicio)
    hf = _norm_text(hora_fin)

    if not (id_asignatura and id_aula and dia_n and hi and hf):
        raise ValueError("Faltan datos para crear horario.")
    if hi >= hf:
        raise ValueError("La hora de inicio debe ser menor que la hora fin.")

    cliente = mongo.get_cliente_mongo()
    db = cliente[mongo.base]

    # Deducir periodo y docente desde asignatura si hace falta
    asig = db["asignaturas"].find_one({"_id": _oid_from_str(id_asignatura)}, {"periodo_academico": 1, "id_docente": 1})
    if not asig:
        raise ValueError("Asignatura no encontrada.")
    periodo_eff = _norm_text(periodo_academico) or _norm_text(asig.get("periodo_academico"))
    docente_eff = _norm_text(id_docente) or _norm_text(asig.get("id_docente"))

    conflicts = verificar_solapamiento_horario(
        periodo_academico=periodo_eff,
        dia=dia_n,
        hora_inicio=hi,
        hora_fin=hf,
        id_aula=id_aula,
        id_docente=docente_eff,
    )
    if conflicts:
        return {"inserted": False, "conflicts": conflicts}

    doc = {
        "id_asignatura": str(id_asignatura),
        "id_aula": str(id_aula),
        "hora_inicio": hi,
        "hora_fin": hf,
        "dia": dia_n,
    }
    res = db["horarios"].insert_one(doc)
    return {"inserted": True, "id": str(res.inserted_id), "conflicts": []}
