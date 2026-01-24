import streamlit as st
from PIL import Image
import base64
from io import BytesIO

with st.spinner("Cargando inicio..."):

    logo = Image.open("extras/logo_tec.png")

    buffer = BytesIO()

    logo.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()

    st.markdown(
        f"""
        <div style="width:100%; display:flex; justify-content:center; margin-top:10px; margin-bottom:10px;">
            <img src="data:image/png;base64,{b64}" style="width:450px; max-width:100%; height:auto;" />
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='text-align:center;'>🎓 Focus Meter: Sistema de Monitoreo del Nivel de Atención Estudiantil</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; font-size:17px; line-height:1.7; margin-top:10px;">
            Este proyecto desarrolla un sistema inteligente basado en <strong>inteligencia artificial</strong> para monitorear en tiempo real el nivel de atención
            de los estudiantes durante las clases, utilizando una cámara rtsp para analizar
            gestos faciales y patrones de concentración.<br><br>
            La solución ofrece a los docentes una <strong>herramienta visual e intuitiva</strong>,
            representada mediante un <strong>semáforo de atención</strong>, que permite identificar
            estados de alta, media y baja atención con el fin de optimizar el
            proceso de enseñanza–aprendizaje.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<h3 style='text-align:center; margin-top:18px;'>👨‍💻 Integrantes del Proyecto</h3>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div style="text-align:center; font-size:16px; line-height:1.8;">
            Freddy Orlando Montalván Quito<br>
            Jimmy Adrián Sumba Juela<br>
            Christian Eduardo Mendieta Tenesaca
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<h3 style='text-align:center; margin-top:18px;'>👩‍🏫 Tutor del Proyecto</h3>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; font-size:16px; line-height:1.8;">
            Ing. Lorena Calle, Mgtr.
        </div>
        """,
        unsafe_allow_html=True
    )