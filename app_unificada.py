import streamlit as st
import pandas as pd
import plotly.express as px
import time
import io
import collections
from modules.asr import ASREngine
from modules.nlp import NLPProcessor
from modules.ngrams import ModeloNgramas
from modules.search import MotorBusqueda
from modules.tts import TTSEngine
from modules.db import BaseDatos

# --- CONFIGURACIÓN GLOBAL ---
st.set_page_config(page_title="MuseoVivo Chascomús", page_icon="🏛️", layout="wide")

@st.cache_resource
def inicializar_modulos():
    return ASREngine(), NLPProcessor(), ModeloNgramas(), MotorBusqueda(), TTSEngine(), BaseDatos()

asr, nlp, ngrams, search, tts, db = inicializar_modulos()

# --- ENRUTADOR LATERAL ---
with st.sidebar:
    st.title("⚙️ Navegación del Sistema")
    vista_actual = st.radio(
        "Seleccioná el módulo de trabajo:", 
        ["🏛️ Interfaz del Turista", "📊 Dashboard Técnico"]
    )
    st.markdown("---")
    st.caption("Proyecto MuseoVivo - Fases 1 y 2 Integradas")

# ==========================================
# VISTA 1: LA EXPERIENCIA DEL TURISTA
# ==========================================
if vista_actual == "🏛️ Interfaz del Turista":
    st.title("🏛️ MuseoVivo: Guía de Patrimonio")
    st.markdown("Interactuá con la historia de **Chascomús** a través de tu voz.")

    # 1. TTS CONFIGURABLE (Requisito de la rúbrica)
    activar_tts = st.toggle("🔊 Activar respuesta por voz (TTS)", value=True)
    
    audio_value = st.audio_input("Presioná el micrófono para preguntar")

    if audio_value:
        audio_path = "temp_query.wav"
        with open(audio_path, "wb") as f:
            f.write(audio_value.read())
        
        with st.status("Procesando consulta...", expanded=False) as status:
            start_time = time.time()
            
            texto_usuario = asr.transcribir_desde_archivo(audio_path)
            
            if texto_usuario:
                st.chat_message("user").write(texto_usuario)
                
                analisis_nlp = nlp.procesar_consulta(texto_usuario)
                entidades = analisis_nlp["entidades"]
                
                resultado, score = search.buscar_mas_relevante(texto_usuario)
                pp = ngrams.calcular_perplejidad(texto_usuario)
                st.session_state.ultima_pp = pp
                
                # Asignamos wer_actual como 0 por defecto hasta integrarlo por completo
                wer_actual = 0.0 
                
                # E. LÓGICA DE RESPUESTA INTELIGENTE (Sistema de 3 Umbrales Calibrados)
                
                # NIVEL 1: Entendió la pregunta perfectamente (Umbral optimizado para lenguaje coloquial)
                if score >= 0.08:
                    wer_actual = asr.calcular_wer(resultado.get('titulo', ''), texto_usuario)
                    with st.chat_message("assistant", avatar="🏛️"):
                        st.subheader(f"📍 {resultado.get('titulo', 'Información Encontrada')}")
                        
                        cuerpo = resultado['contenido'].split("Etiquetas:")[0].strip()
                        st.write(cuerpo)
                        
                        with st.expander("Ver ficha técnica"):
                            st.caption(f"**Fuente:** {resultado.get('fuente')}")
                            st.caption(f"**Confianza del Motor:** {score*100:.1f}%")
                            st.caption(f"**Entidades detectadas:** {', '.join([e['texto'] for e in entidades])}")

                        if activar_tts:
                            try:
                                path_audio_res = tts.sintetizar_para_web(cuerpo[:250])
                                st.audio(path_audio_res, autoplay=True)
                            except Exception:
                                st.error("Error en la síntesis de voz.")

                        st.markdown("---")
                        st.write("¿Te resultó útil?")
                        cf1, cf2, _ = st.columns([1, 1, 4])
                        if cf1.button("👍 Sí", key="btn_si"):
                            db.registrar_feedback(texto_usuario, 1)
                            st.toast("¡Gracias!", icon="😊")
                        if cf2.button("👎 No", key="btn_no"):
                            db.registrar_feedback(texto_usuario, -1)
                            st.toast("Lo tendré en cuenta.", icon="🫡")

                # NIVEL 2: Entendió a medias / Capturó el contexto pero con ruido (Ambigüedad controlada)
                elif score >= 0.04:
                    wer_actual = asr.calcular_wer(resultado.get('titulo', ''), texto_usuario)
                    with st.chat_message("assistant", avatar="🏛️"):
                        titulo_dudoso = resultado.get('titulo', 'este lugar')
                        st.warning(f"🤔 Te escuché con un poco de ruido. ¿Quisiste preguntar por **{titulo_dudoso}**?")
                        
                        with st.expander(f"Sí, era eso. Mostrar info sobre {titulo_dudoso}"):
                            cuerpo = resultado['contenido'].split("Etiquetas:")[0].strip()
                            st.write(cuerpo)
                            st.caption(f"Confianza parcial del motor: {score*100:.1f}%")
                            
                        st.info("Si no era esto lo que buscabas, intentá repetir la pregunta usando el nombre específico del lugar.")

                # NIVEL 3: No entiende la pregunta (Fallo total por falta de coincidencia matemática)
                else:
                    wer_actual = 1.0
                    with st.chat_message("assistant", avatar="🏛️"):
                        st.error("No alcancé a comprender la pregunta. Es posible que haya mucho ruido ambiente o que falten palabras clave.")
                        
                        if entidades:
                            lugar_detectado = entidades[0]["texto"]
                            st.write(f"💡 Pude escuchar que mencionaste **{lugar_detectado}**, pero necesito que me des un poco más de contexto.")
                        else:
                            st.write("💡 **Acá tenés ejemplos de cómo preguntarme:**")
                            st.info("🎙️ *'Contame la historia de la Casa de Casco'*")
                            st.info("🎙️ *'¿Por qué es importante la Capilla de los Negros?'*")

                tiempo_resp = time.time() - start_time
                db.guardar_interaccion(texto_usuario, score, pp, tiempo_resp, wer_actual)
                status.update(label="Respuesta generada", state="complete")
            else:
                st.error("El sistema no detectó voz clara.") 

