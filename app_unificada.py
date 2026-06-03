import streamlit as st
import pandas as pd
import plotly.express as px
import time
import io
import os
import collections
import random
from modules.asr import ASREngine
from modules.nlp import NLPProcessor
from modules.ngrams import ModeloNgramas
from modules.search import MotorBusqueda
from modules.tts import TTSEngine
from modules.db import BaseDatos
from modules.geo import GeoEngine

# Librerías para rendering de mapas y captura de GPS del navegador
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# --- CONFIGURACIÓN GLOBAL ---
st.set_page_config(page_title="MuseoVivo Chascomús", page_icon="🏛️", layout="wide")

@st.cache_resource
def inicializar_modulos():
    return ASREngine(), NLPProcessor(), ModeloNgramas(), MotorBusqueda(), TTSEngine(), BaseDatos(), GeoEngine()

asr, nlp, ngrams, search, tts, db, geo = inicializar_modulos()

# --- CONTROL DE ESTADOS CRÍTICOS (Persistencia Absoluta) ---
if "respuesta_lista" not in st.session_state:
    st.session_state["respuesta_lista"] = None
if "ultima_pregunta_guardada" not in st.session_state:
    st.session_state["ultima_pregunta_guardada"] = None
if "id_interaccion_actual" not in st.session_state:
    st.session_state["id_interaccion_actual"] = None
if "interaccion_id_actual" not in st.session_state:
    st.session_state["interaccion_id_actual"] = 0
if "ultimo_audio_id" not in st.session_state:
    st.session_state["ultimo_audio_id"] = None

# --- ENRUTADOR LATERAL ---
with st.sidebar:
    st.title("⚙️ Navegación del Sistema")
    vista_actual = st.radio(
        "Seleccioná el módulo de trabajo:", 
        ["🏛️ Interfaz del Turista", "📊 Dashboard Técnico"]
    )
    st.markdown("---")
    
    # Interruptor visual para simular la posición en la defensa de forma profesional
    modo_simulacion = st.toggle("🕹️ Activar Simulación GPS (Plaza Independencia)", value=False)
    
    st.markdown("---")
    st.caption("Proyecto MuseoVivo - Fases 1 y 2 Integradas")

