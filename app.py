"""
SATDPO — Sistema de Alerta Temprana de Desempeño de Personal Operativo
Streamlit app.py  ·  Motor predictivo con Random Forest + COSO ERM + SHAP

Estructurado para trabajar con:
  - modelo_final_semaforo.pkl  (RandomForestRegressor, 5 features)
  - gold_dataset_ready.csv     (42,595 registros, 59 asesores)
"""

import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

# ════════════════════════════════════════════════════════════════════════════
# 1.  CONFIGURACIÓN DE LA PÁGINA
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SATDPO — Gestión de Riesgos COSO ERM",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS corporativo COSO ERM
st.markdown("""
<style>
.main {background-color: #f4f6f9;}
.stMetric {background:#fff;padding:14px;border-radius:8px;border-left:4px solid #1E3A8A;
           box-shadow:0 2px 4px rgba(0,0,0,0.05);}
h1, h2, h3 {color:#1E3A5F; font-family:'Segoe UI', Tahoma, sans-serif;}
.coso-box {background:#fff;padding:18px;border-radius:10px;
           box-shadow:0 2px 6px rgba(0,0,0,0.08);margin-bottom:16px;}
.coso-banner {background:linear-gradient(90deg,#1E3A5F,#2D5F8A);
              color:#fff;padding:18px 24px;border-radius:10px;margin-bottom:18px;}
.coso-banner h1 {color:#fff;margin:0;font-size:22px;}
.coso-banner p  {color:#bfdbfe;margin:4px 0 0;font-size:13px;}
.risk-badge {display:inline-block;padding:6px 14px;border-radius:20px;
             font-size:13px;font-weight:700;}
.badge-rojo  {background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;}
.badge-ambar {background:#fef3c7;color:#92400e;border:1px solid #fcd34d;}
.badge-verde {background:#dcfce7;color:#166534;border:1px solid #86efac;}
</style>
""", unsafe_allow_html=True)

