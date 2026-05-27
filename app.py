import streamlit as st
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

st.set_page_config(page_title="HipPlanner AI", layout="wide")

st.title("🦿 HipPlanner AI — Planificador Manual de Precisión")
st.write("Selecciona los puntos anatómicos directamente para calcular la dismetría y el offset.")

# Barra lateral
st.sidebar.header("1. Parámetros del Paciente")
uploaded_file = st.sidebar.file_uploader("Subir Radiografía AP de Pelvis", type=["png", "jpg", "jpeg", "webp"])
px_por_mm = st.sidebar.number_input("Factor de Calibración (píxeles por mm)", min_value=0.1, max_value=20.0, value=4.2, step=0.1)
lado_operar = st.sidebar.radio("Lado Patológico (A Operar)", ["Derecho", "Izquierdo"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    h, w = img_np.shape[:2]

    st.subheader("2. Marcación de Hitos Anatómicos")
    st.info("Mueve los deslizadores para posicionar los puntos exactamente sobre la anatomía del paciente.")

    col_ctrls, col_img = st.columns([1, 2])

    with col_ctrls:
        st.markdown("**Lágrimas del Acetábulo (Referencia Horizontal)**")
        t_izq_x = st.slider("Lágrima Izquierda (X)", 0, w, int(w * 0.55))
        t_izq_y = st.slider("Lágrima Izquierda (Y)", 0, h, int(h * 0.50))
        t_der_x = st.slider("Lágrima Derecha (X)", 0, w, int(w * 0.45))
        t_der_y = st.slider("Lágrima Derecha (Y)", 0, h, int(h * 0.50))

        st.markdown("**Puntas de Trocánter Mayor (PTM)**")
        ptm_izq_x = st.slider("PTM Izquierda (X)", 0, w, int(w * 0.70))
        ptm_izq_y = st.slider("PTM Izquierda (Y)", 0, h, int(h * 0.62))
        ptm_der_x = st.slider("PTM Derecha (X)", 0, w, int(w * 0.30))
        ptm_der_y = st.slider("PTM Derecha (Y)", 0, h, int(h * 0.64))

    # Cálculos Biomecánicos
    y_lil = int((t_izq_y + t_der_y) / 2)
    dist_izq_mm = abs(ptm_izq_y - y_lil) / px_por_mm
    dist_der_mm = abs(ptm_der_y - y_lil) / px_por_mm
    lld = abs(dist_der_mm - dist_izq_mm)
    lado_corto = "Derecho" if dist_der_mm > dist_izq_mm else "Izquierdo"

    # Generación del gráfico con Matplotlib
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img_np)
    
    # Líneas y puntos quirúrgicos
    ax.axhline(y=y_lil, color='red', linestyle='-', linewidth=2.5, label="Línea Inter-lagrimal (LIL)")
    ax.vlines(x=ptm_izq_x, ymin=min(y_lil, ptm_izq_y), ymax=max(y_lil, ptm_izq_y), color='orange', linestyle='--')
    ax.vlines(x=ptm_der_x, ymin=min(y_lil, ptm_der_y), ymax=max(y_lil, ptm_der_y), color='orange', linestyle='--')
    ax.scatter([t_izq_x, t_der_x], [t_izq_y, t_der_y], color='cyan', s=100, zorder=5, label="Lágrimas")
    ax.scatter([ptm_izq_x, ptm_der_x], [ptm_izq_y, ptm_der_y], color='magenta', s=100, zorder=5, label="PTM")
    
    ax.axis('off')
    ax.legend(loc='upper right')

    with col_img:
        st.pyplot(fig)

    # Reporte Clínico
    st.markdown("---")
    st.subheader("📋 Reporte de Planificación")
    c1, c2 = st.columns(2)
    c1.metric(label="Dismetría Pélvica (LLD)", value=f"{lld:.1f} mm", delta=f"Lado {lado_corto} más corto", delta_color="inverse")
    c2.info(f"**Sugerencia Quirúrgica:** Para ecualizar las extremidades, el complejo copa/vástago/cuello en el lado patológico debe aportar una corrección vertical neta de **{round(lld)} mm**.")