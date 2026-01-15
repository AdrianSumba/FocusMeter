import cv2
import time
import traceback
import torch
import sys
import os
import threading
from datetime import datetime
from ultralytics import YOLO

from servicio.camara import open_rtsp
from servicio.estado_compartido import STATE
from servicio.com_serial import SerialManager
from bd.mongo import insertar_registro_atencion, get_info_horario_actual


ID_AULA = "694c11148cd1e969b0edc8a0"


MODEL_PATH = "servicio/modelo/best.pt"

RTSP_READ_TIMEOUT = 2.0
RECONNECT_DELAY = 1.5
MAX_FPS_DELAY = 0.03
CUDA_CLEAN_INTERVAL = 150
STREAM_RES = (640, 480)
JPEG_QUALITY_STREAM = 80

EVIDENCIAS_PATH = "extras/evidencias"
os.makedirs(EVIDENCIAS_PATH, exist_ok=True)

PESOS_ATENCION = {
    "attentive": 1.0,
    "hand_rising": 1.0,
    "human": 0.5,
    "daydreaming": 0.3,
    "distracted": 0.1,
    "sleepy": 0.0,
    "bullying": 0.0,
    "phone_use": 0.0
}

info_horario_actual = None
hora_nueva_clase = None


def iniciar_hilo_lector_rtsp(get_cap_func, safe_read_func):
    estado_lector = {
        "cap": None,
        "frame": None,
        "lock": threading.Lock(),
        "conectado": False,
        "detener": False,
    }

    def _loop():
        while not estado_lector["detener"]:
            try:
                if estado_lector["cap"] is None:
                    print("[RTSP] Conectando...")
                    estado_lector["cap"] = get_cap_func()
                    estado_lector["conectado"] = True

                ret, frame = safe_read_func(estado_lector["cap"])
                if not ret:
                    print("[RTSP] Timeout, reconectando...")
                    try:
                        estado_lector["cap"].release()
                    except Exception:
                        pass
                    estado_lector["cap"] = None
                    estado_lector["conectado"] = False
                    time.sleep(RECONNECT_DELAY)
                    continue

                with estado_lector["lock"]:
                    estado_lector["frame"] = frame

            except Exception:
                traceback.print_exc()
                try:
                    if estado_lector["cap"] is not None:
                        estado_lector["cap"].release()
                except Exception:
                    pass
                estado_lector["cap"] = None
                estado_lector["conectado"] = False
                time.sleep(RECONNECT_DELAY)

    threading.Thread(target=_loop, daemon=True).start()
    return estado_lector


def safe_rtsp_read(cap, timeout=RTSP_READ_TIMEOUT):
    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret and frame is not None:
            return True, frame
        time.sleep(0.01)
    return False, None


