import streamlit as st
import pandas as pd

# --- FUNCIÓN PARA CARGAR HOJA "Cys" DESDE GOOGLE SHEETS ---
@st.cache_data
def cargar_hoja_cys():
    url = "https://docs.google.com/spreadsheets/d/1X7dF-WjNNYzA3_FimcZ9IjDycQo8_t3oX9J_ekxqtl4/gviz/tq?tqx=out:csv&sheet=Cys"
    df = pd.read_csv(url)
    df['Código'] = df['Código'].str.strip().str.upper()
    return df

# --- INTERFAZ DE USUARIO ---
st.title("Termociclador Virtual – Carga de muestra")

df = cargar_hoja_cys()

codigo_ingresado = st.text_input("Ingresa el código de la muestra (ej. P001):").strip().upper()

if codigo_ingresado:
    if codigo_ingresado in df['Código'].values:
        fila = df[df['Código'] == codigo_ingresado].iloc[0]
        secuencia_real = fila['Secuencia'].strip()
        ciclico = str(fila['Cíclico']).strip().lower() in ['sí', 'si', 'true', '1']
        st.success(f"Muestra {codigo_ingresado} cargada correctamente.")
        st.markdown(f"Esta muestra es **{'cíclica' if ciclico else 'lineal'}**.")
    else:
        st.error("Código no encontrado en la base de datos.")

#st.write("Columnas detectadas:", df.columns.tolist())

# --- MASAS MOLARES ESTÁNDAR DE LOS 20 AMINOÁCIDOS ---
masas_aminoacidos = {
    'A': 89.09,  'R': 174.20, 'N': 132.12, 'D': 133.10, 'C': 121.16,
    'E': 147.13, 'Q': 146.15, 'G': 75.07,  'H': 155.16, 'I': 131.17,
    'L': 131.17, 'K': 146.19, 'M': 149.21, 'F': 165.19, 'P': 115.13,
    'S': 105.09, 'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
}

# --- PROCESAMIENTO SI EL CÓDIGO ES VÁLIDO ---
if codigo_ingresado in df['Código'].values:
    # Limpiar etiqueta cíclica si la tiene
    secuencia = secuencia_real.replace("(c)", "").strip().upper()

    # Verificar caracteres válidos
    secuencia_valida = all(aa in masas_aminoacidos for aa in secuencia)
    if not secuencia_valida:
        st.error("La secuencia contiene aminoácidos inválidos.")
    else:
        # Calcular frecuencia de cada aminoácido
        from collections import Counter
        conteo = Counter(secuencia)

        # Calcular peso molecular total
        peso_total = sum(masas_aminoacidos[aa] * n for aa, n in conteo.items())

        # Calcular proporción másica (%)
        proporciones = {aa: (masas_aminoacidos[aa] * n / peso_total * 100) for aa, n in conteo.items()}
        proporciones_ordenadas = dict(sorted(proporciones.items(), key=lambda x: x[0]))

        st.markdown("### Análisis de la muestra")
        st.write(f"**Peso molecular estimado:** {peso_total:.2f} Da")

        st.markdown("**Proporción másica por aminoácido (%):**")
        st.dataframe(pd.DataFrame({
            'Aminoácido': list(proporciones_ordenadas.keys()),
            '% másico': [f"{v:.2f}" for v in proporciones_ordenadas.values()]
        }))
