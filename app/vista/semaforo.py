# app/vista/semaforo.py
import time
from datetime import datetime

import requests
import streamlit as st

# =========================
# Configuración
# =========================
METRICS_URL = "http://localhost:8000/metrics"
REFRESH_SECONDS = 2  # "tiempo real" (puedes subir a 3-5 si quieres menos carga)
REQ_TIMEOUT = 1.2    # evita que Streamlit se cuelgue si el servicio no responde


# =========================
# Helpers
# =========================
@st.cache_data(ttl=1, show_spinner=False)  # cache muy corto para no saturar /metrics
def fetch_metrics() -> dict:
    r = requests.get(METRICS_URL, timeout=REQ_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _to_float(v, default=0.0) -> float:
    try:
        if v is None:
            return default
        if isinstance(v, str):
            v = v.strip().replace("%", "")
        return float(v)
    except Exception:
        return default


def semaforo_color(attention_pct: float) -> tuple[str, str]:
    """
    Reglas:
    - Rojo: < 70
    - Amarillo: >= 70 y < 80
    - Verde: >= 80
    """
    if attention_pct < 70:
        return ("ROJO", "#ef4444")
    if attention_pct < 80:
        return ("AMARILLO", "#f59e0b")
    return ("VERDE", "#22c55e")


def _get(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return default


def _fmt_dt(v) -> str:
    if not v:
        return "—"
    # Si ya viene como string del backend, lo respetamos
    if isinstance(v, str):
        return v
    # Si viene como timestamp/epoch
    try:
        return datetime.fromtimestamp(float(v)).isoformat(sep=" ", timespec="seconds")
    except Exception:
        return str(v)


# =========================
# UI
# =========================
st.set_page_config(page_title="Semáforo", layout="wide")

# CSS (cards elegantes + semáforo)
st.markdown(
    """
    <style>
      .fm-wrap { max-width: 1200px; margin: 0 auto; }
      .fm-title { font-size: 1.55rem; font-weight: 800; margin-bottom: .25rem; }
      .fm-sub { color: rgba(255,255,255,.7); margin-bottom: 1rem; }
      .fm-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
      .fm-card {
        grid-column: span 4;
        padding: 14px 16px;
        border-radius: 14px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(8px);
      }
      .fm-card h4 { margin: 0; font-size: .85rem; color: rgba(255,255,255,.72); font-weight: 700; }
      .fm-card .v { margin-top: 6px; font-size: 1.35rem; font-weight: 800; }
      .fm-card .s { margin-top: 2px; font-size: .85rem; color: rgba(255,255,255,.65); }
      .fm-wide { grid-column: span 12; }
      .fm-semaforo {
        display: flex; align-items: center; justify-content: space-between;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.06);
      }
      .fm-semaforo .left .label { font-size: .9rem; color: rgba(255,255,255,.70); font-weight: 700; }
      .fm-semaforo .left .state { font-size: 1.6rem; font-weight: 900; margin-top: 4px; }
      .fm-pill {
        padding: 6px 10px;
        border-radius: 999px;
        font-weight: 800;
        font-size: .9rem;
        border: 1px solid rgba(0,0,0,.12);
      }
      .fm-error {
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.25);
        color: rgba(255,255,255,.9);
      }
      /* Responsive */
      @media (max-width: 900px){
        .fm-card { grid-column: span 12; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="fm-wrap">', unsafe_allow_html=True)
st.markdown('<div class="fm-title">📊 Semáforo de Atención</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="fm-sub">Actualización en tiempo real (cada {REFRESH_SECONDS}s) solo en esta página.</div>',
    unsafe_allow_html=True,
)

# Auto-refresh SOLO para esta página (no bloquea navegación; al salir de la página deja de existir)
# Esto fuerza un reload de la página actual. Es el método más eficiente y seguro sin loops bloqueantes.
st.markdown(
    f"""
    <script>
      (function() {{
        const key = "fm_semaforo_autorefresh";
        const last = window.sessionStorage.getItem(key);
        // Evita múltiples timers si Streamlit re-renderiza
        if (!window.__fmTimer) {{
          window.__fmTimer = setInterval(function() {{
            // Solo refresca si el documento está visible (ahorra CPU si está en otra pestaña)
            if (document.visibilityState === "visible") {{
              window.location.reload();
            }}
          }}, {REFRESH_SECONDS * 1000});
        }}
      }})();
    </script>
    """,
    unsafe_allow_html=True,
)

# Contenedor principal (se repinta en cada refresh)
placeholder = st.empty()

with placeholder.container():
    try:
        m = fetch_metrics()
        # ---- Datos claves (sin mostrar FPS) ----
        att = _to_float(_get(m, "estimacion_atencion", "nivel_atencion", default=0.0), 0.0)
        att = max(0.0, min(att, 100.0))  # clamp 0..100

        estado_txt, estado_color = semaforo_color(att)

        estudiantes = _get(m, "estudiantes_detectados", "total_estudiantes", default="—")
        aula = _get(m, "aula", default="—")
        docente = _get(m, "docente", default="—")
        materia = _get(m, "materia", default="—")
        carrera = _get(m, "carrera", default="—")
        hora_inicio = _fmt_dt(_get(m, "hora_inicio", default=None))
        hora_fin = _fmt_dt(_get(m, "hora_fin", default=None))
        last_update = _fmt_dt(_get(m, "last_update", "timestamp", default=None))

        # ---- Semáforo ----
        st.markdown(
            f"""
            <div class="fm-grid">
              <div class="fm-semaforo fm-wide">
                <div class="left">
                  <div class="label">Estado Semáforo</div>
                  <div class="state" style="color:{estado_color};">{estado_txt}</div>
                  <div class="s">Última actualización: {last_update}</div>
                </div>
                <div class="fm-pill" style="background:{estado_color}; color: white;">
                  Nivel de atención: {att:.1f}%
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Cards informativas (sin FPS) ----
        st.markdown(
            f"""
            <div class="fm-grid">
              <div class="fm-card">
                <h4>Nivel de atención (estimación)</h4>
                <div class="v">{att:.1f}%</div>
                <div class="s">Rango: 0% - 100%</div>
              </div>

              <div class="fm-card">
                <h4>Estudiantes detectados</h4>
                <div class="v">{estudiantes}</div>
                <div class="s">Detectados por el modelo</div>
              </div>

              <div class="fm-card">
                <h4>Aula</h4>
                <div class="v">{aula}</div>
                <div class="s">Contexto del monitoreo</div>
              </div>

              <div class="fm-card">
                <h4>Docente</h4>
                <div class="v">{docente}</div>
                <div class="s">Responsable de clase</div>
              </div>

              <div class="fm-card">
                <h4>Materia</h4>
                <div class="v">{materia}</div>
                <div class="s">Asignatura</div>
              </div>

              <div class="fm-card">
                <h4>Carrera</h4>
                <div class="v">{carrera}</div>
                <div class="s">Programa académico</div>
              </div>

              <div class="fm-card">
                <h4>Hora inicio</h4>
                <div class="v">{hora_inicio}</div>
                <div class="s">Ventana de sesión</div>
              </div>

              <div class="fm-card">
                <h4>Hora fin</h4>
                <div class="v">{hora_fin}</div>
                <div class="s">Ventana de sesión</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Botón hacia streaming (debajo de cards) ----
        st.markdown("<br/>", unsafe_allow_html=True)
        STREAM_URL = "http://localhost:5500/"  # ajusta si tu frontend está en otro puerto
        st.link_button("📺 Abrir transmisión (Streaming)", STREAM_URL, use_container_width=True)

    except Exception as e:
        st.markdown(
            f"""
            <div class="fm-error">
              No se pudo obtener /metrics desde <b>{METRICS_URL}</b>.<br/>
              Verifica que el servicio esté arriba en el puerto 8000.<br/>
              <small>Detalle: {type(e)._name_}: {e}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br/>", unsafe_allow_html=True)
        STREAM_URL = "http://localhost:5500/"
        st.link_button("📺 Abrir transmisión (Streaming)", STREAM_URL, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)