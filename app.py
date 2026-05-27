import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

st.set_page_config(page_title="HipPlanner AI Pro", layout="wide")

st.title("🦿 HipPlanner AI — Planificación Biomecánica Avanzada")
st.write("Análisis completo de dismetría, offsets, línea de Köhler y reconstrucción del Centro de Rotación.")

# --- BARRA LATERAL ---
st.sidebar.header("1. Parámetros Clínicos y Calibración")
uploaded_file = st.sidebar.file_uploader("Subir Radiografía AP de Pelvis", type=["png", "jpg", "jpeg", "webp"])
px_por_mm = st.sidebar.number_input("Factor de Calibración (píxeles por mm)", min_value=0.1, max_value=20.0, value=4.2, step=0.1)
lado_operar = st.sidebar.radio("Lado Patológico (A Operar)", ["Derecho", "Izquierdo"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    h, w = img_np.shape[:2]

    st.subheader("2. Mapeo Quirúrgico Manual")
    st.info("Ajuste los controles para hacer coincidir los marcadores con la anatomía radiográfica exacta del paciente.")

    col_ctrls, col_img = st.columns([1, 1.8])

    with col_ctrls:
        with st.expander("🟢 Referencias Pélvicas Base", expanded=True):
            t_izq_x = st.slider("Lágrima Izquierda (X)", 0, w, int(w * 0.55))
            t_izq_y = st.slider("Lágrima Izquierda (Y)", 0, h, int(h * 0.50))
            t_der_x = st.slider("Lágrima Derecha (X)", 0, w, int(w * 0.45))
            t_der_y = st.slider("Lágrima Derecha (Y)", 0, h, int(h * 0.50))
            
            st.markdown("**Línea de Köhler (Línea Ilioisquiática)**")
            kohler_izq_x = st.slider("Köhler Izquierda (X)", 0, w, int(w * 0.53))
            kohler_der_x = st.slider("Köhler Derecha (X)", 0, w, int(w * 0.47))

        with st.expander("🔵 Centros de Rotación (COR) de la Cabeza Femoral", expanded=True):
            cor_izq_x = st.slider("COR Izquierdo (X)", 0, w, int(w * 0.65))
            cor_izq_y = st.slider("COR Izquierdo (Y)", 0, h, int(h * 0.53))
            cor_der_x = st.slider("COR Derecho (X)", 0, w, int(w * 0.35))
            cor_der_y = st.slider("COR Derecho (Y)", 0, h, int(h * 0.53))

        with st.expander("🟡 Fémur Proximal (Trocánteres y Eje Anatómico)", expanded=True):
            st.markdown("**Trocánter Mayor (PTM)**")
            ptm_izq_y = st.slider("PTM Izquierda (Y)", 0, h, int(h * 0.60))
            ptm_der_y = st.slider("PTM Derecha (Y)", 0, h, int(h * 0.62))
            
            st.markdown("**Trocánter Menor (PTm)**")
            ptm_menor_izq_y = st.slider("PTm Menor Izquierda (Y)", 0, h, int(h * 0.72))
            ptm_menor_der_y = st.slider("PTm Menor Derecha (Y)", 0, h, int(h * 0.74))
            
            st.markdown("**Eje Anatómico Femoral (EAF)**")
            eje_izq_x = st.slider("Eje Femoral Izquierdo (X)", 0, w, int(w * 0.67))
            eje_der_x = st.slider("Eje Femoral Derecho (X)", 0, w, int(w * 0.33))

    # --- CÁLCULOS BIOMECÁNICOS AVANZADOS ---
    # 1. Línea Inter-lagrimal (LIL) como referencia "Cero" horizontal
    y_lil = int((t_izq_y + t_der_y) / 2)
    
    # 2. Dismetrías (LLD)
    lld_mayor = abs(ptm_der_y - ptm_izq_y) / px_por_mm
    lld_menor = abs(ptm_menor_der_y - ptm_menor_izq_y) / px_por_mm
    
    # 3. Offsets Femorales (Distancia horizontal desde el COR al Eje Anatómico)
    offset_fem_izq = abs(cor_izq_x - eje_izq_x) / px_por_mm
    offset_fem_der = abs(cor_der_x - eje_der_x) / px_por_mm
    
    # 4. Offsets Acetabulares (Distancia horizontal desde la Lágrima al COR)
    offset_ace_izq = abs(cor_izq_x - t_izq_x) / px_por_mm
    offset_ace_der = abs(cor_der_x - t_der_x) / px_por_mm

    # --- GENERACIÓN DEL GRÁFICO (OVERLAY MULTICOLOR) ---
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.imshow(img_np)
    
    # Línea Inter-lagrimal (Roja)
    ax.axhline(y=y_lil, color='red', linestyle='-', linewidth=2.5, label="Línea Inter-lagrimal (LIL)")
    
    # Líneas de Köhler Bilaterales (Líneas verticales discontinuas Cian)
    ax.axvline(x=kohler_izq_x, color='cyan', linestyle=':', linewidth=2, label="Línea de Köhler")
    ax.axvline(x=kohler_der_x, color='cyan', linestyle=':')
    
    # Ejes Anatómicos Femorales (Amarillo)
    ax.axvline(x=eje_izq_x, color='yellow', linestyle='--', linewidth=1.5, label="Eje Anatómico Femoral")
    ax.axvline(x=eje_der_x, color='yellow', linestyle='--', linewidth=1.5)
    
    # Puntos e indicadores de referencia
    ax.scatter([t_izq_x, t_der_x], [t_izq_y, t_der_y], color='red', s=120, zorder=5)
    ax.scatter([cor_izq_x, cor_der_x], [cor_izq_y, cor_der_y], color='blue', s=140, zorder=5, label="COR Cabeza Femoral")
    
    # Líneas horizontales indicadoras para Trocánteres Mayores y Menores hacia los ejes
    ax.hlines(y=ptm_izq_y, xmin=min(eje_izq_x, cor_izq_x), xmax=max(eje_izq_x, cor_izq_x), color='magenta', linestyle='-', linewidth=2, label="Offset/Trocánteres")
    ax.hlines(y=ptm_der_y, xmin=min(eje_der_x, cor_der_x), xmax=max(eje_der_x, cor_der_x), color='magenta', linestyle='-', linewidth=2)
    ax.scatter([eje_izq_x, eje_der_x], [ptm_menor_izq_y, ptm_menor_der_y], color='orange', s=100, marker='^', zorder=5, label="Trocánter Menor")
    
    ax.axis('off')
    ax.legend(loc='upper right', fontsize='small')

    with col_img:
        st.pyplot(fig)

    # --- PANEL DE RESULTADOS QUIRÚRGICOS ---
    st.markdown("---")
    st.subheader("📋 REPORTE CLÍNICO DE PLANIFICACIÓN BIOMECÁNICA")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 📏 Control de Dismetría (LLD)")
        st.metric(label="Dismetría por Trocánter Mayor", value=f"{lld_mayor:.1f} mm", 
                  delta="Lado Derecho más bajo" if ptm_der_y > ptm_izq_y else "Lado Izquierdo más bajo")
        st.metric(label="Dismetría por Trocánter Menor", value=f"{lld_menor:.1f} mm", 
                  delta="Referencia para altura de corte de cuello")
        
    with c2:
        st.markdown("### 📐 Análisis de Offset")
        st.markdown(f"**Lado Derecho (Patológico en este análisis):**")
        st.write(f"* Offset Femoral: **{offset_fem_der:.1f} mm**")
        st.write(f"* Offset Acetabular: **{offset_ace_der:.1f} mm**")
        st.markdown(f"**Lado Izquierdo (Sano de referencia):**")
        st.write(f"* Offset Femoral: **{offset_fem_izq:.1f} mm**")
        st.write(f"* Offset Acetabular: **{offset_ace_izq:.1f} mm**")

    with c3:
        st.markdown("### ⚠️ Línea de Köhler y Techo")
        dist_cor_kohler_der = abs(cor_der_x - kohler_der_x) / px_por_mm
        st.write(f"Distancia COR a Línea de Köhler (Der): **{dist_cor_kohler_der:.1f} mm**")
        if (cor_der_x > kohler_der_x and lado_operar == "Derecho") or (cor_izq_x < kohler_izq_x and lado_operar == "Izquierdo"):
            st.error("🚨 Alerta: Riesgo de Protrusión Acetabular detectado en relación con la línea ilioisquiática.")
        else:
            st.success("✅ Relación de pared medial y línea ilioisquiática segura.")

    # Conclusión médica personalizada basada en reglas biomecánicas
    st.markdown("---")
    offset_deficit = abs(offset_fem_izq - offset_fem_der)
    st.subheader("🛠️ Objetivos de Reconstrucción Intraoperatoria")
    st.warning(f"""
    * **Objetivo de Longitud:** Se debe corregir la discrepancia de **{lld_menor:.1f} mm** tomando como guía la distancia desde el Trocánter Menor al centro del implante.
    * **Objetivo de Offset Femoral:** Existe un déficit de offset en el lado enfermo de **{offset_deficit:.1f} mm** en comparación con el lado sano. Para restaurar la tensión abductora sin alargar la extremidad, considere utilizar un **vástago de alto offset (High Offset)** o incrementar la lateralización mediante el ángulo del cuello del implante.
    """)
