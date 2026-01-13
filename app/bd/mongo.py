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
    return coleccion.insert_one(registro)


def get_info_horario_actual(id_aula):
    info_horario = {
        "aula": "",
        "docente": "",
        "materia": "",
        "carrera": "",
        "id_horario": "",
        "hora_inicio": "",
        "hora_fin": ""
    }

    try:
        cliente = get_cliente_mongo()
        db = cliente[base]

        aulas = db["aulas"]
        horarios = db["horarios"]
        asignaturas = db["asignaturas"]
        docentes = db["docentes"]
        carreras = db["carreras"]

        aula = aulas.find_one({"_id": ObjectId(id_aula)})
        if not aula:
            return None

        ahora = datetime.now()
        hora_actual = ahora.time()

        dias_semana = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles",
            "Thursday": "Jueves", "Friday": "Viernes",
            "Saturday": "Sabado", "Sunday": "Domingo"
        }

        dia_actual_es = dias_semana.get(ahora.strftime("%A"))
        if not dia_actual_es:
            return None

        query = {
            "dia": dia_actual_es,
            "id_aula": id_aula
        }

        horarios_dia = horarios.find(query)

        for horario in horarios_dia:
            hora_inicio = datetime.strptime(horario["hora_inicio"], "%H:%M").time()
            hora_fin = datetime.strptime(horario["hora_fin"], "%H:%M").time()


            if hora_inicio <= hora_actual < hora_fin:
                asignatura = asignaturas.find_one(
                    {"_id": ObjectId(horario["id_asignatura"])}
                )
                if not asignatura:
                    continue

                docente = docentes.find_one(
                    {"_id": ObjectId(asignatura["id_docente"])}
                )
                carrera = carreras.find_one(
                    {"_id": ObjectId(asignatura["id_carrera"])}
                )

                info_horario["aula"] = aula["nombre_aula"]
                info_horario["docente"] = docente["nombre"] if docente else ""
                info_horario["materia"] = asignatura["nombre_asignatura"]
                info_horario["carrera"] = carrera["nombre_carrera"] if carrera else ""
                info_horario["id_horario"] = str(horario["_id"])
                info_horario["hora_inicio"] = horario["hora_inicio"]
                info_horario["hora_fin"] = horario["hora_fin"]

                return info_horario

        return None

    except Exception as e:
        print(f"Ocurrió un error al consultar MongoDB: {e}")
        return None
