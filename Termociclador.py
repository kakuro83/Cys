import streamlit as st
import pandas as pd

# --- FUNCIONES ---

def cargar_csv_desde_github(url):
    try:
        df = pd.read_csv(url)
        df['Código'] = df['Código'].str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"No se pudo leer el archivo CSV: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---

st.title("Termociclador Virtual – Paso 1: Cargar muestra")

url = st.text_input("Ingresa el enlace RAW del archivo CSV en GitHub:", 
                    value="https://raw.githubusercontent.com/tu_usuario/tu_repo/main/secuencias.csv")

codigo = st.text_input("Código de muestra (ej. P001):").strip().upper()

if st.button("Cargar muestra"):
    df = cargar_csv_desde_github(url)
    if not df.empty and codigo in df['Código'].values:
        secuencia_real = df[df['Código'] == codigo]['Secuencia'].values[0]
        st.success(f"Secuencia cargada para {codigo}")
        st.code(secuencia_real)
    else:
        st.warning("Código no encontrado.")
