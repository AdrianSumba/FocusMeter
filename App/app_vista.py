import streamlit as st

st.set_page_config(
    page_title="Sistema de Atención Estudiantil",
    layout="wide"
)

pg = st.navigation([
    st.Page("vista/pages/home.py", title="🏠 Home"),
    st.Page("vista/pages/monitoreo.py", title="📹 Monitoreo"),
    st.Page("vista/pages/analisis.py", title="📊 Análisis"),
    st.Page("vista/pages/tendencias.py", title="📈 Tendencias"),
    st.Page("vista/pages/proyecciones.py", title="🔮 Proyecciones"),
    st.Page("vista/pages/metodologia.py", title="📚 Metodología"),
])

pg.run()


