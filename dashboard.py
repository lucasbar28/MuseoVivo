import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db import BaseDatos
from streamlit_autorefresh import st_autorefresh

# Configuración de página
st.set_page_config(page_title="MuseoVivo: Dashboard", layout="wide", page_icon="📊")

# Auto-refresh cada 30 segundos
st_autorefresh(interval=30000, key="datarefresh")

def cargar_datos():
    db = BaseDatos()
    # Traemos también el título (o el ID) para saber qué se consultó
    query = "SELECT timestamp, texto_transcripto, perplejidad, score_similitud, tiempo_ms, feedback FROM historial"
    df = pd.read_sql_query(query, db.conn)
    
    # Traemos el conteo de documentos del corpus
    total_corpus = db.contar_documentos()
    db.cerrar()
    return df, total_corpus

st.title("📊 Panel de Control MuseoVivo Chascomús")

try:
    df, total_corpus = cargar_datos()

    if not df.empty:
        # --- FILA 1: KPIs Principales ---
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # 1. Total Consultas
        total_consultas = len(df)
        col1.metric("Consultas Totales", total_consultas)

        # 2. Perplejidad Media (Comparada con el objetivo de 6.69)
        avg_pp = df['perplejidad'].mean()
        col2.metric("Perplejidad Media", f"{avg_pp:.2f}", 
                  delta=f"{avg_pp - 6.69:.2f}", delta_color="inverse")

        # 3. Confianza del Motor de Búsqueda
        avg_score = df['score_similitud'].mean() * 100
        col3.metric("Confianza Media", f"{avg_score:.1f}%")

        # 4. Latencia (Tiempo de respuesta del ASR + Búsqueda)
        avg_time = df['tiempo_ms'].mean() / 1000 
        col4.metric("Latencia Media", f"{avg_time:.2f}s")

        # 5. Satisfacción Real (Excluyendo los "Sin Voto" para ser más precisos)
        votos_validos = df[df['feedback'] != 0]
        if not votos_validos.empty:
            votos_positivos = len(votos_validos[votos_validos['feedback'] == 1])
            satisfaccion = (votos_positivos / len(votos_validos)) * 100
        else:
            satisfaccion = 0
        col5.metric("Satisfacción", f"{satisfaccion:.1f}%")

        # --- FILA INTERMEDIA: Info del Corpus ---
        st.info(f"📚 Actualmente el sistema cuenta con **{total_corpus}** documentos históricos de Chascomús indexados.")

        # --- FILA 2: Gráficos ---
        st.divider()
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("📈 Evolución de Perplejidad")
            # Convertimos timestamp a datetime por si viene como texto
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig_pp = px.line(df, x='timestamp', y='perplejidad', 
                            title="Salud del Lenguaje (N-Grams)",
                            labels={'timestamp': 'Fecha/Hora', 'perplejidad': 'PP'})
            # Línea roja de referencia del modelo
            fig_pp.add_hline(y=6.69, line_dash="dash", line_color="red", annotation_text="Objetivo")
            st.plotly_chart(fig_pp, use_container_width=True)

        with g2:
            st.subheader("👍 Análisis de Feedback")
            feedback_counts = df['feedback'].replace({1: 'Útil', -1: 'No Útil', 0: 'Sin Voto'}).value_counts()
            fig_pie = px.pie(names=feedback_counts.index, 
                            values=feedback_counts.values, 
                            hole=0.4,
                            color=feedback_counts.index,
                            color_discrete_map={'Útil':'#2ecc71', 'No Útil':'#e74c3c', 'Sin Voto':'#95a5a6'})
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- FILA 3: Registro Detallado ---
        st.subheader("📄 Registro de Interacciones")
        # Estilizamos el dataframe para que sea más legible
        st.dataframe(
            df.sort_values(by='timestamp', ascending=False),
            column_config={
                "timestamp": "Fecha y Hora",
                "texto_transcripto": "Pregunta del Turista",
                "perplejidad": st.column_config.NumberColumn("PP", format="%.2f"),
                "score_similitud": st.column_config.ProgressColumn("Confianza", min_value=0, max_value=1),
                "tiempo_ms": "Latencia (ms)",
                "feedback": "Voto"
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info("Esperando primeras interacciones para generar métricas...")

except Exception as e:
    st.error(f"Error al cargar el Dashboard: {e}") 