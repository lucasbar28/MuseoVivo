import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from modules.db import BaseDatos
from streamlit_autorefresh import st_autorefresh # Necesitaremos instalar esto

# Configuración de página
st.set_page_config(page_title="MuseoVivo: Dashboard", layout="wide")

# Auto-refresh cada 30 segundos para no tocar el F5
st_autorefresh(interval=30000, key="datarefresh")

def cargar_datos():
    db = BaseDatos()
    # Agregamos la columna feedback a la consulta
    query = "SELECT timestamp, texto_transcripto, perplejidad, score_similitud, tiempo_ms, feedback FROM historial"
    df = pd.read_sql_query(query, db.conn)
    db.cerrar()
    return df

st.title("📊 Panel de Control MuseoVivo Chascomús")

try:
    df = cargar_datos()

    if not df.empty:
        # --- FILA 1: KPIs Principales ---
        col1, col2, col3, col4, col5 = st.columns(5)
        
        avg_pp = df['perplejidad'].mean()
        avg_score = df['score_similitud'].mean() * 100
        avg_time = df['tiempo_ms'].mean() / 1000 # Convertimos a segundos para que sea legible
        total_consultas = len(df)
        
        # Cálculo de Satisfacción (Votos positivos vs totales)
        votos_positivos = len(df[df['feedback'] == 1])
        satisfaccion = (votos_positivos / total_consultas) * 100 if total_consultas > 0 else 0

        col1.metric("Consultas", total_consultas)
        col2.metric("Perplejidad", f"{avg_pp:.2f}", delta=f"{avg_pp - 6.69:.2f}", delta_color="inverse")
        col3.metric("Confianza", f"{avg_score:.1f}%")
        col4.metric("Latencia Media", f"{avg_time:.2f}s")
        col5.metric("Satisfacción", f"{satisfaccion:.1f}%")

        # --- FILA 2: Gráficos ---
        st.divider()
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("📈 Evolución de Perplejidad")
            fig_pp = px.line(df, x='timestamp', y='perplejidad', title="Salud del Lenguaje")
            fig_pp.add_hline(y=6.69, line_dash="dash", line_color="red")
            st.plotly_chart(fig_pp, use_container_width=True)

        with g2:
            st.subheader("👍 Análisis de Feedback")
            # Un gráfico de torta o barras para ver votos
            feedback_counts = df['feedback'].replace({1: 'Útil', -1: 'No Útil', 0: 'Sin Voto'}).value_counts()
            fig_pie = px.pie(names=feedback_counts.index, values=feedback_counts.values, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📄 Registro de Interacciones")
        st.dataframe(df.sort_values(by='timestamp', ascending=False), use_container_width=True)

    else:
        st.info("Esperando primeras interacciones...")

except Exception as e:
    st.error(f"Error: {e}") 