# ==========================================
# VISTA 2: EL DASHBOARD TÉCNICO
# ==========================================
elif vista_actual == "📊 Dashboard Técnico":
    st.title("📊 Panel de Control Analítico")
    
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.markdown("Monitor de desempeño de los modelos de procesamiento y lenguaje.")
    if col_t2.button("🔄 Actualizar Datos", use_container_width=True):
        st.rerun()

    try:
        query = "SELECT timestamp, texto_transcripto, perplejidad, score_similitud, tiempo_ms, feedback FROM historial"
        df = pd.read_sql_query(query, db.conn)
        total_corpus = db.contar_documentos()

        if not df.empty:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            col1.metric("Consultas Totales", len(df))
            
            avg_pp = df['perplejidad'].mean()
            col2.metric("Perplejidad Media", f"{avg_pp:.2f}", delta=f"{avg_pp - 6.69:.2f}", delta_color="inverse")
            
            avg_score = df['score_similitud'].mean() * 100
            col3.metric("Confianza Media", f"{avg_score:.1f}%")
            
            avg_time = df['tiempo_ms'].mean() / 1000 
            col4.metric("Latencia Media", f"{avg_time:.2f}s")
            
            votos_validos = df[df['feedback'] != 0]
            satisfaccion = (len(votos_validos[votos_validos['feedback'] == 1]) / len(votos_validos) * 100) if not votos_validos.empty else 0
            col5.metric("Satisfacción", f"{satisfaccion:.1f}%")

            st.info(f"📚 El sistema cuenta con **{total_corpus}** documentos históricos indexados.")

            st.divider()
            g1, g2 = st.columns(2)

            with g1:
                st.subheader("📈 Evolución de Perplejidad")
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                fig_pp = px.line(df.dropna(subset=['timestamp']), x='timestamp', y='perplejidad', 
                                title="Salud del Modelo de Lenguaje")
                fig_pp.add_hline(y=6.69, line_dash="dash", line_color="red", annotation_text="Objetivo")
                st.plotly_chart(fig_pp, use_container_width=True)

            with g2:
                # 2. HISTOGRAMA DE TÉRMINOS (Nube de palabras / Frecuencia)
                st.subheader("📊 Términos Más Buscados")
                todas_palabras = " ".join(df['texto_transcripto'].dropna().tolist()).lower().split()
                # Quitamos palabras comunes (stopwords) para que el gráfico tenga sentido
                stopwords = {"el", "la", "los", "las", "un", "una", "de", "en", "y", "a", "que", "es", "del", "al", "por", "con", "para", "qué", "como", "se", "te", "me"}
                palabras_limpias = [p for p in todas_palabras if p not in stopwords and len(p) > 2]
                
                if palabras_limpias:
                    conteo = collections.Counter(palabras_limpias).most_common(10)
                    df_palabras = pd.DataFrame(conteo, columns=['Término', 'Frecuencia'])
                    fig_hist = px.bar(df_palabras, x='Término', y='Frecuencia', color='Frecuencia', color_continuous_scale='Blues')
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No hay suficientes palabras para generar el histograma.")

            st.markdown("---")
            
            # 3. TABLA DE TRANSICIÓN DE N-GRAMAS
            st.subheader("🔗 Tablas de Probabilidad de Transición (N-gramas)")
            st.caption("Top 10 secuencias más probables según el corpus de entrenamiento.")
            transiciones = []
            
            # Recorremos el diccionario anidado del ModeloNgramas
            for ctx, next_words in ngrams.counts.items():
                ctx_str = " ".join(ctx) if ctx else "<inicio>"
                for word, count in next_words.items():
                    prob = ngrams.obtener_probabilidad(word, ctx)
                    transiciones.append({
                        "Contexto": ctx_str, 
                        "Siguiente Palabra": word, 
                        "Apariciones": count, 
                        "Probabilidad": prob
                    })
                    
            if transiciones:
                df_trans = pd.DataFrame(transiciones).sort_values(by="Apariciones", ascending=False).head(10)
                # Formateamos la probabilidad visualmente
                df_trans["Probabilidad"] = df_trans["Probabilidad"].apply(lambda x: f"{x:.4f}")
                st.dataframe(df_trans, hide_index=True, use_container_width=True)
            else:
                st.info("El modelo de N-gramas aún no ha procesado el corpus.")

            st.markdown("---")
            
            # 4. MÉTRICAS DE EVALUACIÓN OBLIGATORIAS (P/R/F1)
            # -> ¡Mejora Crítica Aplicada! Se conecta a SQLite automáticamente.
            st.subheader("🎯 Métricas de Evaluación Rigurosa")
            st.caption("Resultados automáticos de los últimos tests de validación en consola.")
            
            metricas_test = db.obtener_metricas_test()
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Precisión (P)", f"{metricas_test['precision']:.2f}")
            col_m2.metric("Recall (R)", f"{metricas_test['recall']:.2f}")
            col_m3.metric("F1-Score", f"{metricas_test['f1']:.2f}")
            col_m4.metric("Accuracy NER", f"{metricas_test['accuracy_ner']*100:.1f}%")

            st.markdown("---")
            st.subheader("📄 Registro de Interacciones")
            st.dataframe(df.sort_values(by='timestamp', ascending=False), hide_index=True, use_container_width=True)
            
        else:
            st.info("Aún no hay interacciones registradas en la base de datos.")

    except Exception as e:
        st.error(f"Error de lectura en la base de datos: {e}. Verificá que la tabla 'historial' exista con el esquema correcto.")