def start_model_loop():
    global hora_nueva_clase, info_horario_actual

    print("[INIT] Iniciando modelo RTSP")

    # =======================
    # CARGA INICIAL DE HORARIO
    # =======================
    ahora_dt = datetime.now()
    hora_nueva_clase = ahora_dt.strftime("%H:00")
    info_horario_actual = get_info_horario_actual(ID_AULA)

    if info_horario_actual:
        with STATE.lock:
            STATE.metrics.update({
                "aula": info_horario_actual.get("aula", ""),
                "docente": info_horario_actual.get("docente", ""),
                "materia": info_horario_actual.get("materia", ""),
                "carrera": info_horario_actual.get("carrera", ""),
                "hora_inicio": info_horario_actual.get("hora_inicio", ""),
                "hora_fin": info_horario_actual.get("hora_fin", "")
            })

    try:
        model = YOLO(MODEL_PATH)
        class_names = model.names
        print("[INIT] Modelo YOLO cargado")
    except Exception:
        traceback.print_exc()
        return

    lector_rtsp = iniciar_hilo_lector_rtsp(open_rtsp, safe_rtsp_read)
    serial_mgr = SerialManager()
    frame_count = 0

    start_time_interval = time.time()
    interval_data = {
        "estudiantes_list": [],
        "atencion_list": [],
        "etiquetas_conteos": {},
        "inicio_fecha": "",
        "inicio_hora": ""
    }

    while True:
        try:
            ahora_dt = datetime.now()
            hora_actual_str = ahora_dt.strftime("%H:00")

            # =======================
            # ACTUALIZACIÓN HORARIA
            # =======================
            if hora_actual_str != hora_nueva_clase:
                info_horario_actual = get_info_horario_actual(ID_AULA)
                hora_nueva_clase = hora_actual_str

                if info_horario_actual:
                    with STATE.lock:
                        STATE.metrics.update({
                            "aula": info_horario_actual.get("aula", ""),
                            "docente": info_horario_actual.get("docente", ""),
                            "materia": info_horario_actual.get("materia", ""),
                            "carrera": info_horario_actual.get("carrera", ""),
                            "hora_inicio": info_horario_actual.get("hora_inicio", ""),
                            "hora_fin": info_horario_actual.get("hora_fin", "")
                        })

            # =======================
            # RTSP: obtener siempre el frame más reciente del hilo lector
            # =======================
            with lector_rtsp["lock"]:
                frame = None if lector_rtsp["frame"] is None else lector_rtsp["frame"].copy()

            if frame is None:
                time.sleep(0.01)
                continue

            # Inicializar intervalo cuando ya llega el primer frame válido
            if not interval_data["inicio_fecha"]:
                interval_data["inicio_fecha"] = ahora_dt.strftime("%Y-%m-%d")
                interval_data["inicio_hora"] = ahora_dt.strftime("%H:%M:%S")

            # =======================
            # INFERENCIA
            # =======================
            results = model(frame, conf=0.25, verbose=False)
            boxes = results[0].boxes

            total_detectados = len(boxes)
            suma_ponderada = 0.0
            conteo_frame = {}

            for box in boxes:
                cls = int(box.cls[0])
                label = class_names[cls].lower()
                conf = float(box.conf[0]) if hasattr(box, "conf") else 0.0

                conteo_frame[label] = conteo_frame.get(label, 0) + 1

                peso = PESOS_ATENCION.get(label, 0.0)
                suma_ponderada += peso

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 0) if peso >= 0.7 else (255, 255, 0) if peso >= 0.3 else (0, 0, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"{label} conf:{conf:.2f}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )

            estimacion_iap = (suma_ponderada / total_detectados * 100) if total_detectados > 0 else 0

            # =======================
            # ACUMULADORES POR MINUTO
            # =======================
            interval_data["estudiantes_list"].append(total_detectados)
            interval_data["atencion_list"].append(estimacion_iap)

            for lab, cant in conteo_frame.items():
                interval_data["etiquetas_conteos"].setdefault(lab, []).append(cant)

            # =======================
            # STATE
            # =======================
            frame_stream = cv2.resize(frame, STREAM_RES)
            ok_jpg, jpg = cv2.imencode(
                ".jpg",
                frame_stream,
                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY_STREAM],
            )
            jpeg_bytes = jpg.tobytes() if ok_jpg else None

            # =======================
            # STATE
            # =======================
            metricas_actuales = None
            with STATE.lock:
                STATE.last_frame = frame_stream
                STATE.ultimo_jpeg = jpeg_bytes
                STATE.metrics["estimacion_atencion"] = round(estimacion_iap, 2)
                STATE.metrics["estudiantes_detectados"] = total_detectados
                STATE.ts_ultima_actualizacion = time.time()
                # snapshot listo para lectura rápida
                STATE.ultimas_metricas = STATE.metrics.copy()
                metricas_actuales = STATE.ultimas_metricas

            # =======================
            # SERIAL
            # =======================
            serial_mgr.send(estimacion_iap)

            # =======================
            # INSERCIÓN + EVIDENCIA
            # =======================
            if time.time() - start_time_interval >= 60:
                timestamp = ahora_dt.strftime("%Y%m%d_%H%M%S")

                cv2.putText(
                    frame,
                    f"Atencion: {round(estimacion_iap, 2)}% | Estudiantes: {total_detectados}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2
                )

                cv2.imwrite(
                    os.path.join(EVIDENCIAS_PATH, f"evidencia_{timestamp}.jpg"),
                    frame
                )

                atencion_prom = sum(interval_data["atencion_list"]) / len(interval_data["atencion_list"])
                num_est_max = max(interval_data["estudiantes_list"])
                res_num_det = {k: max(v) for k, v in interval_data["etiquetas_conteos"].items()}

                documento = {
                    "num_estudiantes_detectados": num_est_max,
                    "porcentaje_estimado_atencion": round(atencion_prom, 2),
                    "num_deteccion_etiquetas": res_num_det,
                    "fecha_deteccion": interval_data["inicio_fecha"],
                    "hora_detecccion": interval_data["inicio_hora"],
                    "id_horario": info_horario_actual["id_horario"] if info_horario_actual else ""
                }

                insertar_registro_atencion(documento)

                start_time_interval = time.time()
                interval_data = {
                    "estudiantes_list": [],
                    "atencion_list": [],
                    "etiquetas_conteos": {},
                    "inicio_fecha": ahora_dt.strftime("%Y-%m-%d"),
                    "inicio_hora": ahora_dt.strftime("%H:%M:%S")
                }

                sys.stdout.write("\033[H\033[J")

            # =======================
            # LIMPIEZA GPU
            # =======================
            frame_count += 1
            if torch.cuda.is_available() and frame_count % CUDA_CLEAN_INTERVAL == 0:
                torch.cuda.empty_cache()

            time.sleep(MAX_FPS_DELAY)

        except Exception:
            traceback.print_exc()
            time.sleep(RECONNECT_DELAY)
