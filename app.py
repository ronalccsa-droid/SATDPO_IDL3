import streamlit as st
import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# -----------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA (UI Corporativa)
# -----------------------------------------------------------
st.set_page_config(page_title="Gestión de Riesgos | SATDPO", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    .stMetric {background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    h1, h2, h3 {color: #2C3E50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
    .coso-box {background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;}
    .css-1v3fvcr {font-size: 1.2rem; font-weight: 600;} /* Mejora el texto de las pestañas */
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🛡️ SATDPO: Evaluación de Riesgo Operativo (Framework COSO)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7f8c8d;'>Motor Predictivo de Supervisión y Control Interno</p>", unsafe_allow_html=True)
st.markdown("---")

# -----------------------------------------------------------
import os

# -----------------------------------------------------------
# 2. CARGA DE MODELO Y DATOS (CON BUSCADOR AUTOMÁTICO)
# -----------------------------------------------------------
@st.cache_resource
def load_model_and_explainer():
    # El sistema buscará el modelo en todos estos lugares
    rutas_modelo = [
        'train.py/models/modelo_final_semaforo.pkl', # Donde está según tu foto
        'models/modelo_final_semaforo.pkl',          # Ruta estándar
        'modelo_final_semaforo.pkl'                  # En la raíz
    ]
    
    modelo = None
    for ruta in rutas_modelo:
        if os.path.exists(ruta):
            modelo = joblib.load(ruta)
            break # Si lo encuentra, deja de buscar
            
    if modelo is None:
        raise FileNotFoundError("⚠️ No encuentro el archivo 'modelo_final_semaforo.pkl'.")
        
    explainer = shap.Explainer(modelo)
    return modelo, explainer

def load_clean_data():
    # El sistema buscará el CSV en todos estos lugares
    rutas_csv = [
        'train.py/gold_dataset_ready.csv', # Donde está según tu foto
        'gold_dataset_ready.csv',          # Ruta estándar
        'data/processed/gold_dataset_ready.csv'
    ]
    
    ruta_correcta = None
    for ruta in rutas_csv:
        if os.path.exists(ruta):
            ruta_correcta = ruta
            break
            
    if ruta_correcta is None:
        raise FileNotFoundError("⚠️ No encuentro el archivo 'gold_dataset_ready.csv'.")
        
    df = pd.read_csv(ruta_correcta)
    
    # Limpieza de corchetes y anomalías
    df['asesor'] = df['asesor'].astype(str).str.replace(r"[\[\]'\"]", "", regex=True).str.strip()
    df = df[df['asesor'].str.lower() != 'chamo']
    return df

try:
    rf_model, explainer = load_model_and_explainer()
    df_gold = load_clean_data()
    modelo_cargado = True
except Exception as e:
    st.error(f"Falla en la carga de componentes: {e}")
    modelo_cargado = False
# -----------------------------------------------------------
# 3. PROCESAMIENTO GLOBAL (Para el Ranking)
# -----------------------------------------------------------
if modelo_cargado:
    # Evaluamos a TODOS los asesores en segundo plano para el Ranking
    features_cols = ['Horas_conexion_num', 'Calidad_num', 'NPS_num', 'TIP_num', 'TMO_num']
    df_evaluacion = df_gold.copy()
    df_evaluacion['Score_Predictivo'] = rf_model.predict(df_evaluacion[features_cols])
    
    # -----------------------------------------------------------
    # 4. PANEL LATERAL: SELECCIÓN Y SIMULACIÓN
    # -----------------------------------------------------------
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/10061/10061838.png", width=80)
    st.sidebar.header("📋 Sujeto de Control")

    lista_asesores = sorted(df_gold['asesor'].unique().tolist())
    asesor_seleccionado = st.sidebar.selectbox("Seleccionar colaborador a auditar:", lista_asesores)
    datos_asesor = df_gold[df_gold['asesor'] == asesor_seleccionado].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Simulador (What-If)")
    st.sidebar.markdown("Modifique para proyectar metas:")

    horas_conexion = st.sidebar.slider("Disponibilidad (%)", 0.0, 100.0, float(datos_asesor['Horas_conexion_num']))
    calidad = st.sidebar.slider("Calidad de Proceso (%)", 0.0, 100.0, float(datos_asesor['Calidad_num']))
    nps = st.sidebar.slider("Satisfacción (NPS %)", 0.0, 100.0, float(datos_asesor['NPS_num']))
    tipificacion = st.sidebar.slider("Cumplimiento (TIP %)", 0.0, 100.0, float(datos_asesor['TIP_num']))
    tmo = st.sidebar.number_input("Eficiencia (TMO Min)", min_value=1.0, max_value=20.0, value=float(datos_asesor['TMO_num']), step=0.1)

    input_data = pd.DataFrame([[horas_conexion, calidad, nps, tipificacion, tmo]], columns=features_cols)
    score_predicho = rf_model.predict(input_data)[0]

    # -----------------------------------------------------------
    # 5. CREACIÓN DE LAS PESTAÑAS (TABS)
    # -----------------------------------------------------------
    tab1, tab2 = st.tabs(["🎯 Auditoría Individual", "🏆 Ranking y Visión Global"])

    # ==========================================
    # PESTAÑA 1: AUDITORÍA INDIVIDUAL (SEMAFORO)
    # ==========================================
    with tab1:
        st.markdown("### 📊 Indicadores Clave de Desempeño (KPIs) Base")
        met1, met2, met3, met4, met5 = st.columns(5)
        met1.metric("Cumplimiento Normativo (TIP)", f"{tipificacion}%")
        met2.metric("Calidad del Proceso", f"{calidad}%")
        met3.metric("Satisfacción (NPS)", f"{nps}%")
        met4.metric("Disponibilidad", f"{horas_conexion}%")
        met5.metric("Eficiencia (TMO)", f"{tmo} min")
        
        st.markdown("<br>", unsafe_allow_html=True)

        if score_predicho >= 90:
            nivel_riesgo, color_medidor, coso_diag = "BAJO RIESGO", "#27ae60", "Riesgo residual dentro del Apetito de Riesgo."
        elif score_predicho >= 70:
            nivel_riesgo, color_medidor, coso_diag = "RIESGO MODERADO", "#f39c12", "Riesgo latente de desviación operativa."
        else:
            nivel_riesgo, color_medidor, coso_diag = "RIESGO CRÍTICO", "#c0392b", "Excede la tolerancia al riesgo (Plan PIP requerido)."

        col1, col2 = st.columns([1, 1.2])

        with col1:
            st.markdown("<div class='coso-box'>", unsafe_allow_html=True)
            st.subheader(f"Proyección: {asesor_seleccionado}")
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = score_predicho, domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"{nivel_riesgo}", 'font': {'size': 20, 'color': color_medidor}},
                number = {'font': {'size': 40}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 2},
                    'bar': {'color': "#34495e", 'thickness': 0.25},
                    'steps': [
                        {'range': [0, 70], 'color': "#fadbd8"},
                        {'range': [70, 90], 'color': "#fdebd0"},
                        {'range': [90, 100], 'color': "#d5f5e3"}
                    ],
                    'threshold': {'line': {'color': color_medidor, 'width': 6}, 'thickness': 0.8, 'value': score_predicho}
                }
            ))
            fig_gauge.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.info(f"**Diagnóstico COSO:** {coso_diag}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='coso-box'>", unsafe_allow_html=True)
            st.subheader("🧠 Hallazgos de Control (IA Explicativa)")
            
            shap_values = explainer(input_data)
            nombres_negocio = ["Disponibilidad", "Calidad de Proceso", "Satisfacción (NPS)", "Normativo CRM", "Eficiencia (TMO)"]
            shap_values.feature_names = nombres_negocio
            
            plt.clf() 
            fig_shap, ax = plt.subplots(figsize=(6, 3.2))
            shap.plots.waterfall(shap_values[0], show=False)
            plt.tight_layout()
            st.pyplot(fig_shap)
            plt.clf()

            impactos = shap_values.values[0]
            for i, nombre in enumerate(nombres_negocio):
                if impactos[i] <= -2.0:
                    st.error(f"⚠️ **Vulnerabilidad:** '{nombre}' incrementa el riesgo.")
                elif impactos[i] >= 2.0:
                    st.success(f"✅ **Control Efectivo:** '{nombre}' mitiga riesgos.")
            st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # PESTAÑA 2: RANKING Y VISIÓN GLOBAL
    # ==========================================
    with tab2:
        st.markdown("### 🏆 Tablero de Mando General")
        st.markdown("El modelo de Inteligencia Artificial ha evaluado a todos los asesores en la base de datos para identificar el talento clave y los focos de riesgo.")
        
        # Ordenar a los asesores
        df_ranking = df_evaluacion.sort_values(by='Score_Predictivo', ascending=False)
        top_5 = df_ranking.head(5)[['asesor', 'Score_Predictivo']]
        bottom_5 = df_ranking.tail(5).sort_values(by='Score_Predictivo', ascending=True)[['asesor', 'Score_Predictivo']]

        col_top, col_bottom = st.columns(2)

        with col_top:
            st.success("🌟 TOP 5: Mejor Desempeño Operativo")
            fig_top = px.bar(top_5, x='Score_Predictivo', y='asesor', orientation='h', 
                             color_discrete_sequence=['#27ae60'], text_auto='.2f')
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, height=300, xaxis_title="Score", yaxis_title="")
            st.plotly_chart(fig_top, use_container_width=True)

        with col_bottom:
            st.error("🚨 BOTTOM 5: Riesgo Operativo Crítico")
            fig_bottom = px.bar(bottom_5, x='Score_Predictivo', y='asesor', orientation='h', 
                                color_discrete_sequence=['#c0392b'], text_auto='.2f')
            fig_bottom.update_layout(yaxis={'categoryorder':'total descending'}, height=300, xaxis_title="Score", yaxis_title="")
            st.plotly_chart(fig_bottom, use_container_width=True)
            
        st.markdown("---")
        st.markdown("#### 📂 Directorio Completo de Evaluaciones")
        st.dataframe(df_ranking[['asesor', 'Score_Predictivo', 'Calidad_num', 'NPS_num', 'TMO_num']], use_container_width=True)