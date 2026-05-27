import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math
# Componente crítico para registrar clics exactos en la imagen
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="HipPlanner Click-to-Plan", layout="wide")

st.title("🦿 HipPlanner AI — Planificación Dinámica por Clics")
st.write("Flujo guiado secuencial para el cálculo biomecánico completo y estimación de componentes.")

# --- CONFIGURACIÓN DE HITOS ANATÓMICOS ---
PUNTOS_CONFIG = [
    ("teardrop_izq", "🟢 Lágrima Izquierda (Punto inferior-medial)"),
    ("teardrop_der", "🟢 Lágrima Derecha (Punto inferior-medial)"),
    ("borde_ace", "🟣 Borde Súpero-Lateral del Acetábulo (Lado a operar)"),
    ("kohler_izq", "🔵 Línea de Köhler Izquierda (Frontera de pared medial)"),
    ("kohler_der", "🔵 Línea de Köhler Derecha (Frontera de pared medial)"),
    ("cor_izq", "🔴 Centro de Rotación (COR) Anatómico Izquierdo"),
    ("cor_der", "🔴 Centro de Rotación (COR) Derecho"),
    ("ptm_izq", "🟡 Trocánter Mayor Izquierdo (PTM)"),
    ("ptm_der", "🟡 Trocánter Mayor Derecho (PTM)"),
    ("ptm_menor_izq", "🟠 Trocánter Menor Izquierdo (PTm)"),
    ("ptm_menor_der", "🟠 Trocánter Menor Derecho (PTm)"),
    ("eje_izq", "⚪ Eje Anatómico Femoral Izquierdo (Punto en centro de diáfisis)"),
    ("eje_der", "⚪ Eje Anatómico Femoral Derecho (Punto en centro de diáfisis)")
]

# --- INICIALIZACIÓN DEL ESTADO DE LA APLICACIÓN ---
if "puntos" not in st.session_state:
    st.session_state.puntos = {k: None for k, _ in PUNTOS_CONFIG}
if "idx_actual" not in st.session_state:
    st.session_state.idx_actual = 0
if "last_click" not in st.session_state:
    st.session_state.last_click = None

# --- BARRA LATERAL CONTROLES ---
st.sidebar.header("1. Parámetros y Herramientas")
uploaded_file = st.sidebar.file_uploader("Subir Radiografía AP de Pelvis", type=["png", "jpg", "jpeg", "webp"])
px_por_mm = st.sidebar.number_input("Factor de Calibración (píxeles por mm)", min_value=0.1, max_value=20.0, value=4.2, step=0.1)
lado_operar = st.sidebar.radio("Lado Patológico (A Operar)", ["Derecho", "Izquierdo"])

# Botones de navegación del flujo de marcado
st.sidebar.markdown("---")
st.sidebar.markdown("### 🕹️ Navegación de Puntos")
col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("⏮️ Anterior") and st.session_state.idx_actual > 0:
        st.session_state.idx_actual -= 1
        st.rerun()
with col_b2:
    if st.button("⏭️ Omitir") and st.session_state.idx_actual < len(PUNTOS_CONFIG) - 1:
        st.session_state.idx_actual += 1
        st.rerun()

if st.sidebar.button("🔄 Reiniciar Todo el Trazado"):
    st.session_state.puntos = {k: None for k, _ in PUNTOS_CONFIG}
    st.session_state.idx_actual = 0
    st.session_state.last_click = None
    st.rerun()

