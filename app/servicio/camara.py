import cv2

RTSP_URL = "rtsp://admin:Novat3ch@192.168.137.35:554/Streaming/Channels/101"

def open_rtsp():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir RTSP")
    return cap