import streamlit as st
import groq
import os
import uuid
from PyPDF2 import PdfReader
from docx import Document

MODELOS = ["llama3-8b-8192", "llama3-70b-8192"]

# ---------------- CONFIGURACIÓN ----------------
def configurar_pagina():
    st.set_page_config(page_title="Mi Chatbot", page_icon="🐐", layout="wide")
    st.title("🤖 Chatbot Multimodal")

# ---------------- SIDEBAR ----------------
def mostrar_sidebar():
    st.sidebar.header("🗂 Historial de Chats")

    if "chats" not in st.session_state:
        st.session_state.chats = {"Nuevo Chat": []}
        st.session_state.chat_actual = "Nuevo Chat"

    chat_names = list(st.session_state.chats.keys())
    chat_seleccionado = st.sidebar.selectbox("Seleccioná un chat", chat_names, key="chat_selector")

    if st.sidebar.button("➕ Nuevo chat"):
        nuevo_nombre = f"Chat-{str(uuid.uuid4())[:4]}"
        st.session_state.chats[nuevo_nombre] = []
        st.session_state.chat_actual = nuevo_nombre
        st.rerun()

    if st.sidebar.button("🖑 Borrar chat actual"):
        if st.session_state.chat_actual != "Nuevo Chat":
            del st.session_state.chats[st.session_state.chat_actual]
            st.session_state.chat_actual = "Nuevo Chat"
            st.rerun()

    nuevo_nombre = st.sidebar.text_input("✏️ Renombrar chat actual", key="nuevo_nombre")
    if nuevo_nombre and nuevo_nombre not in st.session_state.chats:
        if st.sidebar.button("Guardar nuevo nombre"):
            st.session_state.chats[nuevo_nombre] = st.session_state.chats.pop(st.session_state.chat_actual)
            st.session_state.chat_actual = nuevo_nombre
            st.rerun()

    st.session_state.chat_actual = chat_seleccionado

    st.sidebar.markdown("---")
    st.sidebar.header("🧠 Selección de Modelo")
    modelo_seleccionado = st.sidebar.selectbox("Elegí tu modelo", MODELOS)

    return modelo_seleccionado

# ---------------- CLIENTE GROQ ----------------
def crear_cliente_groq():
    groq_api_key = st.secrets["GROQ_API_KEY"]
    return groq.Groq(api_key=groq_api_key)

# ---------------- ARCHIVOS ----------------
def leer_archivo(subido):
    if subido.type == "application/pdf":
        reader = PdfReader(subido)
        texto = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif subido.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(subido)
        texto = "\n".join([p.text for p in doc.paragraphs])
    elif subido.type.startswith("text/"):
        texto = subido.read().decode("utf-8")
    else:
        texto = "⚠️ Tipo de archivo no soportado."
    return texto

def cargar_archivos():
    archivos = st.file_uploader("📂 Subí archivos (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    if archivos:
        for archivo in archivos:
            contenido = leer_archivo(archivo)
            if contenido:
                agregar_mensaje("system", f"📄 Contenido del archivo '{archivo.name}':\n\n{contenido}")

# ---------------- MENSAJES ----------------
def obtener_mensajes_previos():
    for mensaje in st.session_state.chats[st.session_state.chat_actual]:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

def obtener_mensaje_usuario():
    return st.chat_input("Escribí tu mensaje")

def agregar_mensaje(role, content):
    st.session_state.chats[st.session_state.chat_actual].append({"role": role, "content": content})

def mostrar_mensaje(role, content):
    with st.chat_message(role):
        st.markdown(content)

# ---------------- FLUJO PRINCIPAL ----------------
def ejecutar_chat():
    configurar_pagina()
    cliente = crear_cliente_groq()
    modelo = mostrar_sidebar()

    obtener_mensajes_previos()
    cargar_archivos()

    mensaje_usuario = obtener_mensaje_usuario()
    if mensaje_usuario:
        agregar_mensaje("user", mensaje_usuario)
        mostrar_mensaje("user", mensaje_usuario)

        respuesta = cliente.chat.completions.create(
            model=modelo,
            messages=st.session_state.chats[st.session_state.chat_actual]
        )

        contenido_asistente = respuesta.choices[0].message.content
        agregar_mensaje("assistant", contenido_asistente)
        mostrar_mensaje("assistant", contenido_asistente)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    ejecutar_chat()