# --- PROCESAMIENTO QUIRÚRGICO ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    # Mostrar checklist visual en la barra lateral
    st.sidebar.markdown("### 📋 Progreso del Mapeo")
    for idx, (key, name) in enumerate(PUNTOS_CONFIG):
        status = "✅" if st.session_state.puntos[key] is not None else "⚪"
        if idx == st.session_state.idx_actual:
            st.sidebar.markdown(f"👉 **{status} {name}**")
        else:
            st.sidebar.markdown(f"<span style='color:gray'>{status} {name}</span>", unsafe_allow_html=True)

    # Contenedor de interfaz principal (Lienzo izquierdo, Reporte derecho)
    col_canvas, col_reporte = st.columns([1.4, 1])
    
    with col_canvas:
        idx = st.session_state.idx_actual
        key_actual = PUNTOS_CONFIG[idx][0]
        name_actual = PUNTOS_CONFIG[idx][1]
        
        # Cartel indicativo de flujo de trabajo
        if idx < len(PUNTOS_CONFIG):
            st.warning(f"📍 **POR FAVOR, HAZ CLIC EN: {name_actual}**")
        else:
            st.success("🎉 ¡Mapeo completo! Revisa los resultados en el panel lateral.")

        # COMPONENTE INTERACTIVO DE CLIC (Ancho fijo óptimo para scrolling en Android y PC)
        value = streamlit_image_coordinates(image, width=680, key="hip_canvas")
        
        if value is not None:
            click_coord = (value["x"], value["y"])
            # Validación para evitar bucles repetitivos de refresco
            if st.session_state.last_click != click_coord:
                st.session_state.last_click = click_coord
                st.session_state.puntos[key_actual] = click_coord
                # Avanzar secuencialmente de forma automática
                if st.session_state.idx_actual < len(PUNTOS_CONFIG) - 1:
                    st.session_state.idx_actual += 1
                st.rerun()

    # --- GEOMETRÍA COMPUTACIONAL Y TRAZADO (MATPLOTLIB) ---
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img_np)
    pts = st.session_state.puntos

    # Trazado de la Línea Inter-lagrimal (LIL) [Roja, Gruesa]
    if pts["teardrop_izq"] and pts["teardrop_der"]:
        y_lil = int((pts["teardrop_izq"][1] + pts["teardrop_der"][1]) / 2)
        ax.axhline(y=y_lil, color='red', linestyle='-', linewidth=2.5, label="Línea Inter-lagrimal (LIL)")
        
        # Marcadores verticales de dismetría hacia la LIL
        if pts["ptm_izq"]:
            ax.vlines(x=pts["ptm_izq"][0], ymin=min(y_lil, pts["ptm_izq"][1]), ymax=max(y_lil, pts["ptm_izq"][1]), color='orange', linestyle='--')
        if pts["ptm_der"]:
            ax.vlines(x=pts["ptm_der"][0], ymin=min(y_lil, pts["ptm_der"][1]), ymax=max(y_lil, pts["ptm_der"][1]), color='orange', linestyle='--')

    # Líneas de Köhler (Cian)
    if pts["kohler_izq"]: ax.axvline(x=pts["kohler_izq"][0], color='cyan', linestyle=':', linewidth=2, label="Línea Köhler")
    if pts["kohler_der"]: ax.axvline(x=pts["kohler_der"][0], color='cyan', linestyle=':')
    
    # Ejes Femorales (Amarillo)
    if pts["eje_izq"]: ax.axvline(x=pts["eje_izq"][0], color='yellow', linestyle='--', linewidth=1.5, label="Eje Femoral")
    if pts["eje_der"]: ax.axvline(x=pts["eje_der"][0], color='yellow', linestyle='--')

    # Dibujar los puntos que ya han sido clicados en el lienzo
    for k_name, _ in PUNTOS_CONFIG:
        coor = pts[k_name]
        if coor is not None:
            c_dot = 'red' if 'teardrop' in k_name else ('blue' if 'cor' in k_name else 'magenta')
            ax.scatter(coor[0], coor[1], color=c_dot, s=110, zorder=5)

    # Superposición de la copa acetabular (Círculo de orientación a 40°)
    if pts["teardrop_der"] and pts["borde_ace"] and lado_operar == "Derecho":
        r_px = math.dist(pts["teardrop_der"], pts["borde_ace"])
        circle = plt.Circle(pts["teardrop_der"], r_px, color='green', fill=False, linestyle='-', linewidth=2, label="Copa Estimada (40°)")
        ax.add_patch(circle)
    elif pts["teardrop_izq"] and pts["borde_ace"] and lado_operar == "Izquierdo":
        r_px = math.dist(pts["teardrop_izq"], pts["borde_ace"])
        circle = plt.Circle(pts["teardrop_izq"], r_px, color='green', fill=False, linestyle='-', linewidth=2, label="Copa Estimada (40°)")
        ax.add_patch(circle)

    ax.axis('off')
    
    with col_canvas:
        st.markdown("### Radiografía Anotada en Tiempo Real")
        st.pyplot(fig)

    # --- PANEL DE CÁLCULO DE MEDIDAS BIOMECÁNICAS ---
    with col_reporte:
        st.subheader("📋 Parámetros Biomecánicos Calculados")
        
        # 1. Estimación del Tamaño de la Copa Acetabular (Best-Fit Óseo)
        teardrop_ref = "teardrop_der" if lado_operar == "Derecho" else "teardrop_izq"
        if pts[teardrop_ref] and pts["borde_ace"]:
            dist_px = math.dist(pts[teardrop_ref], pts["borde_ace"])
            diametro_mm = (dist_px / px_por_mm) * 2  # Se asume el radio anatómico hasta el borde óseo externo
            
            # Ajuste a tamaño de copa comercial (números pares estándar)
            tamano_copa_estimado = int(2 * round(diametro_mm / 2))
            
            st.success(f"### 🔘 Componente Acetabular Sugerido:\n**Copa Acetabular Tamaño: {tamano_copa_estimado} mm**\n\n*Inclinación recomendada: 40° ± 10° respecto a la LIL.*")
        else:
            st.info("💡 Completa los clics de las Lágrimas y el Borde Acetabular para estimar el tamaño de la copa.")

        st.markdown("---")
        
        # 2. Control de Dismetría (LLD)
        if pts["teardrop_izq"] and pts["teardrop_der"] and pts["ptm_izq"] and pts["ptm_der"]:
            y_lil = (pts["teardrop_izq"][1] + pts["teardrop_der"][1]) / 2
            d_izq = abs(pts["ptm_izq"][1] - y_lil) / px_por_mm
            d_der = abs(pts["ptm_der"][1] - y_lil) / px_por_mm
            lld_m = abs(d_der - d_izq)
            lcorto = "Derecho" if d_der > d_izq else "Izquierdo"
            st.metric(label="Dismetría Trocánter Mayor (LLD)", value=f"{lld_m:.1f} mm", delta=f"Lado {lcorto} más corto", delta_color="inverse")
        
        if pts["ptm_menor_izq"] and pts["ptm_menor_der"]:
            lld_menor = abs(pts["ptm_menor_der"][1] - pts["ptm_menor_izq"][1]) / px_por_mm
            st.metric(label="Dismetría Trocánter Menor", value=f"{lld_menor:.1f} mm", delta="Referencia de altura de corte femoral")

        # 3. Offsets Horizontales
        st.markdown("### 📐 Análisis de Offsets")
        off_f_izq = abs(pts["cor_izq"][0] - pts["eje_izq"][0]) / px_por_mm if (pts["cor_izq"] and pts["eje_izq"]) else 0
        off_f_der = abs(pts["cor_der"][0] - pts["eje_der"][0]) / px_por_mm if (pts["cor_der"] and pts["eje_der"]) else 0
        
        st.write(f"Offset Femoral Izquierdo: **{off_f_izq:.1f} mm**" if off_f_izq > 0 else "Offset Femoral Izq: *Pendiente*")
        st.write(f"Offset Femoral Derecho: **{off_f_der:.1f} mm**" if off_f_der > 0 else "Offset Femoral Der: *Pendiente*")

        # Alerta de Protrusión con Línea de Köhler
        if pts["cor_der"] and pts["kohler_der"] and lado_operar == "Derecho":
            if pts["cor_der"][0] > pts["kohler_der"][0]:
                st.error("🚨 Alerta de Estabilidad: El COR cruza la línea de Köhler (Peligro de protrusión acetabular).")
else:
    st.info("👋 Por favor, sube una radiografía AP de pelvis para iniciar la secuencia de planificación.")
