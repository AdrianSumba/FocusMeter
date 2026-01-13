import threading

class EstadoCompartido:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_frame = None
        self.ultimo_jpeg = None
        self.ultimas_metricas = None
        self.ts_ultima_actualizacion = 0.0
        self.metrics = {
            "estimacion_atencion": 0,
            "estudiantes_detectados": 0,
            "aula": "",
            "docente": "",
            "materia": "",
            "carrera": "",
            "hora_inicio": "",
            "hora_fin": ""
        }

STATE = EstadoCompartido()
