import streamlit as st
import pandas as pd
import random

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

# --- MASAS MOLARES ESTÁNDAR DE LOS 20 AMINOÁCIDOS ---
masas_aminoacidos = {
    'A': 89.09,  'R': 174.20, 'N': 132.12, 'D': 133.10, 'C': 121.16,
    'E': 147.13, 'Q': 146.15, 'G': 75.07,  'H': 155.16, 'I': 131.17,
    'L': 131.17, 'K': 146.19, 'M': 149.21, 'F': 165.19, 'P': 115.13,
    'S': 105.09, 'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
}

# --- PROCESAMIENTO SI EL CÓDIGO ES VÁLIDO ---
if codigo_ingresado and codigo_ingresado in df['Código'].values:
    fila = df[df['Código'] == codigo_ingresado].iloc[0]
    secuencia_real = fila['Secuencia'].strip()
    ciclico = str(fila['Cíclico']).strip().lower() in ['sí', 'si', 'true', '1']
    secuencia = secuencia_real.replace("(c)", "").strip().upper()

    secuencia_valida = all(aa in masas_aminoacidos for aa in secuencia)

    if not secuencia_valida:
        st.error("La secuencia contiene aminoácidos inválidos.")
    else:
        from collections import Counter
        conteo = Counter(secuencia)
        n_residuos = sum(conteo.values())

        peso_sin_agua = sum(masas_aminoacidos[aa] * n for aa, n in conteo.items())
        correccion = 18.015 * (n_residuos - 1)
        peso_total = peso_sin_agua - correccion

        proporciones = {aa: (masas_aminoacidos[aa] * n / peso_total * 100) for aa, n in conteo.items()}
        proporciones_ordenadas = dict(sorted(proporciones.items(), key=lambda x: x[0]))

        st.markdown("### Caracterización de la muestra purificada")
        st.markdown(f"**Peso molecular total estimado del péptido:** `{peso_total:.2f} Da`")

        df_prop = pd.DataFrame({
            'Aminoácido': list(proporciones_ordenadas.keys()),
            'Masa molar (Da)': [masas_aminoacidos[aa] for aa in proporciones_ordenadas.keys()],
            '% másico': [round(v, 2) for v in proporciones_ordenadas.values()]
        })

        st.markdown("**Proporciones másicas y masas molares:**")
        st.dataframe(df_prop.set_index('Aminoácido'))

        st.markdown("### Verificación del número de residuos")
        st.markdown("Con base en el peso molecular total y las proporciones másicas, indica cuántos aminoácidos contiene el péptido:")

        numero_real = sum(conteo.values())
        respuesta_estudiante = st.number_input("Número de aminoácidos", min_value=1, step=1, format="%d")
        continuar = False

        if respuesta_estudiante:
            if int(respuesta_estudiante) == numero_real:
                st.success("¡Correcto! Puedes continuar con el análisis.")
                continuar = True
            else:
                st.error("❌ Revisa bien tus cálculos. Identifica si estás utilizando los pesos moleculares correctamente. ¡Y no te olvides de los enlaces peptídicos!")

        if continuar:
            # --- BLOQUE DE REINICIO AUTOMÁTICO SI CAMBIA EL CÓDIGO ---
            codigo_actual = codigo_ingresado

            if "codigo_anterior" not in st.session_state:
                st.session_state.codigo_anterior = codigo_actual

            if st.session_state.codigo_anterior != codigo_actual:
                st.session_state.codigo_anterior = codigo_actual
                for key in ["fragmentos_disponibles", "resumen_rondas", "numero_ronda"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

            from termociclador_bloques import termociclador_virtual
            termociclador_virtual(secuencia, ciclico)

            # --- BOTÓN PARA REINICIAR MANUALMENTE ---
            if st.button("🔁 Reiniciar termociclador"):
                for key in ["fragmentos_disponibles", "resumen_rondas", "numero_ronda"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Termociclador reiniciado. Puedes comenzar de nuevo.")
                st.rerun()
