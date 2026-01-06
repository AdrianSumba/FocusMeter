from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

base = "FocusMeter"

def get_cliente_mongo():
    uri = (
        "mongodb+srv://Adrian_bd:Administrador31.@base.f1r4j33.mongodb.net/"
        "FocusMeter?retryWrites=true&w=majority&appName=Base"
    )
    return MongoClient(uri)


def insertar_registro_atencion(registro):
    

    cliente = get_cliente_mongo()
    coleccion = cliente[base]["registros_atencion"]

    documento = {
        "num_estudiantes_detectados": registro.num_estudiantes_detectados,
        "porcentaje_estimado_atencion": registro.porcentaje_estimado_atencion,
        "porcentajes_etiquetas": registro.porcentajes_etiquetas,
        "num_deteccion_etiquetas": registro.num_deteccion_etiquetas,
        "fecha_deteccion": registro.fecha_deteccion,
        "hora_detecccion": registro.hora_detecccion,
        "id_horario": registro.id_horario
    }

    return coleccion.insert_one(documento)