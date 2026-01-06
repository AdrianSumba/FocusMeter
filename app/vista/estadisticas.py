import streamlit as st
import streamlit.components.v1 as components

st.title("📊 Estadísticas")

embed_url = "https://app.fabric.microsoft.com/view?r=eyJrIjoiMDFjODcxNTgtMzZiZC00YzdiLWJhNDgtOWI0MzdmM2JlMGYxIiwidCI6IjU5MzM1ZjViLWQ5MTUtNDBjNC1iOTM0LTcyOWZlYmU5Mjc3YSIsImMiOjEwfQ%3D%3D"

components.html(
    f"""
    <iframe 
        title="Call Center Performance Report" 
        width="100%" 
        height="600" 
        src="{embed_url}" 
        frameborder="0" 
        allowFullScreen="true">
    </iframe>
    """,
    height=600,
)