# ==========================================
# VISTA 1: LA EXPERIENCIA DEL TURISTA
# ==========================================
if vista_actual == "🏛️ Interfaz del Turista":
    st.title("🏛️ MuseoVivo: Guía de Patrimonio")
    st.markdown("Interactuá con la historia de **Chascomús** a través de tu voz.")

    # --- 1. TOGGLE DE TTS ---
    activar_tts = st.toggle("🔊 Activar respuesta por voz (TTS)", value=True)

    st.markdown("---")

    # --- 2. BLOQUE DE GEOLOCALIZACIÓN ---
    lat_usuario, lng_usuario = None, None

    if modo_simulacion:
        lat_usuario = -35.57884215682103
        lng_usuario = -58.01312048592014
    else:
        coordenadas_gps = get_geolocation()
        try:
            if coordenadas_gps and isinstance(coordenadas_gps, dict):
                coords = coordenadas_gps.get("coords", {})
                lat_raw = coords.get("latitude")
                lng_raw = coords.get("longitude")
                if lat_raw is not None and lng_raw is not None:
                    lat_usuario = float(lat_raw)
                    lng_usuario = float(lng_raw)
                    if not (-55.0 <= lat_usuario <= -21.0 and -73.0 <= lng_usuario <= -53.0):
                        lat_usuario, lng_usuario = None, None
        except (TypeError, ValueError, KeyError):
            lat_usuario, lng_usuario = None, None

    # Radar de Proximidad Turística
    with st.container(border=True):
        st.markdown("### 📍 Mi Radar Chascomús")
        
        if lat_usuario is not None and lng_usuario is not None:
            if modo_simulacion:
                st.caption("🕹️ Modo Simulación Activo: Posicionado en Plaza Independencia (Centro Histórico)")
            else:
                st.caption("🟢 Señal GPS detectada y sincronizada en tiempo real")
            
            col_geo1, col_geo2, col_geo3 = st.columns(3)

            if col_geo1.button("🏛️ Patrimonio Cercano", width='stretch'):
                archivo_id, datos, dist = geo.obtener_mas_cercano(lat_usuario, lng_usuario, tipo_filtro="Historico")
                if datos:
                    msg = f"A {dist*1000:.0f} metros tenés {datos['nombre']}."
                    st.success(f"🏛️ {msg}")
                    mapa_cercano = geo.generar_mapa_sitio(archivo_id)
                    if mapa_cercano:
                        st_folium(mapa_cercano, width=700, height=250, key="mapa_cercano_hist", returned_objects=[])
                    if activar_tts:
                        try: tts.sintetizar_para_web(msg)
                        except Exception: pass

            if col_geo2.button("🍔 Dónde Comer", width='stretch'):
                archivo_id, datos, dist = geo.obtener_mas_cercano(lat_usuario, lng_usuario, tipo_filtro="Gastronomia")
                if datos:
                    msg = f"A {dist*1000:.0f} metros podés visitar {datos['nombre']}."
                    st.success(f"🍺 {msg}")
                    mapa_cercano = geo.generar_mapa_sitio(archivo_id)
                    if mapa_cercano:
                        st_folium(mapa_cercano, width=700, height=250, key="mapa_cercano_gast", returned_objects=[])
                    if activar_tts:
                        try: tts.sintetizar_para_web(msg)
                        except Exception: pass
            
            if col_geo3.button("🗺️ Ver Mapa General", width='stretch'):
                st.info("Explorando todos los puntos de interés de la ciudad.")
                mapa_completo = geo.generar_mapa_general()
                if mapa_completo:
                    st_folium(mapa_completo, width=700, height=350, key="mapa_turista_global", returned_objects=[])
        else:
            st.info("💡 Habilitá los permisos de ubicación en tu navegador para desbloquear el radar turístico o activá la simulación lateral.")

    st.markdown("---")
    st.markdown("### 🎙️ Consultá al Asistente de Voz")

    audio_value = st.audio_input("Presioná el micrófono para preguntar")

    if audio_value is not None:
        audio_id = id(audio_value)
        if audio_id != st.session_state["ultimo_audio_id"]:
            st.session_state["ultimo_audio_id"] = audio_id
            
            audio_path = "temp_query.wav"
            with open(audio_path, "wb") as f:
                f.write(audio_value.read())
            
            with st.status("Procesando consulta...", expanded=False) as status:
                start_time = time.time()
                texto_usuario = asr.transcribir_desde_archivo(audio_path)
                
                if texto_usuario:
                    st.session_state["ultima_pregunta_guardada"] = texto_usuario
                    st.session_state["interaccion_id_actual"] += 1
                    
                    analisis_nlp = nlp.procesar_consulta(texto_usuario)
                    entidades = analisis_nlp["entidades"]
                    texto_busqueda = nlp.optimizar_consulta_tfidf(analisis_nlp)
                    resultado, score = search.buscar_mas_relevante(texto_busqueda)
                    pp = ngrams.calcular_perplejidad(texto_usuario)
                    wer_actual = 0.0

                    categoria_geo = nlp.evaluar_intencion_geo_generica(texto_usuario)
                    
                    st.session_state["respuesta_lista"] = {
                        "texto_usuario": texto_usuario,
                        "categoria_geo": categoria_geo,
                        "entidades": entidades,
                        "resultado": resultado,
                        "score": score,
                        "pp": pp,
                        "start_time": start_time,
                        "wer_actual": wer_actual
                    }
                    
                    if not (categoria_geo and not entidades and lat_usuario is not None):
                        tiempo_resp = time.time() - start_time
                        # Almacenamos el ID incremental retornado de forma asincrónica por db.py
                        st.session_state["id_interaccion_actual"] = db.guardar_interaccion(texto_usuario, score, pp, tiempo_resp, wer_actual)
                    
                    status.update(label="Respuesta generada", state="complete")

    # --- RENDERIZADO PERSISTENTE DESDE EL STATE ---
    if st.session_state["respuesta_lista"] is not None:
        res = st.session_state["respuesta_lista"]
        st.chat_message("user").write(res["texto_usuario"])
        ruta_geo_activada = False

        if res["categoria_geo"] and not res["entidades"] and lat_usuario is not None:
            archivo_id, datos_geo, dist_geo = geo.obtener_mas_cercano(lat_usuario, lng_usuario, tipo_filtro=res["categoria_geo"])
            if datos_geo:
                ruta_geo_activada = True
                with st.chat_message("assistant", avatar="🏛️"):
                    emoji = "🍽️" if res["categoria_geo"] == "Gastronomia" else "🏛️"
                    msg_geo = f"A {dist_geo*1000:.0f} metros tenés **{datos_geo['nombre']}**."
                    st.success(f"{emoji} {msg_geo}")
                    mapa_geo = geo.generar_mapa_sitio(archivo_id)
                    if mapa_geo:
                        st_folium(mapa_geo, width=700, height=250, key=f"mapa_ruteo_{archivo_id}_{st.session_state['interaccion_id_actual']}", returned_objects=[])
                    if activar_tts:
                        try:
                            tts.sintetizar_para_web(msg_geo)
                            st.audio(os.path.join("data", "temp_res.mp3"), autoplay=True)
                        except Exception: pass
                
                # Sincronización geoespacial con almacenamiento por ID único
                if st.session_state["id_interaccion_actual"] is None:
                    tiempo_resp = time.time() - res["start_time"]
                    st.session_state["id_interaccion_actual"] = db.guardar_interaccion(res["texto_usuario"], 1.0, res["pp"], tiempo_resp, res["wer_actual"])

        if not ruta_geo_activada and res["score"] >= 0.08:
            with st.chat_message("assistant", avatar="🏛️"):
                titulo_limpio = res["resultado"].get('titulo', 'Información Encontrada').replace("[COLOQUIAL]", "").replace("[Coloquial]", "").strip()
                st.subheader(f"📍 {titulo_limpio}")
                
                contenido_raw = res["resultado"]['contenido'].split("Etiquetas:")[0].strip()
                cuerpo = contenido_raw.split("Respuesta:")[-1].strip() if "Respuesta:" in contenido_raw else contenido_raw

                intro_aleatoria = nlp.generar_introduccion_espontanea(titulo_limpio)
                st.markdown(f"*{intro_aleatoria}*")
                st.write(cuerpo)
                
                id_documento = res["resultado"].get('fuente', '').split('/')[-1].split('\\')[-1]
                mapa_sitio = geo.generar_mapa_sitio(id_documento, entidades=res["entidades"])
                if mapa_sitio:
                    st_folium(mapa_sitio, width=700, height=320, key=f"mapa_{id_documento}_{st.session_state['interaccion_id_actual']}", returned_objects=[])
                    st.caption(f"🗺️ Distribución espacial estimada de: *{res['resultado'].get('titulo')}*")
                
                with st.expander("Ver ficha técnica"):
                    st.caption(f"**Fuente:** {res['resultado'].get('fuente')}")
                    st.caption(f"**Confianza del Motor (Léxico Expandido):** {res['score']*100:.1f}%")
                    st.caption(f"**Entidades detectadas por spaCy:** {', '.join([e['texto'] for e in res['entidades']]) if res['entidades'] else 'Ninguna.'}")

                if activar_tts:
                    try:
                        tts.sintetizar_para_web(f"{intro_aleatoria} {cuerpo[:200]}")
                        st.audio(os.path.join("data", "temp_res.mp3"), autoplay=True)
                    except Exception: st.error("Error en la síntesis de voz.")

        elif not ruta_geo_activada and 0.04 <= res["score"] < 0.08:
            with st.chat_message("assistant", avatar="🏛️"):
                titulo_dudoso = res["resultado"].get('titulo', 'este lugar')
                st.warning(f"🤔 Te escuché con un poco de ruido. ¿Quisiste preguntar por **{titulo_dudoso}**?")
                with st.expander(f"Sí, era eso. Mostrar info sobre {titulo_dudoso}"):
                    cuerpo = res["resultado"]['contenido'].split("Etiquetas:")[0].strip()
                    st.write(cuerpo)

        elif not ruta_geo_activada:
            with st.chat_message("assistant", avatar="🏛️"):
                st.error("No alcancé a comprender la pregunta. Intentá de nuevo aportando más contexto.")

        # --- BLOQUE DE CAPTURA DE VOTO DE UTILIDAD (Sincronizado por ID único) ---
        if st.session_state["id_interaccion_actual"] is not None:
            st.write("---")
            st.markdown("💡 **¿Te sirvió la respuesta del Asistente?**")
            
            col_voto1, col_voto2 = st.columns(2)
            idx = st.session_state["interaccion_id_actual"]
            
            with col_voto1:
                if st.button("👍 Sí, fue útil", width='stretch', key=f"voto_pos_{idx}"):
                    db.registrar_feedback_por_id(st.session_state["id_interaccion_actual"], 1)
                    st.success("¡Gracias por ayudarnos a mejorar! 🗳️")
                    st.session_state["id_interaccion_actual"] = None
                    st.session_state["respuesta_lista"] = None
                    time.sleep(1)
                    st.rerun()

            with col_voto2:
                if st.button("👎 No me sirvió", width='stretch', key=f"voto_neg_{idx}"):
                    db.registrar_feedback_por_id(st.session_state["id_interaccion_actual"], -1)
                    st.error("Registrado para análisis en el Dashboard. 🔧")
                    st.session_state["id_interaccion_actual"] = None
                    st.session_state["respuesta_lista"] = None
                    time.sleep(1)
                    st.rerun()

