import streamlit as st
import streamlit.components.v1 as components

st.title("🚦 Semáforo")

with st.spinner("Cargando Semáforo..."):
    components.html(
    """
    <iframe
        src="http://localhost:5500"
        style="width:100%; height:92vh; border:none;">
    </iframe>
    """,
    height=550
    )