# Cabecera
st.markdown("""
<div class='coso-banner'>
  <h1>🛡️ SATDPO · Sistema de Alerta Temprana de Desempeño</h1>
  <p>Motor predictivo Random Forest · Framework COSO ERM · IA Explicable (SHAP)</p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 2.  CONSTANTES DEL MODELO
# ════════════════════════════════════════════════════════════════════════════
FEATURES = ['Horas_conexion_num', 'Calidad_num', 'NPS_num', 'TIP_num', 'TMO_num']

FEATURE_LABELS = {
    'Horas_conexion_num': 'Disponibilidad (Horas Cx %)',
    'Calidad_num':        'Calidad del Servicio (%)',
    'NPS_num':            'Satisfacción NPS (%)',
    'TIP_num':            'Tipificación CRM (%)',
    'TMO_num':            'Eficiencia TMO (min)',
}

# Umbrales operativos del semáforo (alineados a la distribución real de los datos)
TH_VERDE = 90   # score >= 90  → Bajo Riesgo
TH_AMBAR = 70   # score >= 70  → Riesgo Moderado
# score <  70  → Riesgo Crítico

COLOR_VERDE  = "#16a34a"
COLOR_AMBAR  = "#d97706"
COLOR_ROJO   = "#dc2626"
COLOR_NAVY   = "#1E3A5F"


def clasificar_riesgo(score: float):
    """Convierte score numérico → (nivel, color, diagnóstico COSO)."""
    if score >= TH_VERDE:
        return "BAJO RIESGO", COLOR_VERDE, "verde", "Riesgo residual dentro del apetito de riesgo definido por COSO ERM."
    elif score >= TH_AMBAR:
        return "RIESGO MODERADO", COLOR_AMBAR, "ambar", "Riesgo latente de desviación operativa. Aplicar plan de monitoreo focalizado."
    else:
        return "RIESGO CRÍTICO", COLOR_ROJO, "rojo", "Excede la tolerancia al riesgo. Plan de mejora individual (PIP) requerido."


# ════════════════════════════════════════════════════════════════════════════
# 3.  CARGA DE ARTEFACTOS (con búsqueda robusta de rutas)
# ════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="Cargando modelo Random Forest...")
def load_model():
    """Carga el modelo desde cualquier ruta razonable."""
    candidatos = [
        'modelo_final_semaforo.pkl',
        'models/modelo_final_semaforo.pkl',
        'data/modelo_final_semaforo.pkl',
        'artifacts/modelo_final_semaforo.pkl',
        Path(__file__).parent / 'modelo_final_semaforo.pkl' if '__file__' in globals() else None,
    ]
    for ruta in candidatos:
        if ruta and Path(ruta).exists():
            modelo = joblib.load(ruta)
            return modelo, str(ruta)
    raise FileNotFoundError(
        "No se encontró 'modelo_final_semaforo.pkl'. "
        "Colócalo en la raíz del proyecto o en una carpeta 'models/'."
    )


@st.cache_resource(show_spinner="Inicializando explainer SHAP...")
def load_shap_explainer(_modelo):
    """Construye TreeExplainer para el RandomForest (más rápido y exacto)."""
    import shap
    return shap.TreeExplainer(_modelo)


@st.cache_data(show_spinner="Cargando dataset Gold...")
def load_gold():
    """Carga gold_dataset_ready.csv y aplica limpieza defensiva."""
    candidatos = [
        'gold_dataset_ready.csv',
        'data/gold_dataset_ready.csv',
        'data/processed/gold_dataset_ready.csv',
        'gold/gold_dataset_ready.csv',
    ]
    for ruta in candidatos:
        if Path(ruta).exists():
            df = pd.read_csv(ruta)
            # Limpieza defensiva del campo asesor
            df['asesor'] = (df['asesor'].astype(str)
                            .str.replace(r"[\[\]'\"]", "", regex=True)
                            .str.strip())
            df = df[df['asesor'].str.lower() != 'nan']
            df = df[df['asesor'].str.len() > 0]
            return df, str(ruta)
    raise FileNotFoundError(
        "No se encontró 'gold_dataset_ready.csv'. "
        "Colócalo en la raíz del proyecto o en 'data/'."
    )


# ── Carga con manejo de errores ─────────────────────────────────────────────
try:
    rf_model, ruta_modelo = load_model()
    df_gold,  ruta_csv    = load_gold()
    explainer             = load_shap_explainer(rf_model)
    modelo_ok = True
except Exception as e:
    st.error(f"❌ Falla en la carga de componentes: {e}")
    st.info("**Estructura esperada:** modelo_final_semaforo.pkl + gold_dataset_ready.csv en la misma carpeta que app.py")
    modelo_ok = False
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# 4.  PROCESAMIENTO GLOBAL — predicciones y agregación
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def calcular_predicciones_globales(_df: pd.DataFrame) -> pd.DataFrame:
    """Predice el score para todo el dataset y agrega resúmenes por asesor."""
    df_pred = _df.copy()
    df_pred['Score_Predictivo'] = rf_model.predict(df_pred[FEATURES])
    df_pred['Nivel_Riesgo'] = df_pred['Score_Predictivo'].apply(
        lambda s: clasificar_riesgo(s)[0]
    )
    return df_pred


@st.cache_data(show_spinner=False)
def ranking_por_asesor(_df_pred: pd.DataFrame) -> pd.DataFrame:
    """Agrega por asesor (promedio) y aporta n° de registros y nivel global."""
    agg = (_df_pred.groupby('asesor')
                   .agg(Score_Promedio=('Score_Predictivo', 'mean'),
                        Registros=('Score_Predictivo', 'count'),
                        Calidad=('Calidad_num', 'mean'),
                        NPS=('NPS_num', 'mean'),
                        TMO=('TMO_num', 'mean'),
                        Horas_Cx=('Horas_conexion_num', 'mean'),
                        TIP=('TIP_num', 'mean'))
                   .reset_index())
    agg['Nivel_Riesgo'] = agg['Score_Promedio'].apply(lambda s: clasificar_riesgo(s)[0])
    return agg.round(2)


df_predicciones = calcular_predicciones_globales(df_gold)
df_ranking      = ranking_por_asesor(df_predicciones)


# ════════════════════════════════════════════════════════════════════════════
# 5.  PANEL LATERAL — selección, filtros y simulador what-if
# ════════════════════════════════════════════════════════════════════════════
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/10061/10061838.png", width=70)
st.sidebar.header("📋 Sujeto de Control")

lista_asesores = sorted(df_gold['asesor'].unique().tolist())
asesor_sel = st.sidebar.selectbox("Asesor a auditar:", lista_asesores)

# Filtros por período (si las columnas existen)
anios = sorted(df_gold['anio'].unique().tolist()) if 'anio' in df_gold.columns else []
meses = (df_gold['mes'].drop_duplicates().tolist() if 'mes' in df_gold.columns else [])
orden_mes = ['January','February','March','April','May','June',
             'July','August','September','October','November','December']
meses = sorted(meses, key=lambda m: orden_mes.index(m) if m in orden_mes else 99)

with st.sidebar.expander("🗓 Filtros de período", expanded=False):
    anio_sel = st.selectbox("Año:", ["Todos"] + anios, index=0) if anios else "Todos"
    mes_sel  = st.selectbox("Mes:",  ["Todos"] + meses, index=0) if meses else "Todos"

# Subset del asesor (con filtros aplicados)
df_asesor = df_gold[df_gold['asesor'] == asesor_sel].copy()
if anio_sel != "Todos":
    df_asesor = df_asesor[df_asesor['anio'] == anio_sel]
if mes_sel != "Todos":
    df_asesor = df_asesor[df_asesor['mes'] == mes_sel]

# Si no hay datos con los filtros, usar promedio global del asesor
if len(df_asesor) == 0:
    df_asesor = df_gold[df_gold['asesor'] == asesor_sel].copy()
    st.sidebar.warning("Sin datos para ese período; se usa el promedio histórico del asesor.")

# Valores base = promedio del subset (no iloc[0] arbitrario)
base = df_asesor[FEATURES].mean().to_dict()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Simulador (What-If)")
st.sidebar.markdown("*Ajusta los valores para proyectar metas.*")

horas_cx  = st.sidebar.slider("Disponibilidad (%)",          0.0, 100.0, float(base['Horas_conexion_num']), step=0.5)
calidad   = st.sidebar.slider("Calidad del Servicio (%)",     0.0, 100.0, float(base['Calidad_num']),        step=0.5)
nps       = st.sidebar.slider("Satisfacción NPS (%)",          0.0, 100.0, float(base['NPS_num']),            step=0.5)
tip       = st.sidebar.slider("Tipificación CRM (%)",          0.0, 100.0, float(base['TIP_num']),            step=0.5)
tmo       = st.sidebar.number_input("Eficiencia TMO (min)",    min_value=1.0, max_value=20.0,
                                    value=float(base['TMO_num']), step=0.1)

# DataFrame de entrada con orden correcto de features
X_input = pd.DataFrame([[horas_cx, calidad, nps, tip, tmo]], columns=FEATURES)
score_pred = float(rf_model.predict(X_input)[0])
nivel, color_nivel, clave_nivel, diag_coso = clasificar_riesgo(score_pred)

# Info técnica del sistema
with st.sidebar.expander("ℹ️ Información del modelo"):
    st.caption(f"**Algoritmo:** RandomForestRegressor")
    st.caption(f"**Árboles:** {rf_model.n_estimators}")
    st.caption(f"**Max depth:** {rf_model.max_depth}")
    st.caption(f"**Features:** {len(FEATURES)}")
    st.caption(f"**Registros gold:** {len(df_gold):,}")
    st.caption(f"**Asesores:** {df_gold['asesor'].nunique()}")


# ════════════════════════════════════════════════════════════════════════════
# 6.  CONTENIDO PRINCIPAL — pestañas
# ════════════════════════════════════════════════════════════════════════════
tab_audit, tab_ranking, tab_dist = st.tabs([
    "🎯 Auditoría Individual",
    "🏆 Ranking & Visión Global",
    "📊 Distribución de Riesgo"
])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — AUDITORÍA INDIVIDUAL
# ────────────────────────────────────────────────────────────────────────────
with tab_audit:
    st.markdown("### 📊 Indicadores Clave de Desempeño (KPIs)")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tipificación CRM",     f"{tip:.1f}%")
    c2.metric("Calidad del Servicio", f"{calidad:.1f}%")
    c3.metric("Satisfacción NPS",     f"{nps:.1f}%")
    c4.metric("Disponibilidad",       f"{horas_cx:.1f}%")
    c5.metric("Eficiencia TMO",       f"{tmo:.2f} min")

    st.markdown("<br>", unsafe_allow_html=True)

    col_g, col_s = st.columns([1, 1.2])

    # ── Medidor de riesgo (gauge) ──
    with col_g:
        st.markdown("<div class='coso-box'>", unsafe_allow_html=True)
        st.subheader(f"Proyección · {asesor_sel}")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score_pred,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': nivel, 'font': {'size': 20, 'color': color_nivel}},
            number={'font': {'size': 42}, 'suffix': "/100", 'valueformat': '.1f'},
            gauge={
                'axis': {'range': [50, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                'bar': {'color': "#34495e", 'thickness': 0.25},
                'steps': [
                    {'range': [50, TH_AMBAR], 'color': "#fadbd8"},
                    {'range': [TH_AMBAR, TH_VERDE], 'color': "#fdebd0"},
                    {'range': [TH_VERDE, 100], 'color': "#d5f5e3"},
                ],
                'threshold': {'line': {'color': color_nivel, 'width': 5},
                              'thickness': 0.85, 'value': score_pred},
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(
            f"<div class='risk-badge badge-{clave_nivel}'>{nivel}  ·  Score {score_pred:.2f}</div>",
            unsafe_allow_html=True,
        )
        st.info(f"**Diagnóstico COSO ERM:** {diag_coso}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Explicabilidad SHAP ──
    with col_s:
        st.markdown("<div class='coso-box'>", unsafe_allow_html=True)
        st.subheader("🧠 Hallazgos de Control (XAI · SHAP)")

        shap_values = explainer(X_input)
        nombres = [FEATURE_LABELS[f] for f in FEATURES]
        shap_values.feature_names = nombres

        plt.clf()
        fig_shap, ax = plt.subplots(figsize=(6, 3.4))
        import shap
        shap.plots.waterfall(shap_values[0], show=False)
        plt.tight_layout()
        st.pyplot(fig_shap, clear_figure=True)
        plt.clf()

        # Interpretación automática de los impactos
        impactos = shap_values.values[0]
        impactos_ord = sorted(
            zip(nombres, impactos), key=lambda x: abs(x[1]), reverse=True
        )

        st.markdown("**Análisis individual de variables:**")
        for nom, imp in impactos_ord:
            if imp <= -1.5:
                st.error(f"⚠️ `{nom}` **resta {abs(imp):.2f} pts** al score — vulnerabilidad clave.")
            elif imp >= 1.5:
                st.success(f"✅ `{nom}` **suma {imp:.2f} pts** al score — control efectivo.")
            elif abs(imp) >= 0.3:
                signo = "+" if imp >= 0 else ""
                st.caption(f"• `{nom}` aporta {signo}{imp:.2f} pts — impacto moderado.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Histórico del asesor (si hay datos por período) ──
    if 'anio' in df_gold.columns and 'mes' in df_gold.columns:
        st.markdown("### 📈 Evolución Histórica del Asesor")
        st.markdown("<div class='coso-box'>", unsafe_allow_html=True)

        df_hist = df_predicciones[df_predicciones['asesor'] == asesor_sel].copy()
        df_hist['mes_num'] = df_hist['mes'].apply(
            lambda m: orden_mes.index(m) + 1 if m in orden_mes else 0
        )
        df_hist['periodo'] = df_hist['anio'].astype(str) + '-' + df_hist['mes_num'].astype(str).str.zfill(2)
        df_evo = (df_hist.groupby('periodo')['Score_Predictivo']
                         .mean()
                         .reset_index()
                         .sort_values('periodo'))

        fig_evo = go.Figure()
        fig_evo.add_trace(go.Scatter(
            x=df_evo['periodo'], y=df_evo['Score_Predictivo'],
            mode='lines+markers', line=dict(color=COLOR_NAVY, width=2.5),
            marker=dict(size=7, color=COLOR_NAVY), name='Score predicho'
        ))
        fig_evo.add_hline(y=TH_VERDE, line_dash="dash", line_color=COLOR_VERDE,
                          annotation_text="Umbral Verde (90)", annotation_position="right")
        fig_evo.add_hline(y=TH_AMBAR, line_dash="dash", line_color=COLOR_ROJO,
                          annotation_text="Umbral Crítico (70)", annotation_position="right")
        fig_evo.update_layout(
            height=320, margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Período", yaxis_title="Score",
            yaxis=dict(range=[50, 100]),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_evo, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — RANKING Y VISIÓN GLOBAL
# ────────────────────────────────────────────────────────────────────────────
with tab_ranking:
    st.markdown("### 🏆 Tablero de Mando — Score Promedio por Asesor")
    st.markdown("Ranking agregado por asesor (promedio de todos los registros, no por evento individual).")

    # ── KPIs de cabecera ──
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total asesores", f"{len(df_ranking)}")
    k2.metric("Verde (≥ 90)",   f"{(df_ranking['Nivel_Riesgo']=='BAJO RIESGO').sum()}")
    k3.metric("Ámbar (70-89)",  f"{(df_ranking['Nivel_Riesgo']=='RIESGO MODERADO').sum()}")
    k4.metric("Rojo (< 70)",    f"{(df_ranking['Nivel_Riesgo']=='RIESGO CRÍTICO').sum()}")

    st.markdown("<br>", unsafe_allow_html=True)

    rk = df_ranking.sort_values('Score_Promedio', ascending=False)
    top5 = rk.head(5)
    bot5 = rk.tail(5).sort_values('Score_Promedio', ascending=True)

    c_top, c_bot = st.columns(2)
    with c_top:
        st.success("🌟 TOP 5 — Mejor desempeño operativo")
        fig_top = px.bar(
            top5, x='Score_Promedio', y='asesor', orientation='h',
            color_discrete_sequence=[COLOR_VERDE], text_auto='.2f',
        )
        fig_top.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=300, xaxis_title="Score promedio", yaxis_title="",
            xaxis=dict(range=[60, 100]),
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with c_bot:
        st.error("🚨 BOTTOM 5 — Riesgo operativo crítico")
        fig_bot = px.bar(
            bot5, x='Score_Promedio', y='asesor', orientation='h',
            color_discrete_sequence=[COLOR_ROJO], text_auto='.2f',
        )
        fig_bot.update_layout(
            yaxis={'categoryorder': 'total descending'},
            height=300, xaxis_title="Score promedio", yaxis_title="",
            xaxis=dict(range=[60, 100]),
        )
        st.plotly_chart(fig_bot, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📂 Directorio completo de evaluaciones")

    # Buscador en el directorio
    busq = st.text_input("🔍 Buscar asesor:", placeholder="Escribe parte del nombre...")
    tabla = df_ranking.copy()
    if busq:
        tabla = tabla[tabla['asesor'].str.contains(busq, case=False, na=False)]

    st.dataframe(
        tabla[['asesor', 'Score_Promedio', 'Nivel_Riesgo', 'Registros',
               'Calidad', 'NPS', 'TMO', 'Horas_Cx', 'TIP']]
            .sort_values('Score_Promedio', ascending=False)
            .reset_index(drop=True),
        use_container_width=True, height=420,
    )

    # Descarga
    csv_data = df_ranking.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "⬇️ Descargar ranking completo (CSV)",
        data=csv_data, file_name="satdpo_ranking_asesores.csv", mime="text/csv",
    )


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — DISTRIBUCIÓN DE RIESGO E IMPORTANCIA GLOBAL
# ────────────────────────────────────────────────────────────────────────────
with tab_dist:
    st.markdown("### 📊 Distribución del Score Predictivo")

    fig_hist = px.histogram(
        df_predicciones, x='Score_Predictivo', nbins=40,
        color_discrete_sequence=[COLOR_NAVY],
    )
    fig_hist.add_vline(x=TH_VERDE, line_dash="dash", line_color=COLOR_VERDE,
                       annotation_text="Verde (≥90)", annotation_position="top right")
    fig_hist.add_vline(x=TH_AMBAR, line_dash="dash", line_color=COLOR_ROJO,
                       annotation_text="Crítico (<70)", annotation_position="top left")
    fig_hist.update_layout(
        height=340, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Score", yaxis_title="Frecuencia",
        bargap=0.05, plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # ── Importancia global de variables ──
    st.markdown("### 🌲 Importancia Global de Variables (Feature Importance)")
    importancias = pd.DataFrame({
        'Variable':   [FEATURE_LABELS[f] for f in FEATURES],
        'Importancia': rf_model.feature_importances_,
    }).sort_values('Importancia', ascending=True)

    fig_imp = px.bar(
        importancias, x='Importancia', y='Variable', orientation='h',
        color='Importancia', color_continuous_scale=[[0, '#cbd5e1'], [1, COLOR_NAVY]],
        text=importancias['Importancia'].apply(lambda v: f"{v*100:.1f}%"),
    )
    fig_imp.update_layout(
        height=320, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Importancia relativa", yaxis_title="",
        coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)",
    )
    fig_imp.update_traces(textposition='outside')
    st.plotly_chart(fig_imp, use_container_width=True)

    # ── Distribución por nivel de riesgo ──
    st.markdown("### 🚦 Distribución por Nivel de Riesgo")
    counts = (df_ranking['Nivel_Riesgo']
              .value_counts()
              .reindex(['BAJO RIESGO', 'RIESGO MODERADO', 'RIESGO CRÍTICO'], fill_value=0)
              .reset_index())
    counts.columns = ['Nivel', 'Cantidad']

    fig_pie = px.pie(
        counts, names='Nivel', values='Cantidad',
        color='Nivel',
        color_discrete_map={
            'BAJO RIESGO':    COLOR_VERDE,
            'RIESGO MODERADO': COLOR_AMBAR,
            'RIESGO CRÍTICO':  COLOR_ROJO,
        },
        hole=0.4,
    )
    fig_pie.update_traces(textposition='outside', textinfo='label+percent+value')
    fig_pie.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption(
    f"📂 Modelo: `{os.path.basename(ruta_modelo)}`  ·  "
    f"📊 Dataset: `{os.path.basename(ruta_csv)}`  ·  "
    f"🛡️ Framework: COSO ERM 2017  ·  "
    f"🧠 XAI: SHAP TreeExplainer"
)
