import streamlit as st
from PIL import Image

logo = Image.open("extras/logo_tec.png")

col1, col2, col3 = st.columns([1, 2, 1])  
with col2:
    st.image(logo, width=450)

st.markdown(
    "<h1 style='text-align: center;'>🎓 Focus Meter: Sistema de Monitoreo del Nivel de Atención Estudiantil</h1>",
    unsafe_allow_html=True
)


st.markdown(
    """
    <p style='text-align: justify; font-size:17px;'>
    Este proyecto desarrolla un sistema inteligente basado en <strong>inteligencia artificial</strong> para monitorear en tiempo real el nivel de atención
    de los estudiantes durante las clases, utilizando una cámara web para analizar gestos
    faciales y patrones de concentración.  
    La solución ofrece a los docentes una <strong>herramienta visual e intuitiva</strong>,
    representada mediante un <strong>semáforo de atención</strong>, que permite identificar
    estados de alta, media y baja atención con el fin de optimizar el proceso de enseñanza–aprendizaje.
    </p>
    """,
    unsafe_allow_html=True
)


st.subheader("👨‍💻 Integrantes del Proyecto")
st.markdown(""" 
    - Freddy Orlando Montalván Quito  
    - Jimmy Adrián Sumba Juela  
    - Christian Eduardo Mendieta Tenesaca 
""")

st.subheader("👩‍🏫 Tutor del Proyecto")
st.write("Ing. Lorena Calle, Mgtr.")