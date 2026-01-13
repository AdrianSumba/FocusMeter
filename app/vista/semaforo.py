import streamlit as st
import streamlit.components.v1 as components


FRONTEND_URL = "http://localhost:5500/"


components.html(
    f"""
    <script>
      window.open('{FRONTEND_URL}', '_blank');
    </script>
    <div style="font-family: sans-serif; padding: 10px;">
      <b>Abriendo transmisión...</b><br/>
      Si tu navegador bloqueó el popup, abre manualmente: <a href="{FRONTEND_URL}" target="_blank">{FRONTEND_URL}</a>
    </div>
    """,
    height=90,
)

st.stop()
