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
            
            # --- INICIO DEL TERMO CICLADOR ---
            st.markdown("## 🧪 Termociclador virtual")
            
           # --- INICIALIZACIÓN Y RONDA 1 ---
            if "num_rondas" not in st.session_state:
                num_rondas = 3
                if numero_real > 10:
                    num_rondas += (numero_real - 10) // 5
                st.session_state["num_rondas"] = num_rondas
            
            # Guardamos la secuencia original como input base
            st.session_state["fragmentos_ronda_0"] = [secuencia]
            
            # Ejecutamos ronda 1
            fragmentos_ronda_1 = ejecutar_ronda(0, st.session_state["fragmentos_ronda_0"])
            st.session_state["fragmentos_ronda_1"] = fragmentos_ronda_1
            
            # Guardamos selecciones de ronda 1 para detectar cambios
            if "seleccion_ronda_1" not in st.session_state:
                st.session_state["seleccion_ronda_1"] = {
                    "fragmento": "Secuencia original",
                    "cortador": st.session_state.get("corte_ronda_0")
                }
            
            # Detectar si se ha cambiado la selección en ronda 1
            seleccion_actual_ronda_1 = {
                "fragmento": "Secuencia original",  # ronda 1 siempre usa secuencia original
                "cortador": st.session_state.get("corte_ronda_0")
            }
            
            # Si cambió, reiniciamos estado posterior y pregunta
            if seleccion_actual_ronda_1 != st.session_state["seleccion_ronda_1"]:
                st.warning("Has cambiado la selección de la primera ronda. Rondas posteriores han sido reiniciadas.")
                st.session_state["seleccion_ronda_1"] = seleccion_actual_ronda_1
                if "fragmentos_ronda_2" in st.session_state:
                    del st.session_state["fragmentos_ronda_2"]
                if "seleccion_ronda_2" in st.session_state:
                    del st.session_state["seleccion_ronda_2"]
                if "hacer_otra_ronda_2" in st.session_state:
                    del st.session_state["hacer_otra_ronda_2"]
            
            # PREGUNTA: ¿Quieres hacer otro corte?
            if "hacer_otra_ronda_2" not in st.session_state:
                st.session_state["hacer_otra_ronda_2"] = None
            
            st.session_state["hacer_otra_ronda_2"] = st.radio(
                "¿Quieres hacer otro corte?",
                ["No", "Sí"],
                index=0 if st.session_state["hacer_otra_ronda_2"] is None else ["No", "Sí"].index(st.session_state["hacer_otra_ronda_2"]),
                key="radio_ronda_2"
            )
            
            # Ejecutar ronda 2 solo si el estudiante dijo que sí
            if st.session_state["hacer_otra_ronda_2"] == "Sí":
                fragmentos_ronda_2 = ejecutar_ronda(1, fragmentos_ronda_1)
                st.session_state["fragmentos_ronda_2"] = fragmentos_ronda_2
                st.session_state["seleccion_ronda_2"] = {
                    "fragmento": st.session_state.get("frag_ronda_1"),
                    "cortador": st.session_state.get("corte_ronda_1")
                }

            # --- CONTROL DE RONDA 3 ---
        
            # Verificar si ronda 2 existe
            if "fragmentos_ronda_2" in st.session_state:
            
                # Guardar selecciones de ronda 2 si aún no se han registrado
                if "seleccion_ronda_2" not in st.session_state:
                    st.session_state["seleccion_ronda_2"] = {
                        "fragmento": st.session_state.get("frag_ronda_1"),
                        "cortador": st.session_state.get("corte_ronda_1")
                    }
            
                # Comparar selecciones actuales de ronda 2
                seleccion_actual_ronda_2 = {
                    "fragmento": st.session_state.get("frag_ronda_1"),
                    "cortador": st.session_state.get("corte_ronda_1")
                }
            
                # Si cambió algo, reiniciamos ronda 3
                if seleccion_actual_ronda_2 != st.session_state["seleccion_ronda_2"]:
                    st.warning("Has cambiado la selección de la segunda ronda. Ronda 3 ha sido reiniciada.")
                    if "fragmentos_ronda_3" in st.session_state:
                        del st.session_state["fragmentos_ronda_3"]
                    if "seleccion_ronda_3" in st.session_state:
                        del st.session_state["seleccion_ronda_3"]
                    if "hacer_otra_ronda_3" in st.session_state:
                        del st.session_state["hacer_otra_ronda_3"]
                    st.session_state["seleccion_ronda_2"] = seleccion_actual_ronda_2
            
                # Mostrar botón de decisión si no ha cambiado nada
                if "hacer_otra_ronda_3" not in st.session_state:
                    st.session_state["hacer_otra_ronda_3"] = None
            
                st.session_state["hacer_otra_ronda_3"] = st.radio(
                    "¿Quieres hacer otro corte (ronda 3)?",
                    ["No", "Sí"],
                    index=0 if st.session_state["hacer_otra_ronda_3"] is None else ["No", "Sí"].index(st.session_state["hacer_otra_ronda_3"]),
                    key="radio_ronda_3"
                )
            
                # Ejecutar ronda 3 solo si se aceptó continuar
                if st.session_state["hacer_otra_ronda_3"] == "Sí":
                    fragmentos_ronda_3 = ejecutar_ronda(2, st.session_state["fragmentos_ronda_2"])
                    st.session_state["fragmentos_ronda_3"] = fragmentos_ronda_3
                    st.session_state["seleccion_ronda_3"] = {
                        "fragmento": st.session_state.get("frag_ronda_2"),
                        "cortador": st.session_state.get("corte_ronda_2")
                    }
