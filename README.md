# 🧪 Termociclador Virtual para Secuenciación de Péptidos

Este proyecto es una aplicación educativa interactiva desarrollada en **Streamlit** para simular el proceso de **secuenciación de péptidos**. Está diseñada para estudiantes de Bioquímica, Biotecnología y áreas afines, permitiéndoles identificar experimentalmente la secuencia de un péptido, a partir de información parcial como proporciones másicas, peso molecular y resultados de digestiones específicas.

## 🎯 Objetivos

- Simular un experimento de secuenciación paso a paso.
- Permitir selección y aplicación de enzimas/cortadores sobre fragmentos.
- Validar hipótesis de secuencia (lineal o cíclica).
- Visualizar y registrar las rondas de digestión realizadas.

## 🧬 Flujo de la aplicación

1. **Ingreso de código de muestra**  
   El usuario introduce un código (`P001`, `P002`, etc.) para obtener los datos del péptido desde una hoja de cálculo pública en Google Sheets.

2. **Cálculo automático del peso molecular**  
   Se calcula el peso total y se presentan las proporciones másicas de cada aminoácido.

3. **Verificación del número de residuos**  
   El estudiante debe deducir el número de aminoácidos a partir de los datos anteriores.

4. **Simulación del termociclador**  
   - Selección de un fragmento o la secuencia original.
   - Aplicación de cortadores como Tripsina, Pepsina, CNBr, Bromelina, HCl 6M (corte aleatorio), entre otros.
   - Visualización de fragmentos generados.
   - Registro de rondas hasta un máximo de 10.

5. **Validación de la secuencia propuesta**  
   El estudiante puede ingresar la secuencia que considera correcta.  
   - Para péptidos **cíclicos**, debe iniciar con `(c)` y puede comenzar desde cualquier punto de la cadena.
   - Para péptidos **lineales**, la coincidencia debe ser exacta.

## 🧩 Tecnologías utilizadas

- [Streamlit](https://streamlit.io/)
- [Python 3.10+](https://www.python.org/)
- [Pandas](https://pandas.pydata.org/)
- Google Sheets API pública (sin autenticación)

## 📁 Estructura esperada del archivo en Google Sheets

Hoja oculta `Cys` con las siguientes columnas:

| Código | Secuencia      | Cíclico |
|--------|----------------|---------|
| P001   | AKGEFLMKG      | No      |
| P002   | (c)FELKAMRG    | Sí      |

> ⚠️ Asegúrate de que esta hoja esté configurada como pública para que Streamlit pueda accederla sin autenticación.

## 🧠 Consideraciones

- El número de fragmentos generados por digestión con **HCl 6M** es dinámico:
  - 5 fragmentos si el péptido tiene ≤10 residuos.
  - +1 fragmento por cada 3 residuos adicionales.
- El sistema reinicia automáticamente las rondas si se cambia el código de muestra.
- El botón de reinicio permite al usuario comenzar una nueva simulación sin recargar manualmente la página.

## 🚀 Ejecución local

1. Instala los requisitos:

   ```bash
   pip install streamlit pandas
   ```

2. Ejecuta la app:

   ```bash
   streamlit run Termociclador.py
   ```

## 📜 Licencia

Este proyecto es de uso educativo y puede modificarse libremente para fines académicos.

---

Desarrollado con 🤍 por [Tu Nombre o Institución]