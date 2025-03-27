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

#st.write("Columnas detectadas:", df.columns.tolist())

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

        # Peso sin corrección
        peso_sin_agua = sum(masas_aminoacidos[aa] * n for aa, n in conteo.items())
        correccion = 18.015 * (n_residuos - 1)
        peso_total = peso_sin_agua - correccion

        # Proporciones másicas
        proporciones = {aa: (masas_aminoacidos[aa] * n / peso_total * 100) for aa, n in conteo.items()}
        proporciones_ordenadas = dict(sorted(proporciones.items(), key=lambda x: x[0]))

        # Mostramos los datos al estudiante
        st.markdown("### Caracterización de la muestra purificada")
        st.markdown(f"**Peso molecular total estimado del péptido:** `{peso_total:.2f} Da`")

        df_prop = pd.DataFrame({
            'Aminoácido': list(proporciones_ordenadas.keys()),
            'Masa molar (Da)': [masas_aminoacidos[aa] for aa in proporciones_ordenadas.keys()],
            '% másico': [round(v, 2) for v in proporciones_ordenadas.values()]
        })

        st.markdown("**Proporciones másicas y masas molares:**")
        st.dataframe(df_prop.set_index('Aminoácido'))

        # --- VERIFICACIÓN DEL NÚMERO DE AMINOÁCIDOS ---
        st.markdown("### Verificación del número de residuos")
        st.markdown("Con base en el peso molecular total y las proporciones másicas, indica cuántos aminoácidos contiene el péptido:")
        
        numero_real = sum(conteo.values())
        respuesta_estudiante = st.number_input("Número de aminoácidos", min_value=1, step=1, format="%d")
        continuar = False  # Reinicio de estado
        
        if respuesta_estudiante:
            if int(respuesta_estudiante) == numero_real:
                st.success("¡Correcto! Puedes continuar con el análisis.")
                continuar = True
            else:
                st.error("❌ Revisa bien tus cálculos. Identifica si estás utilizando los pesos moleculares correctamente. ¡Y no te olvides de los enlaces peptídicos!")
                continuar = False
        
        # --- TODO LO DEMÁS VA AQUÍ DENTRO ---
        if continuar:
        
            # --- ANÁLISIS POR FDNB ---
            st.markdown("### Resultado del análisis por FDNB (método de Sanger)")
            if ciclico:
                st.info("No se detectó ningún aminoácido N-terminal, lo cual sugiere que el péptido podría ser **cíclico**.")
            else:
                residuo_fdnb = secuencia[0]
                st.success(f"El análisis por FDNB indica que el residuo **N-terminal** es: `{residuo_fdnb}`")

           # --- CÁLCULO DEL NÚMERO MÁXIMO DE RONDAS ---
            num_rondas = 3
            if numero_real > 10:
                num_rondas += (numero_real - 10) // 5
            
            st.session_state["num_rondas"] = num_rondas
            st.session_state["fragmentos_ronda_0"] = [secuencia]

            cortadores = {
                    "Tripsina": {"residuos": ["K", "R"], "modo": "después"},
                    "Quimotripsina": {"residuos": ["F", "Y", "W"], "modo": "después"},
                    "CNBr": {"residuos": ["M"], "modo": "después"},
                    "Pepsina": {"residuos": ["L", "F", "E"], "modo": "antes"},
                    "Bromelina": {"residuos": ["A", "G"], "modo": "antes"},
                    "Digestión con HCl 6M": {"residuos": [], "modo": "aleatorio"}
            }

            # --- FUNCIONES ---
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
            
            def ejecutar_ronda(ronda, fragmentos_entrada):
                st.markdown(f"### Ronda {ronda + 1}: Selección de corte")
            
                if ronda == 0:
                    secuencia_actual = fragmentos_entrada[0]
                    seleccion = "Secuencia original"
                    st.info("Usando la secuencia original para el primer corte.")
                else:
                    # Incluir secuencia original + fragmentos anteriores
                    opciones = {"Secuencia original": st.session_state["fragmentos_ronda_0"][0]}
                    opciones.update({f"Fragmento {i+1}": f for i, f in enumerate(fragmentos_entrada)})
                    
                    seleccion = st.selectbox(
                        f"Selecciona fragmento o secuencia original para cortar (Ronda {ronda + 1}):",
                        opciones.keys(),
                        key=f"frag_ronda_{ronda}"
                    )
                    secuencia_actual = opciones[seleccion]
            
                # --- Selección del cortador ---
                cortador = st.selectbox(
                    f"Selecciona cortador (Ronda {ronda + 1}):",
                    list(cortadores.keys()),
                    key=f"corte_ronda_{ronda}"
                )
                modo = cortadores[cortador]["modo"]
                residuos = cortadores[cortador]["residuos"]
                
                # Mostrar descripción del cortador
                if modo == "aleatorio":
                    st.info("**Digestión con HCl 6M**: corte aleatorio no específico, genera fragmentos que incluyen todos los aminoácidos presentes, con posibles repeticiones.")
                else:
                    st.info(f"**{cortador}** corta **{modo}** los siguientes residuos: {', '.join(residuos)}")
            
                # --- Aplicar corte ---
                if modo == "aleatorio":
                    nuevos = digestion_aleatoria_controlada(secuencia_actual)
                else:
                    nuevos = cortar_peptido(secuencia_actual, residuos, modo)
            
                # --- Mostrar resultado ---
                st.markdown(f"**{cortador} aplicado sobre {seleccion} → Fragmentos generados:**")
                for i, frag in enumerate(nuevos, 1):
                    st.markdown(f"- Fragmento {i}: `{frag}`")
            
                return nuevos

            # --- DETECTAR CAMBIO DE CÓDIGO ---
            codigo_actual = codigo_ingresado  # corregido
            
            if "codigo_anterior" not in st.session_state:
                st.session_state.codigo_anterior = codigo_actual
            
            if st.session_state.codigo_anterior != codigo_actual:
                st.session_state.codigo_anterior = codigo_actual
                # Reiniciar termociclador
                for key in ["fragmentos_disponibles", "resumen_rondas", "numero_ronda"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

            # --- INICIO DEL TERMO CICLADOR ---
            st.markdown("## 🧪 Termociclador virtual")

            # --- INICIALIZACIÓN DEL ESTADO ---
            if "fragmentos_disponibles" not in st.session_state:
                st.session_state.fragmentos_disponibles = {"R0 - Secuencia original": secuencia}
            if "resumen_rondas" not in st.session_state:
                st.session_state.resumen_rondas = []
            if "numero_ronda" not in st.session_state:
                st.session_state.numero_ronda = 1

            # --- DESPLEGABLE: Selección de secuencia/fragmento ---
            fragmento_seleccionado_label = st.selectbox(
                "Selecciona la secuencia o fragmento que deseas cortar:",
                list(st.session_state.fragmentos_disponibles.keys())
            )
            fragmento_seleccionado = st.session_state.fragmentos_disponibles[fragmento_seleccionado_label]

            # --- DESPLEGABLE: Cortador ---
            cortador = st.selectbox("Selecciona el cortador:", list(cortadores.keys()))
            modo = cortadores[cortador]["modo"]
            residuos = cortadores[cortador]["residuos"]

            # --- Mostrar explicación del cortador ---
            if modo == "aleatorio":
                st.info("**Digestión con HCl 6M**: corte aleatorio no específico, genera fragmentos que incluyen todos los aminoácidos presentes, con posibles repeticiones.")
                fragmentos_generados = digestion_aleatoria_controlada(fragmento_seleccionado)
            else:
                st.info(f"**{cortador}** corta **{modo}** los residuos: {', '.join(residuos)}")
                fragmentos_generados = cortar_peptido(fragmento_seleccionado, residuos, modo)

            # --- Mostrar fragmentos generados ---
            st.markdown("**Fragmentos generados:**")
            for i, frag in enumerate(fragmentos_generados, 1):
                st.markdown(f"- Fragmento {i}: `{frag}`")

            # --- GUARDAR RESULTADO EN EL RESUMEN ---
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
                    st.warning("⚠️ Se alcanzó el máximo de 10 rondas.")
# --- RESUMEN FINAL ---
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

# --- BOTÓN PARA REINICIAR TODO ---
if st.button("🔁 Reiniciar termociclador"):
    for key in ["fragmentos_disponibles", "resumen_rondas", "numero_ronda"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Termociclador reiniciado. Puedes comenzar de nuevo.")
    st.experimental_rerun()
