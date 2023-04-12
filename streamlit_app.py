import streamlit as st
import openai
import PyPDF2
import io
import base64
from streamlit_option_menu import option_menu
import shutil
from pathlib import Path
import os

# Establecer la clave de API de GPT-4 desde la variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

def extraer_texto_de_pdf(ruta_archivo_pdf):
    pdf_file = io.BytesIO(ruta_archivo_pdf.read())
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    texto = ""

    for page in range(len(pdf_reader.pages)):
        texto_pagina = pdf_reader.pages[page].extract_text()
        texto += texto_pagina + " "
        lineas = texto.split("\n")

    indice = 0
    for i, linea in enumerate(lineas):
        if "Referencias" in linea:
            indice = i
            break

    lineas = lineas[:indice + 1]

    texto = "\n".join(lineas)

    return texto

def crear_texto(contenido_texto):

    if len(contenido_texto) > 7000 * 4:
        text1 = contenido_texto[:15000]
        text2 = contenido_texto[-15000:]
        texto_documento = text1 + text2
    else:
        texto_documento = contenido_texto

    prompt = [
        {"role": "system",
         "content": "Estás recopilando información de un artículo de investigación académica para un estudiante universitario. Incluye una respuesta de 2 oraciones para cada uno de los siguientes encabezados: Resumen, Hallazgos, Brechas en la investigación, Importancia, Metodología"},
        {"role": "user", "content": texto_documento}
    ]

    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=prompt,
        max_tokens=500,
        temperature=.5)
    respuestas_de_gpt = response['choices'][0]['message']['content']
    st.write(respuestas_de_gpt)

    return respuestas_de_gpt

def charla_con_documentos(entrada_pregunta, texto_documento):

    if len(texto_documento) > 7000 * 4:
        text1 = texto_documento[:13000]
        text2 = texto_documento[-13000:]
        texto_documento = text1 + text2

    prompt = [
        {"role": "system", "content": "Eres un chatbot que responde preguntas sobre un artículo de investigación"},
        {"role": "user",
         "content": f"Mi pregunta es: {entrada_pregunta}" + f" Por favor, utiliza el siguiente artículo de investigación para ayudar a responder la pregunta{texto_documento}"}
    ]

    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=prompt,
        max_tokens=800,
        temperature=.5)

    st.write(f"### {entrada_pregunta}")

    return response['choices'][0]['message']['content']

def main():
    st.set_page_config(page_title="AI Research Pal", page_icon=":newspaper:", layout="wide")

    with st.sidebar:
        choose = option_menu("App Gallery",
                             ["Subir artículo", "Charlar con el artículo", "Resumir artículo"],
                             icons=['house', 'person lines fill', 'book'],
                             menu_icon="app-indicator", default_index=0,
                             styles={
                                 "container": {"padding": "5!important", "background-color": "#fafafa"},
                                 "                                 "icon": {"color": "orange", "font-size": "25px"},
                                 "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                              "--hover-color": "#eee"},
                                 "nav-link-selected": {"background-color": "#02ab21"},
                             }
                             )
    if choose == "Subir artículo":
        archivo_subido = st.file_uploader("Selecciona un archivo PDF", type=["pdf"])
        if archivo_subido:
            st.session_state.pdf_data = archivo_subido.read()
    elif choose == "Resumir artículo":
        st.title('Resumen del artículo')
        if 'pdf_data' in st.session_state:
            texto_documento = extraer_texto_de_pdf(io.BytesIO(st.session_state.pdf_data))
            resumen_articulo = crear_texto(texto_documento)
        else:
            st.write("Por favor, sube un artículo para comenzar")
    elif choose == 'Charlar con el artículo':
        if 'pdf_data' in st.session_state:
            texto_documento = extraer_texto_de_pdf(io.BytesIO(st.session_state.pdf_data))
            col1, col2 = st.columns((3, 1))
            with col1:
                st.subheader("Visor de PDF")
                pdf_base64 = base64.b64encode(st.session_state.pdf_data).decode('utf-8')
                mostrar_pdf = f'<iframe src="data:application/pdf;base64,' \
                              f'{pdf_base64}" width="900" height="800" type="application/pdf"></iframe>'
                st.markdown(mostrar_pdf, unsafe_allow_html=True)

            with col2:
                st.subheader("Charla")
                historial_chat = st.empty()
                lista_chat = []

                entrada_usuario = st.text_input("Escribe tu mensaje y presiona Enter")

                if entrada_usuario:
                    lista_chat.append({"user": entrada_usuario})
                    respuesta = charla_con_documentos(entrada_usuario, texto_documento)

                    lista_chat.append({"bot": respuesta})

                    historial_chat.markdown("#### Historial de chat")
                    for chat in lista_chat:
                        if "user" in chat:
                            historial_chat.markdown(f"**Tú:** {chat['user']}")
                        elif "bot" in chat:
                            historial_chat.markdown(f"**Bot:** {chat['bot']}")
        else:
            st.write('Por favor, sube un archivo para comenzar')


if __name__ == "__main__":
    main()
