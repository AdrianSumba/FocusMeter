import streamlit as st

st.set_page_config(page_title="Focus Meter Web",)

pg = st.navigation([
    st.Page("vista/home.py", title="🏠 Home"),
    st.Page("vista/semaforo.py", title="🚦 Semáforo"),
    st.Page("vista/estadisticas.py", title="📊 Estadísticas"),
    st.Page("vista/docs.py", title="📖 Documentación"),
])

pg.run()