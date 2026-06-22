import streamlit as st
import pandas as pd
import plotly.express as px
import time
import io
import os
import collections
import random
import unicodedata

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

# --- CONFIGURACIÓN GLOBAL Y ESTILADO ---
st.set_page_config(page_title="MuseoVivo Chascomús", page_icon="🏛️", layout="wide")

# Custom CSS institucional premium para optimizar espacio, contraste y profundidad visual
st.markdown("""
    <style>
        /* 1. Fondo general de la App con un degradado sutil y tecnológico */
        .stApp {
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        }
        
        /* 2. Suavizar la barra lateral para que acompañe el tono */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #f1f5f9 100%);
            border-right: 1px solid #cbd5e1;
        }
        
        /* 3. Estilado moderno de contenedores con borde (Efecto Tarjeta Premium translúcida) */
        div[data-testid="stHeaderBlock"] + div, 
        .stElementContainer div[data-testid="stHTMLBlock"] + div,
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(8px);
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.6) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            padding: 15px !important;
        }

        /* 4. Tipografías institucionales limpias */
        h1 {
            color: #0f172a;
            font-weight: 800 !important;
            letter-spacing: -0.05em;
        }
        h3 {
            color: #1e293b;
            font-weight: 700 !important;
            margin-top: 10px !important;
        }
        .subtitulo-guia {
            color: #475569;
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }
        
        /* 5. Forzar a los iFrames de Folium a respetar el contenedor de forma fluida */
        iframe {
            width: 100% !important;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def inicializar_modulos():
    # 1. Instanciamos la DB y el Motor de Búsqueda primero
    base_datos = BaseDatos()
    motor_busqueda = MotorBusqueda()
    
    # 2. Instanciamos el modelo de N-gramas vacío
    modelo_ngrams = ModeloNgramas(n=2, k=0.5, db_instancia=None)
    
    # 3. --- ENTRENAMIENTO ROBUSTO CON EL CORPUS REAL DE CHASCOMÚS ---
    try:
        corpus_base = []
        if hasattr(motor_busqueda, 'documentos') and motor_busqueda.documentos:
            for doc in motor_busqueda.documentos:
                if 'contenido' in doc:
                    corpus_base.append(doc['contenido'])
        
        if corpus_base:
            modelo_ngrams.entrenar(corpus_base)
        else:
            modelo_ngrams.entrenar([
                "donde queda la capilla de los negros", 
                "lugares para comer algo o tomar cerveza", 
                "donde pescar pejerrey en la laguna de chascomus"
            ])
    except Exception:
        modelo_ngrams.entrenar(["donde queda la capilla de los negros", "donde comer algo", "pescar en la laguna"])
    
    return ASREngine(), NLPProcessor(), modelo_ngrams, motor_busqueda, TTSEngine(), base_datos, GeoEngine()

asr, nlp, ngrams, search, tts, db, geo = inicializar_modulos()

# --- CONTROL DE ESTADOS CRÍTICOS (Persistencia Absoluta) ---
if "respuesta_lista" not in st.session_state:
    st.session_state["respuesta_lista"] = None
if "ultima_pregunta_guardada" not in st.session_state:
    st.session_state["ultima_pregunta_guardada"] = None
if "id_interaccion_actual" not in st.session_state:
    st.session_state["id_interaccion_actual"] = None
if "contador_interacciones" not in st.session_state:
    st.session_state["contador_interacciones"] = 0
if "ultimo_audio_id" not in st.session_state:
    st.session_state["ultimo_audio_id"] = None
if "disparar_sugerencia" not in st.session_state:
    st.session_state["disparar_sugerencia"] = None
if "mensaje_feedback" not in st.session_state:
    st.session_state["mensaje_feedback"] = None

# --- FUNCIONES DE CALLBACK PARA EL FEEDBACK ---
def procesar_feedback_callback(id_interaccion, valor_voto):
    """Callback seguro ejecutado antes del rerun de Streamlit"""
    try:
        db.registrar_feedback_por_id(id_interaccion, valor_voto)
        if valor_voto == 1:
            st.session_state["mensaje_feedback"] = ("success", "¡Gracias por tu feedback! 🗳️")
        else:
            st.session_state["mensaje_feedback"] = ("error", "Feedback registrado. Ajustaremos las respuestas. 🔧")
    except Exception as e:
        st.session_state["mensaje_feedback"] = ("error", f"Error al guardar feedback: {e}")
    
    # Limpiamos las variables de la interacción actual para permitir una nueva consulta
    st.session_state["id_interaccion_actual"] = None
    st.session_state["respuesta_lista"] = None

# --- ENRUTADOR LATERAL ---
with st.sidebar:
    st.markdown("# 🏛️ MuseoVivo\n**Patrimonio Inteligente**")
    st.markdown("---")
    
    st.write("📌 **Módulo de Trabajo**")
    vista_actual = st.radio(
        "Seleccioná la interfaz:", 
        ["🏛️ Interfaz del Turista", "📊 Dashboard Técnico"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    with st.container(border=True):
        st.markdown("🛰 *Herramientas de Defensa*")
        modo_simulacion = st.toggle("🕹️ Simular GPS en Plaza Independencia", value=False)
    
    st.markdown("---")
    st.caption("🎓 **Proyecto Integrador**")
    st.caption("Ciencia de Datos | UTN")
    st.caption("Fases 1 y 2 Integradas • v2.7")


# Funcionalidad auxiliar para procesar textos disparados (Voz o Botones de Sugerencia)
def procesar_texto_consulta(texto_usuario, lat_usuario):
    start_time = time.time()
    st.session_state["ultima_pregunta_guardada"] = texto_usuario
    st.session_state["contador_interacciones"] += 1
    st.session_state["mensaje_feedback"] = None # Limpiamos carteles anteriores de feedback
    
    analisis_nlp = nlp.procesar_consulta(texto_usuario)
    entidades = analisis_nlp["entidades"]
    
    palabras_ruido = {
        "que", "qué", "puedo", "pueden", "hacer", "donde", "dónde", "buscar", 
        "quiero", "algun", "alguna", "la", "el", "los", "las", "un", "una", 
        "de", "del", "al", "en", "para", "queda", "sobre", "comerte", "algo"
    }
    
    texto_normalizado = ''.join(
        c for c in unicodedata.normalize('NFD', texto_usuario.lower()) 
        if unicodedata.category(c) != 'Mn'
    )
    
    palabras_filtradas = [p for p in texto_normalizado.split() if p not in palabras_ruido]
    texto_busqueda_limpio = " ".join(palabras_filtradas) if palabras_filtradas else texto_normalizado
    
    if "negros" in texto_normalizado or "negro" in texto_normalizado:
        texto_busqueda_limpio = "negros capilla"
    if "comer" in texto_normalizado or "cerveceria" in texto_normalizado:
        texto_busqueda_limpio = "comer"
    if "pejerrey" in texto_normalizado or "pesca" in texto_normalizado:
        texto_busqueda_limpio = "pejerrey"
    
    resultado, score = search.buscar_mas_relevante(texto_busqueda_limpio)
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
    
    if not (categoria_geo and lat_usuario is not None):
        tiempo_resp = time.time() - start_time
        st.session_state["id_interaccion_actual"] = db.guardar_interaccion(texto_usuario, score, pp, tiempo_resp, wer_actual)


# ==========================================
# VISTA 1: LA EXPERIENCIA DEL TURISTA
# ==========================================
if vista_actual == "🏛️ Interfaz del Turista":
    st.title("🏛️ MuseoVivo: Guía de Patrimonio")
    st.markdown("<p class='subtitulo-guia'>Interactuá con la historia y cultura de Chascomús a través de tu voz.</p>", unsafe_allow_html=True)

    # Mostrar notificaciones efímeras de feedback si existen del ciclo anterior
    if st.session_state["mensaje_feedback"]:
        tipo, msg = st.session_state["mensaje_feedback"]
        if tipo == "success":
            st.success(msg)
        else:
            st.error(msg)
        st.session_state["mensaje_feedback"] = None # Consumir el mensaje

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

    if st.session_state["disparar_sugerencia"] is not None:
        sug_texto = st.session_state["disparar_sugerencia"]
        st.session_state["disparar_sugerencia"] = None
        procesar_texto_consulta(sug_texto, lat_usuario)

    # Distribución en proporciones balanceadas 11:10 para evitar estiramientos laterales
    col_izquierda, col_derecha = st.columns([11, 10], gap="large")

    with col_izquierda:
        st.markdown("### 🎙️ Panel de Control y Voz")
        with st.container(border=True):
            activar_tts = st.toggle("🔊 Activar respuesta por voz (TTS)", value=True)
            audio_value = st.audio_input("Presioná el micrófono para preguntar")
            
        st.markdown("---")
        st.markdown("### 📍 Mi Radar Chascomús")
        with st.container(border=True):
            if lat_usuario is not None and lng_usuario is not None:
                if modo_simulacion:
                    st.caption("🕹️ Modo Simulación Activo: Centro Histórico (Plaza Independencia)")
                else:
                    st.caption("🟢 Señal GPS detectada y sincronizada en tiempo real")
                
                col_geo1, col_geo2, col_geo3 = st.columns(3)

                if col_geo1.button("🏛️ Patrimonio", width="stretch"):
                    archivo_id, datos, dist = geo.obtener_mas_cercano(lat_usuario, lng_usuario, tipo_filtro="Historico")
                    if datos:
                        msg = f"A {dist*1000:.0f} metros tenés {datos['nombre']}."
                        st.success(f"🏛️ {msg}")
                        mapa_cercano = geo.generar_mapa_sitio(archivo_id)
                        if mapa_cercano:
                            st_folium(mapa_cercano, height=220, key="mapa_cercano_hist", returned_objects=[])
                        if activar_tts:
                            try:
                                ruta_audio = tts.sintetizar_para_web(msg)
                                if ruta_audio: st.audio(ruta_audio, autoplay=False)
                            except Exception: pass

                if col_geo2.button("🍔 Gastronomía", width="stretch"):
                    archivo_id, datos, dist = geo.obtener_mas_cercano(lat_usuario, lng_usuario, tipo_filtro="Gastronomia")
                    if datos:
                        msg = f"A {dist*1000:.0f} metros podés visitar {datos['nombre']}."
                        st.success(f"🍺 {msg}")
                        mapa_cercano = geo.generar_mapa_sitio(archivo_id)
                        if mapa_cercano:
                            st_folium(mapa_cercano, height=220, key="mapa_cercano_gast", returned_objects=[])
                        if activar_tts:
                            try:
                                ruta_audio = tts.sintetizar_para_web(msg)
                                if ruta_audio: st.audio(ruta_audio, autoplay=False)
                            except Exception: pass
                
                if col_geo3.button("🗺️ Ver Mapa", width="stretch"):
                    mapa_completo = geo.generar_mapa_general()
                    if mapa_completo:
                        st_folium(mapa_completo, height=220, key="mapa_turista_global", returned_objects=[])
            else:
                col_info, col_action = st.columns([3, 2])
                col_info.info("💡 Habilitá los permisos de ubicación en tu navegador para el radar turístico.")
                if col_action.button("🕹️ Activar Simulación", width="stretch"):
                    st.warning("Activando simulación en la barra lateral...")
                    time.sleep(0.4)

        if audio_value is not None:
            audio_id = id(audio_value)
            if audio_id != st.session_state["ultimo_audio_id"]:
                st.session_state["ultimo_audio_id"] = audio_id
                audio_path = "temp_query.wav"
                with open(audio_path, "wb") as f:
                    f.write(audio_value.read())
                
                with st.status("Procesando consulta...", expanded=False) as status:
                    texto_usuario = asr.transcribir_desde_archivo(audio_path)
                    if texto_usuario:
                        procesar_texto_consulta(texto_usuario, lat_usuario)
                        status.update(label="Respuesta generada", state="complete")

    with col_derecha:
        st.markdown("### 📖 Respuestas del Asistente")
        
        if st.session_state["respuesta_lista"] is not None:
            res = st.session_state["respuesta_lista"]
            st.chat_message("user").write(res["texto_usuario"])
            ruta_geo_activada = False

            # --- CASO GEOFENCING ACTIVADO ---
            if res["categoria_geo"] and lat_usuario is not None:
                archivo_id, datos_geo, dist_geo = geo.obtener_mas_cercano(lat_usuario, lng_usuario, tipo_filtro=res["categoria_geo"])
                if datos_geo:
                    ruta_geo_activada = True
                    with st.chat_message("assistant", avatar="🏛️"):
                        emoji = "🍽️" if res["categoria_geo"] == "Gastronomia" else "🏛️"
                        msg_geo = f"A {dist_geo*1000:.0f} metros tenés **{datos_geo['nombre']}**."
                        st.markdown(f"{emoji} {msg_geo}")
                        
                        with st.container(border=True):
                            mapa_geo = geo.generar_mapa_sitio(archivo_id)
                            if mapa_geo:
                                st_folium(mapa_geo, height=250, key=f"mapa_ruteo_{archivo_id}_{st.session_state['contador_interacciones']}", returned_objects=[])
                            if activar_tts:
                                try:
                                    notify_audio = tts.sintetizar_para_web(msg_geo)
                                    if notify_audio: st.audio(notify_audio, autoplay=False)
                                except Exception: pass
                    
                    if st.session_state["id_interaccion_actual"] is None:
                        tiempo_resp = time.time() - res["start_time"]
                        st.session_state["id_interaccion_actual"] = db.guardar_interaccion(res["texto_usuario"], res["score"], res["pp"], tiempo_resp, res["wer_actual"])

            # --- CASO BÚSQUEDA EXITOSA LÉXICA ---
            if not ruta_geo_activada and res["score"] >= 0.03:
                with st.chat_message("assistant", avatar="🏛️"):
                    titulo_limpio = res["resultado"].get('titulo', 'Información Encontrada').replace("[COLOQUIAL]", "").replace("[Coloquial]", "").strip()
                    st.subheader(f"📍 {titulo_limpio}")
                    
                    contenido_raw = res["resultado"]['contenido'].split("Etiquetas:")[0].strip()
                    cuerpo = contenido_raw.split("Respuesta:")[-1].strip() if "Respuesta:" in contenido_raw else contenido_raw

                    intro_aleatoria = nlp.generar_introduccion_espontanea(titulo_limpio)
                    st.markdown(f"*{intro_aleatoria}*")
                    
                    # ✨ CAJA CON HEIGHT FIJO Y SCROLL INTERNO PARA EL CUERPO TEXTUAL DEL CORPUS
                    with st.container(height=250, border=False):
                        st.write(cuerpo)
                    
                    with st.container(border=True):
                        id_documento = res["resultado"].get('fuente', '').split('/')[-1].split('\\')[-1]
                        mapa_sitio = geo.generar_mapa_sitio(id_documento, entidades=res["entidades"])
                        if mapa_sitio:
                            st_folium(mapa_sitio, height=260, key=f"mapa_{id_documento}_{st.session_state['contador_interacciones']}", returned_objects=[])
                        
                        with st.expander("Ver ficha técnica", expanded=False):
                            st.caption(f"**Confianza:** {res['score']*100:.1f}%")
                            st.caption(f"**Entidades detectadas:** {', '.join([e['texto'] for e in res['entidades']]) if res['entidades'] else 'Ninguna.'}")

                        if activar_tts:
                            try:
                                ruta_audio = tts.sintetizar_para_web(f"{intro_aleatoria} {cuerpo}")
                                if ruta_audio: st.audio(ruta_audio, autoplay=False)
                            except Exception: pass

            elif not ruta_geo_activada and 0.01 <= res["score"] < 0.03:
                with st.chat_message("assistant", avatar="🏛️"):
                    titulo_dudoso = res["resultado"].get('titulo', 'este lugar').upper()
                    st.warning("🤔 Quizás quisiste consultar sobre:")
                    if st.button(f"👉 {titulo_dudoso}", width="stretch", key=f"sug_btn_{st.session_state['contador_interacciones']}_f"):
                        st.session_state["disparar_sugerencia"] = f"Contame sobre {titulo_dudoso.lower()}"
                        st.rerun()

            elif not ruta_geo_activada:
                with st.chat_message("assistant", avatar="🏛️"):
                    st.error("No alcancé a comprender la pregunta. Intentá incorporando términos específicos (ej: 'Pejerrey' o 'Capilla').")

            # --- FEEDBACK DE INTERACCIÓN (Optimizado con Callbacks) ---
            if st.session_state["id_interaccion_actual"] is not None:
                st.write("---")
                st.markdown("💡 **¿Te sirvió la respuesta?**")
                col_voto1, col_voto2 = st.columns(2)
                idx = st.session_state["contador_interacciones"]
                
                # Se asigna la lógica a on_click para evitar problemas con la recarga de Streamlit
                col_voto1.button(
                    "👍 Sí, útil", 
                    width="stretch", 
                    key=f"voto_pos_{idx}",
                    on_click=procesar_feedback_callback,
                    args=(st.session_state["id_interaccion_actual"], 1)
                )
                
                col_voto2.button(
                    "👎 No me sirvió", 
                    width="stretch", 
                    key=f"voto_neg_{idx}",
                    on_click=procesar_feedback_callback,
                    args=(st.session_state["id_interaccion_actual"], -1)
                )
        else:
            with st.container(border=True):
                st.markdown("""
                    #### 💡 ¿Qué podés consultar?
                    Probá usando tu voz con preguntas cómo:
                    * *¿Dónde queda la Capilla de los Negros?*
                    * *Lugares para comer algo o tomar cerveza.*
                    * *¿Qué historia tiene la Laguna de Chascomús?*
                    
                    ---
                    *El sistema extraerá entidades con spaCy, medirá perplejidad mediante N-gramas y resolverá la consulta usando Similitud Coseno sobre índices locales.*
                """)

# ==========================================
# VISTA 2: EL DASHBOARD TÉCNICO
# ==========================================
elif vista_actual == "📊 Dashboard Técnico":
    st.title("📊 Panel de Control Analítico")
    
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.markdown("Monitor de desempeño de los modelos de procesamiento y lenguaje.")
    if col_t2.button("🔄 Actualizar Datos", width="stretch"):
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
                st_folium(mapa_global, height=380, key="mapa_dashboard_global", returned_objects=[])

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
                stopwords = {"el", "la", "los", "las", "un", "una", "de", "en", "y", "a", "que", "is", "es", "del", "al", "por", "con", "para", "qué", "como", "se", "te", "me"}
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
            df_formateado = df.copy()
            df_formateado['score_similitud'] = df_formateado['score_similitud'].round(4)
            df_formateado = df_formateado.sort_values(by='timestamp', ascending=False)
            
            def colorear_feedback(val):
                if val == 1:
                    return 'background-color: rgba(40, 167, 69, 0.15)'
                elif val == -1:
                    return 'background-color: rgba(220, 53, 69, 0.15)'
                return ''
                
            df_estilado = df_formateado.style.map(colorear_feedback, subset=['feedback'])
            st.dataframe(df_estilado, hide_index=True, use_container_width=True)
        else:
            st.info("Aún no hay interacciones registradas en la base de datos.")
    except Exception as e:
        st.error(f"Error de lectura en la base de datos: {e}") 