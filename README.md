#PROYECTO FINAL CICLO 4: FOCUS METER

- Entorno python: focusmeterv2 con python 3.10.19

- Ejecutar streaming auxiliar:
    - cd app/aux_streaming
    - python -m http.server 5500

- Ejecutar servicio:
    - cd app
    - uvicorn main_servicio_app:app --host 0.0.0.0 --port 8000