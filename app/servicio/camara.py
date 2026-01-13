import cv2

RTSP_URL = "rtsp://admin:Novat3ch@192.168.137.159:554/Streaming/Channels/101"

def open_rtsp():
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir RTSP")
    return cap