# ==========================================
# VISTA 2: EL DASHBOARD TÉCNICO
# ==========================================
elif vista_actual == "📊 Dashboard Técnico":
    st.title("📊 Panel de Control Analítico")
    
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.markdown("Monitor de desempeño de los modelos de procesamiento y lenguaje.")
    if col_t2.button("🔄 Actualizar Datos", width='stretch'):
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

            st.subheader("🗺️ Cobertura y Densidad de Puntos de Interés Indexados")
            mapa_global = geo.generar_mapa_general()
            if mapa_global:
                st_folium(mapa_global, width=1300, height=400, key="mapa_dashboard_global", returned_objects=[])

            st.divider()
            st.subheader("📍 Cobertura Geográfica del Corpus")
            stats_geo = geo.obtener_estadisticas_cobertura()
            cg1, cg2, cg3, cg4 = st.columns(4)
            cg1.metric("Entradas en el Motor", stats_geo["total_entradas"])
            cg2.metric("Ubicaciones Únicas", stats_geo["coords_unicas"])
            cg3.metric("Puntos Históricos", stats_geo["historicos"])
            cg4.metric("Puntos Gastronómicos", stats_geo["gastronomicos"])

            st.divider()
            g1, g2 = st.columns(2)

            with g1:
                st.subheader("📈 Evolución de Perplejidad")
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                fig_pp = px.line(df.dropna(subset=['timestamp']), x='timestamp', y='perplejidad', title="Salud del Modelo de Lenguaje")
                fig_pp.add_hline(y=6.69, line_dash="dash", line_color="red", annotation_text="Objetivo")
                st.plotly_chart(fig_pp, use_container_width=True)

            with g2:
                st.subheader("📊 Términos Más Buscados")
                todas_palabras = " ".join(df['texto_transcripto'].dropna().tolist()).lower().split()
                stopwords = {"el", "la", "los", "las", "un", "una", "de", "en", "y", "a", "que", "es", "del", "al", "por", "con", "para", "qué", "como", "se", "te", "me"}
                palabras_limpias = [p for p in todas_palabras if p not in stopwords and len(p) > 2]
                if palabras_limpias:
                    conteo = collections.Counter(palabras_limpias).most_common(10)
                    df_palabras = pd.DataFrame(conteo, columns=['Término', 'Frecuencia'])
                    fig_hist = px.bar(df_palabras, x='Término', y='Frecuencia', color='Frecuencia', color_continuous_scale='Blues')
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No hay suficientes palabras para generar el histograma.")

            st.divider()
            st.subheader("🔗 Tablas de Probabilidad de Transición (N-gramas)")
            transiciones = []
            for ctx, next_words in ngrams.counts.items():
                ctx_str = " ".join(ctx) if ctx else "<inicio>"
                for word, count in next_words.items():
                    prob = ngrams.obtener_probabilidad(word, ctx)
                    transiciones.append({"Contexto": ctx_str, "Siguiente Palabra": word, "Apariciones": count, "Probabilidad": prob})
            if transiciones:
                df_trans = pd.DataFrame(transiciones).sort_values(by="Apariciones", ascending=False).head(10)
                df_trans["Probabilidad"] = df_trans["Probabilidad"].apply(lambda x: f"{x:.4f}")
                st.dataframe(df_trans, hide_index=True, use_container_width=True)

            st.divider()
            st.subheader("🎯 Métricas de Evaluación Rigurosa")
            metricas_test = db.obtener_metricas_test()
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Precisión (P)", f"{metricas_test['precision']:.2f}")
            col_m2.metric("Recall (R)", f"{metricas_test['recall']:.2f}")
            col_m3.metric("F1-Score", f"{metricas_test['f1']:.2f}")
            col_m4.metric("Accuracy NER", f"{metricas_test['accuracy_ner']*100:.1f}%")

            st.divider()
            st.subheader("📄 Registro de Interacciones")
            st.dataframe(df.sort_values(by='timestamp', ascending=False), hide_index=True, use_container_width=True)
        else:
            st.info("Aún no hay interacciones registradas en la base de datos.")
    except Exception as e:
        st.error(f"Error de lectura en la base de datos: {e}") 