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

from PIL import Image

# Carga del ícono
icono = Image.open("termociclador_icono.png")
col1, col2 = st.columns([1, 9])

# --- INTERFAZ DE USUARIO ---
with col1:
    st.image(icono, width=150)
with col2:
    st.markdown("<h1 style='padding-top: 10px;'>Termociclador Virtual</h1>", unsafe_allow_html=True)

df = cargar_hoja_cys()

st.markdown("### 🤓 Ingresa el código de la muestra (ej. `P001`):")
codigo_ingresado = st.text_input("", key="codigo_input").strip().upper()

if codigo_ingresado:
    if codigo_ingresado in df['Código'].values:
        fila = df[df['Código'] == codigo_ingresado].iloc[0]
        secuencia_real = fila['Secuencia'].strip()
        ciclico = str(fila['Cíclico']).strip().lower() in ['sí', 'si', 'true', '1']
        #st.success(f"Muestra {codigo_ingresado} cargada correctamente.")
        #st.markdown(f"Esta muestra es **{'cíclica' if ciclico else 'lineal'}**.")
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
              
        st.markdown("**Pesos moleculares y proporciones másicas:**")
        
        # Crear una copia para formatear las columnas
        tabla = df_prop.copy()
        tabla["Masa molar (Da)"] = tabla["Masa molar (Da)"].map("{:.2f}".format)
        tabla["% másico"] = tabla["% másico"].map("{:.2f}".format)
        
        # Generar tabla HTML
        html = tabla.to_html(index=False, classes='styled-table', justify='center', escape=False)
        
        # Inyectar estilo CSS
        st.markdown(
            """
            <style>
            .styled-table {
                border-collapse: collapse;
                margin: auto;
                font-size: 16px;
                width: auto;
                min-width: 480px;
            }
            .styled-table th, .styled-table td {
                border: 1px solid #ccc;
                padding: 8px;
                text-align: center;
            }
            .styled-table th {
                background-color: #f0f0f0;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Mostrar la tabla
        st.markdown(html, unsafe_allow_html=True)

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

            # --- SIMULACIÓN DEL MÉTODO DE SANGER ---
            st.markdown("### 🧪 Método de Sanger – Identificación del N-terminal")
            
            if ciclico:
                st.info("🔄 No se detecta N-terminal con el método de Sanger.")
            else:
                aa_n_terminal = secuencia[0]
                st.success(f"🧬 N-terminal identificado: **{aa_n_terminal}**")

            # --- INICIO DEL TERMO CICLADOR DIRECTAMENTE ---
            if "fragmentos_disponibles" not in st.session_state:
                st.session_state.fragmentos_disponibles = {"R0 - Secuencia original": secuencia}
            if "resumen_rondas" not in st.session_state:
                st.session_state.resumen_rondas = []
            if "numero_ronda" not in st.session_state:
                st.session_state.numero_ronda = 1

            cortadores = {
                "Tripsina": {"modo": "después", "residuos": ["K", "R"]},
                "Quimotripsina": {"modo": "después", "residuos": ["F", "Y", "W"]},
                "CNBr": {"modo": "después", "residuos": ["M"]},
                "Pepsina": {"modo": "antes", "residuos": ["F", "Y", "W"]},
                "V8 proteasa": {"modo": "después", "residuos": ["D", "E"]},
                "Asp-N-proteasa": {"modo": "antes", "residuos": ["D", "E"]},
                "Bromelina": {"modo": "antes", "residuos": ["F", "Y", "L", "A", "V"]},
                "Digestión con HCl 6M": {"modo": "aleatorio", "residuos": []}
            }

            def cortar_peptido(secuencia, residuos, modo):
                fragmentos = []
                actual = ""
                for aa in secuencia:
                    if modo == "después":
                        actual += aa
                        if aa in residuos:
                            fragmentos.append(actual)
                            actual = ""
                    elif modo in ["antes", "before"]:
                        if aa in residuos:
                            if actual:
                                fragmentos.append(actual)
                            actual = aa
                        else:
                            actual += aa
                if actual:
                    fragmentos.append(actual)
                return fragmentos

            def digestion_aleatoria_controlada(secuencia):
                longitud = len(secuencia)
                if longitud <= 1:
                    return [secuencia]
                n_fragmentos = 5
                if longitud > 10:
                    n_fragmentos += (longitud - 10) // 3
                n_fragmentos = min(n_fragmentos, longitud)
                if n_fragmentos == 1:
                    return [secuencia]
                indices = sorted(random.sample(range(1, longitud), n_fragmentos - 1))
                indices = [0] + indices + [longitud]
                fragmentos = [secuencia[indices[i]:indices[i+1]] for i in range(len(indices) - 1)]
                return fragmentos

            st.markdown("## 🧪 ¡Hora del Secuenciamiento!")

            fragmento_seleccionado_label = st.selectbox(
                "Selecciona la secuencia o fragmento que deseas cortar:",
                list(st.session_state.fragmentos_disponibles.keys())
            )
            fragmento_seleccionado = st.session_state.fragmentos_disponibles[fragmento_seleccionado_label]

            cortador = st.selectbox("Selecciona el cortador:", list(cortadores.keys()))
            modo = cortadores[cortador]["modo"]
            residuos = cortadores[cortador]["residuos"]

            if modo == "aleatorio":
                st.info("**Digestión con HCl 6M**: corte aleatorio no específico, genera fragmentos que incluyen todos los aminoácidos presentes, con posibles repeticiones.")
                fragmentos_generados = digestion_aleatoria_controlada(fragmento_seleccionado)
            else:
                # Validación si contiene residuos objetivo
                contiene_residuo = any(res in fragmento_seleccionado for res in residuos)
                
                if not contiene_residuo:
                    st.warning("⚠️ Este cortador no sirve para la secuenciación: no se encontraron los residuos diana en la secuencia.")
                    fragmentos_generados = []  # Evita mostrar fragmentos innecesarios
                else:
                    st.info(f"**{cortador}** corta **{modo}** los residuos: {', '.join(residuos)}")
                    fragmentos_generados = cortar_peptido(fragmento_seleccionado, residuos, modo)

            if fragmentos_generados:
                st.markdown("**Fragmentos generados:**")
                for i, frag in enumerate(fragmentos_generados, 1):
                    st.markdown(f"- Fragmento {i}: `{frag}`")
    
            if st.button("💾 Guardar corte"):
                st.session_state.resumen_rondas.append({
                    "Ronda": st.session_state.numero_ronda,
                    "Cortador": cortador,
                    "Cortado desde": fragmento_seleccionado_label,
                    "Fragmentos": fragmentos_generados
                })
            
                for i, frag in enumerate(fragmentos_generados, 1):
                    nueva_etiqueta = f"R{st.session_state.numero_ronda} - Fragmento {i}"
                    st.session_state.fragmentos_disponibles[nueva_etiqueta] = frag
            
                if st.session_state.numero_ronda < 10:
                    st.session_state.numero_ronda += 1
                else:
                    st.warning("⚠️ Se alcanzó el máximo de 10 rondas. Reinicie el Termociclador.")

            if st.session_state.resumen_rondas:
                st.markdown("---")
                st.markdown("## 📋 Resumen de cortes realizados")
                for ronda in st.session_state.resumen_rondas:
                    st.markdown(f"### 🔄 Ronda {ronda['Ronda']}")
                    st.markdown(f"- **Cortador aplicado:** {ronda['Cortador']}")
                    st.markdown(f"- **Fragmento cortado:** `{ronda['Cortado desde']}`")
                    st.markdown("**Fragmentos generados:**")
                    for i, frag in enumerate(ronda["Fragmentos"], 1):
                        st.markdown(f"  - Fragmento {i}: `{frag}`")

            if st.button("🔁 Reiniciar termociclador"):
                for key in ["fragmentos_disponibles", "resumen_rondas", "numero_ronda"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Termociclador reiniciado. Puedes comenzar de nuevo.")
                st.rerun()

    st.markdown("---")
    st.markdown("## ✅ Validación de tu secuencia propuesta")

    # Campo de entrada editable
    entrada_cruda = st.text_input(
        "Escribe tu secuencia (se convertirá automáticamente a mayúsculas):"
    )

    # Estandarización automática
    if entrada_cruda.lower().startswith("(c)"):
        propuesta_estandar = "(c)" + entrada_cruda[3:].upper()
    else:
        propuesta_estandar = entrada_cruda.upper()

    # Vista previa bonita como texto normal
    if entrada_cruda:
        st.markdown(f"**Vista previa estandarizada:** `{propuesta_estandar}`")

    # Validación al hacer clic
    if st.button("🔍 Validar secuencia"):
        secuencia_real_sin_c = secuencia_real.replace("(c)", "").upper()
        propuesta = propuesta_estandar

        if ciclico:
            if not propuesta.startswith("(C)"):
                st.error("❌ Revisa el orden de los residuos o inicia con (c) si es cíclica")
            else:
                propuesta_limpia = propuesta.replace("(C)", "")
                rotaciones_validas = [
                    secuencia_real_sin_c[i:] + secuencia_real_sin_c[:i]
                    for i in range(len(secuencia_real_sin_c))
                ]
                if propuesta_limpia in rotaciones_validas:
                    st.success("✅ ¡Secuencia correcta!")
                    if st.button("💾 Guardar resultado"):
                        st.success("✅ Resultado registrado correctamente.")
                else:
                    st.error("❌ La secuencia no es correcta. Revisa el orden o los residuos.")
        else:
            if propuesta == secuencia_real.upper():
                st.success("✅ ¡Secuencia correcta!")
                if st.button("💾 Guardar resultado"):
                    st.success("✅ Resultado registrado correctamente.")
            else:
                st.error("❌ La secuencia no es correcta.")



