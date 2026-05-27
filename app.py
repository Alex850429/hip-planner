import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
# Requiere instalar: pip install streamlit-image-coordinates
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="HipPlanner Click Pro", layout="wide")

st.title("🦿 HipPlanner AI — Planificación por Clic Quirúrgico")
st.write("Planifique con máxima rapidez haciendo clic directamente sobre las estructuras anatómicas de la radiografía.")

# --- DECLARACIÓN DEL FLUJO SECUENCIAL DE HITOS ---
PUNTOS_CONFIG = [
    ("teardrop_izq", "🟢 Lágrima Izquierda (Referencia Base H)"),
    ("teardrop_der", "🟢 Lágrima Derecha (Referencia Base H)"),
    ("kohler_izq", "🔵 Línea de Köhler Izquierda (Pared Medial)"),
    ("kohler_der", "🔵 Línea de Köhler Derecha (Pared Medial)"),
    ("cor_izq", "🔴 Centro de Rotación (COR) Izquierdo"),
    ("cor_der", "🔴 Centro de Rotación (COR) Derecho"),
    ("ptm_izq", "🟡 Trocánter Mayor Izquierdo (Altura Distal)"),
    ("ptm_der", "🟡 Trocánter Mayor Derecho (Altura Distal)"),
    ("ptm_menor_izq", "🟠 Trocánter Menor Izquierdo (Corte de Cuello)"),
    ("ptm_menor_der", "🟠 Trocánter Menor Derecho (Corte de Cuello)"),
    ("eje_izq", "⚪ Eje Anatómico Femoral Izquierdo"),
    ("eje_der", "⚪ Eje Anatómico Femoral Derecho")
]

# --- INICIALIZACIÓN DE ESTADOS (SESSION STATE) ---
if "puntos" not in st.session_state:
    st.session_state.puntos = {k: None for k, _ in PUNTOS_CONFIG}
if "idx_actual" not in st.session_state:
    st.session_state.idx_actual = 0

# --- BARRA LATERAL ---
st.sidebar.header("1. Configuración")
uploaded_file = st.sidebar.file_uploader("Subir Radiografía AP de Pelvis", type=["png", "jpg", "jpeg", "webp"])
px_por_mm = st.sidebar.number_input("Factor de Calibración (px/mm)", min_value=0.1, max_value=20.0, value=4.2, step=0.1)
lado_operar = st.sidebar.radio("Lado Patológico (A Operar)", ["Derecho", "Izquierdo"])

# Botón para reiniciar el mapeo
if st.sidebar.button("🔄 Reiniciar Todos los Puntos"):
    st.session_state.puntos = {k: None for k, _ in PUNTOS_CONFIG}
    st.session_state.idx_actual = 0
    st.rerun()

