import streamlit as st
import cv2
import threading
from ultralytics import YOLO
import time

# =============================
# CONFIGURACIÓN Y ESTADO GLOBAL
# =============================
MODEL_PATH = "app/extras/best.pt"

# Clase para gestionar la cámara en un hilo separado
class VideoCaptureThread:
    def __init__(self, index):
        self.cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        self.model = YOLO(MODEL_PATH)
        self.frame = None
        self.nivel_atencion = 0
        self.running = True
        self.lock = threading.Lock() # Para evitar conflictos de lectura/escritura

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Inferencia YOLO en el hilo
            results = self.model(frame, conf=0.5, verbose=False)
            annotated_frame = results[0].plot()

            # Cálculo de lógica de atención
            atentos = 0
            boxes = results[0].boxes
            total = len(boxes)
            for box in boxes:
                if self.model.names[int(box.cls[0])].lower() in ["atento", "attentive"]:
                    atentos += 1
            
            # Actualizar variables compartidas de forma segura
            with self.lock:
                self.frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                self.nivel_atencion = atentos / total if total > 0 else 0

    def stop(self):
        self.running = False
        self.cap.release()

# =============================
# SINGLETON PARA EL HILO
# =============================
# Usamos cache_resource para que el hilo no se reinicie al interactuar con la web
@st.cache_resource
def get_video_thread():
    # Probamos índice 2 (USB) o 0 (Integrada)
    for idx in [2, 0]:
        test_cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if test_cap.isOpened():
            test_cap.release()
            thread = VideoCaptureThread(idx)
            thread.start()
            return thread
    return None

# =============================
# INTERFAZ STREAMLIT (VISTA)
# =============================
st.set_page_config(page_title="Monitor de Atención", layout="wide")
st.title("📹 Monitoreo en Tiempo Real (Procesamiento Independiente)")

video_thread = get_video_thread()

if video_thread is None:
    st.error("❌ No se pudo inicializar ninguna cámara en el servidor.")
    st.stop()

# Layout de la vista
col_vid, col_stats = st.columns([3, 1])

with col_vid:
    image_placeholder = st.empty()

with col_stats:
    st.subheader("Estadísticas")
    semaforo = st.empty()
    st.info("El modelo está corriendo permanentemente en el servidor.")

# Bucle de la Vista (Streamlit)
while True:
    # Leer datos del hilo sin bloquearlo
    with video_thread.lock:
        current_frame = video_thread.frame
        nivel = video_thread.nivel_atencion

    # Actualizar imagen si hay frame disponible
    if current_frame is not None:
        image_placeholder.image(current_frame, channels="RGB", use_container_width=True)

    # Actualizar semáforo
    if nivel >= 0.7:
        semaforo.success(f"🟢 ALTA ({nivel:.0%})")
    elif nivel >= 0.4:
        semaforo.warning(f"🟡 MEDIA ({nivel:.0%})")
    else:
        semaforo.error(f"🔴 BAJA ({nivel:.0%})")

    # Pequeña pausa para no saturar la CPU del navegador
    time.sleep(0.03)