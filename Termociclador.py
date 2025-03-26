import streamlit as st
import pandas as pd

# --- FUNCIONES ---

def cargar_secuencias_desde_google(url):
    try:
        df = pd.read_csv(url)
        df['Código'] = df['Código'].str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"No se pudo leer la hoja de Google Sheets: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---

st.title("Termociclador Virtual – Paso 1: Cargar muestra")

url_default = "https://docs.google.com/spreadsheets/d/1X7dF-WjNNYzA3_FimcZ9IjDycQo8_t3oX9J_ekxqtl4/gviz/tq?tqx=out:csv&sheet=Cys"
url = st.text_input("URL de la hoja pública con las secuencias (hoja Cys):", value=url_default)

codigo = st.text_input("Código de muestra (ej. P001):").strip().upper()

if st.button("Cargar muestra"):
    df = cargar_secuencias_desde_google(url)
    if not df.empty and codigo in df['Código'].values:
        fila = df[df['Código'] == codigo].iloc[0]
        secuencia_real = fila['Secuencia']
        ciclico = fila['Cíclico']
        st.success(f"Secuencia cargada para {codigo}")
        st.code(f"(Oculta) {'(c)' if ciclico == 'Sí' else ''}{secuencia_real}")
        st.markdown(f"**¿Cíclico?** {ciclico}")
    else:
        st.warning("Código no encontrado en la hoja.")