# --- VALIDACIÓN DE CARGA DE ARCHIVO ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    # Mostrar checklist del estado de marcación en la barra lateral
    st.sidebar.markdown("### 📋 Estado del Mapeo")
    for idx, (key, name) in enumerate(PUNTOS_CONFIG):
        status = "✅" if st.session_state.puntos[key] is not None else "⚪"
        if idx == st.session_state.idx_actual:
            st.sidebar.markdown(f"👉 **{status} {name}** (Esperando Clic)")
        else:
            st.sidebar.markdown(f"{status} {name}")

    # Control manual del flujo de puntos
    st.sidebar.markdown("---")
    st.session_state.idx_actual = st.sidebar.selectbox(
        "Cambiar manualmente punto activo:", 
        range(len(PUNTOS_CONFIG)), 
        format_func=lambda x: PUNTOS_CONFIG[x][1],
        index=st.session_state.idx_actual
    )

    # --- FLUJO PRINCIPAL DE CAPTURA DE CLICS ---
    col_img, col_rep = st.columns([1.5, 1])
    
    with col_img:
        key_actual = PUNTOS_CONFIG[st.session_state.idx_actual][0]
        name_actual = PUNTOS_CONFIG[st.session_state.idx_actual][1]
        
        st.subheader(f"📍 Objetivo Actual: {name_actual}")
        st.info("Haz clic o toca directamente sobre la imagen para registrar la posición.")
        
        # Renderizado del componente interactivo de clics (Ancho fijo de 650px óptimo para móviles y PC)
        value = streamlit_image_coordinates(image, width=650, key="click_canvas")
        
        if value is not None:
            click_coord = (value["x"], value["y"])
            
            # Evitar bucles infinitos validando si es un clic nuevo
            if st.session_state.puntos[key_actual] != click_coord:
                st.session_state.puntos[key_actual] = click_coord
                # Avanzar automáticamente al siguiente punto si no es el último
                if st.session_state.idx_actual < len(PUNTOS_CONFIG) - 1:
                    st.session_state.idx_actual += 1
                st.rerun()

    # --- RENDERIZADO GRÁFICO PREOPERATORIO EN TIEMPO REAL ---
    # Generamos dinámicamente el overlay matemático basado en los puntos que ya existan
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img_np)
    
    pts = st.session_state.puntos
    
    # 1. Línea Inter-lagrimal (LIL)
    if pts["teardrop_izq"] and pts["teardrop_der"]:
        y_lil = int((pts["teardrop_izq"][1] + pts["teardrop_der"][1]) / 2)
        ax.axhline(y=y_lil, color='red', linestyle='-', linewidth=2.5, label="LIL (Referencia)")
        
        # Líneas verticales de dismetría si existen los trocánteres
        if pts["ptm_izq"]:
            ax.vlines(x=pts["ptm_izq"][0], ymin=min(y_lil, pts["ptm_izq"][1]), ymax=max(y_lil, pts["ptm_izq"][1]), color='orange', linestyle='--')
        if pts["ptm_der"]:
            ax.vlines(x=pts["ptm_der"][0], ymin=min(y_lil, pts["ptm_der"][1]), ymax=max(y_lil, pts["ptm_der"][1]), color='orange', linestyle='--')

    # 2. Líneas de Köhler
    if pts["kohler_izq"]: ax.axvline(x=pts["kohler_izq"][0], color='cyan', linestyle=':', linewidth=2, label="L. Köhler")
    if pts["kohler_der"]: ax.axvline(x=pts["kohler_der"][0], color='cyan', linestyle=':')
    
    # 3. Ejes Anatómicos Femorales
    if pts["eje_izq"]: ax.axvline(x=pts["eje_izq"][0], color='yellow', linestyle='--', linewidth=1.5, label="Eje Anatómico")
    if pts["eje_der"]: ax.axvline(x=pts["eje_der"][0], color='yellow', linestyle='--', linewidth=1.5)

    # Dibujar marcadores físicos de los puntos ya seleccionados
    for key, (k_name, _) in enumerate(PUNTOS_CONFIG):
        coor = pts[k_name]
        if coor is not None:
            color_mark = 'red' if 'teardrop' in k_name else ('blue' if 'cor' in k_name else 'magenta')
            ax.scatter(coor[0], coor[1], color=color_mark, s=120, zorder=5)

    ax.axis('off')
    
    with col_img:
        st.markdown("### Visualización del Trazado Quirúrgico")
        st.pyplot(fig)

    # --- PROCESAMIENTO Y REPORTE DE MEDIDAS BIOMECÁNICAS ---
    with col_rep:
        st.subheader("📋 Reporte Clínico en Tiempo Real")
        
        # Validar si tenemos los puntos mínimos para cálculos críticos
        if pts["teardrop_izq"] and pts["teardrop_der"] and pts["ptm_izq"] and pts["ptm_der"]:
            y_lil = (pts["teardrop_izq"][1] + pts["teardrop_der"][1]) / 2
            dist_izq = abs(pts["ptm_izq"][1] - y_lil) / px_por_mm
            dist_der = abs(pts["ptm_der"][1] - y_lil) / px_por_mm
            lld_m = abs(dist_der - dist_izq)
            lcorto = "Derecho" if dist_der > dist_izq else "Izquierdo"
            st.metric(label="Dismetría Trocánter Mayor (LLD)", value=f"{lld_m:.1f} mm", delta=f"Lado {lcorto} más corto", delta_color="inverse")
        else:
            st.info("Faltan puntos de alineación para calcular dismetría del Trocánter Mayor.")
            
        if pts["ptm_menor_izq"] and pts["ptm_menor_der"]:
            lld_menor = abs(pts["ptm_menor_der"][1] - pts["ptm_menor_izq"][1]) / px_por_mm
            st.metric(label="Dismetría Trocánter Menor", value=f"{lld_menor:.1f} mm", delta="Referencia para corte de cuello")

        st.markdown("---")
        st.markdown("### 📐 Estado de Offsets")
        
        # Cálculos de Offsets Femorales (COR al Eje)
        off_f_izq = abs(pts["cor_izq"][0] - pts["eje_izq"][0]) / px_por_mm if (pts["cor_izq"] and pts["eje_izq"]) else 0
        off_f_der = abs(pts["cor_der"][0] - pts["eje_der"][0]) / px_por_mm if (pts["cor_der"] and pts["eje_der"]) else 0
        
        st.write(f"Offset Femoral Izquierdo: **{off_f_izq:.1f} mm**" if off_f_izq > 0 else "Offset Femoral Izq: *Pendiente clics*")
        st.write(f"Offset Femoral Derecho: **{off_f_der:.1f} mm**" if off_f_der > 0 else "Offset Femoral Der: *Pendiente clics*")

        # Alerta de Protrusión con Línea de Köhler
        if pts["cor_der"] and pts["kohler_der"]:
            if pts["cor_der"][0] > pts["kohler_der"][0] and lado_operar == "Derecho":
                st.error("🚨 Alerta: COR Derecho cruza medialmente la línea de Köhler (Riesgo de protrusión).")

else:
    st.info("👋 Por favor, sube una radiografía AP de pelvis en el panel izquierdo para activar el lienzo interactivo.")
