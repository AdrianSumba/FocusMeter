import streamlit as st

st.title("🚦 Semáforo")

FRONTEND_URL = "http://localhost:5500/"

st.markdown(
    f"""
    <a href="{FRONTEND_URL}" target="_blank">
        <button style="
            padding: 12px 20px;
            font-size: 16px;
            background-color: #1f77b4;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        ">
            📺 Abrir transmisión en tiempo real
        </button>
    </a>
    """,
    unsafe_allow_html=True,
)
