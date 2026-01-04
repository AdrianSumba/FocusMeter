import streamlit as st

st.set_page_config(page_title="Focus Meter Web",)

pg = st.navigation([
    st.Page("paginas/home.py", title="🏠 Home"),
    st.Page("paginas/semaforo.py", title="🚦 Semáforo"),
    st.Page("paginas/estadisticas.py", title="📊 Estadísticas"),
    st.Page("paginas/docs.py", title="📖 Documentación"),
])

pg.run()