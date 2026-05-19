import streamlit as st
import time
import os
from modules.asr import ASREngine
from modules.nlp import NLPProcessor
from modules.ngrams import ModeloNgramas
from modules.search import MotorBusqueda
from modules.tts import TTSEngine
from modules.db import BaseDatos

# 1. Configuración de la Interfaz
st.set_page_config(page_title="MuseoVivo Chascomús", page_icon="🏛️", layout="wide")

@st.cache_resource
def inicializar_modulos():
    return ASREngine(), NLPProcessor(), ModeloNgramas(), MotorBusqueda(), TTSEngine(), BaseDatos()

asr, nlp, ngrams, search, tts, db = inicializar_modulos()

# --- BARRA LATERAL: Estado y Métricas ---
with st.sidebar:
    st.title("📊 Estado del Sistema")
    
    total_docs = db.contar_documentos()
    st.success(f"Base de Datos: {total_docs} archivos indexados")
    
    col1, col2 = st.columns(2)
    col1.metric("Objetivo PP", "6.69")
    
    if "ultima_pp" in st.session_state:
        col2.metric("Última PP", f"{st.session_state.ultima_pp:.2f}")

# --- CUERPO PRINCIPAL ---
st.title("🏛️ MuseoVivo: Guía de Patrimonio")
st.markdown("Interactuá con la historia de **Chascomús** a través de tu voz.")

# 2. CAPTURA DE AUDIO
audio_value = st.audio_input("Presioná el micrófono para preguntar")

if audio_value:
    audio_path = "temp_query.wav"
    with open(audio_path, "wb") as f:
        f.write(audio_value.read())
    
    with st.status("Procesando consulta...", expanded=False) as status:
        start_time = time.time()
        
        # A. ASR (Voz a Texto)
        texto_usuario = asr.transcribir_desde_archivo(audio_path)
        
        if texto_usuario:
            st.chat_message("user").write(texto_usuario)
            
            # B. NLP (Análisis de Entidades e Intenciones)
            analisis_nlp = nlp.procesar_consulta(texto_usuario)
            entidades = analisis_nlp["entidades"]
            
            # C. BÚSQUEDA TF-IDF (N-Grams)
            resultado, score = search.buscar_mas_relevante(texto_usuario)
            
            # D. VALIDACIÓN DE LENGUAJE (N-Grams PP)
            pp = ngrams.calcular_perplejidad(texto_usuario)
            st.session_state.ultima_pp = pp
            
            # E. LÓGICA DE RESPUESTA INTELIGENTE
            # Escenario 1: Confianza suficiente (Score > 0.12 con N-Grams es bueno)
            if score > 0.12:
                with st.chat_message("assistant", avatar="🏛️"):
                    st.subheader(f"📍 {resultado.get('titulo', 'Información Encontrada')}")
                    
                    cuerpo = resultado['contenido'].split("Etiquetas:")[0].strip()
                    st.write(cuerpo)
                    
                    with st.expander("Ver ficha técnica"):
                        st.caption(f"**Fuente:** {resultado.get('fuente')}")
                        st.caption(f"**Confianza del Motor:** {score*100:.1f}%")
                        st.caption(f"**Entidades detectadas:** {', '.join([e['texto'] for e in entidades])}")

                    # Audio de Respuesta
                    path_audio_res = tts.sintetizar_para_web(cuerpo[:250]) # Síntesis del inicio
                    st.audio(path_audio_res)

                    # Sistema de Feedback
                    st.markdown("---")
                    st.write("¿Te resultó útil?")
                    cf1, cf2, _ = st.columns([1, 1, 4])
                    if cf1.button("👍 Sí", use_container_width=True):
                        db.registrar_feedback(texto_usuario, 1)
                        st.toast("¡Gracias!", icon="😊")
                    if cf2.button("👎 No", use_container_width=True):
                        db.registrar_feedback(texto_usuario, -1)
                        st.toast("Lo tendré en cuenta.", icon="🫡")

            # Escenario 2: No hay respuesta exacta pero detectamos de qué lugar habla (Sugerencias)
            elif entidades:
                with st.chat_message("assistant", avatar="🏛️"):
                    lugar_detectado = entidades[0]["texto"]
                    st.markdown(f"🔍 Identifiqué que mencionaste **{lugar_detectado}**.")
                    st.write(f"No tengo una respuesta corta para eso, pero ¿querés saber algo específico?")
                    
                    col_s1, col_s2 = st.columns(2)
                    if col_s1.button(f"📜 Historia de {lugar_detectado}", use_container_width=True):
                        st.info(f"Probá preguntar: 'Contame la historia de {lugar_detectado}'")
                    if col_s2.button(f"📍 Ubicación de {lugar_detectado}", use_container_width=True):
                        st.info(f"Probá preguntar: '¿Dónde queda {lugar_detectado}?'")

            # Escenario 3: Fallo total
            else:
                st.warning("No logré identificar el tema. ¿Podrías intentar reformular con una frase más larga?")

            # F. PERSISTENCIA Y MÉTRICAS FINALES
            tiempo_resp = time.time() - start_time
            # Solo calculamos WER si hay un título contra qué comparar
            wer_actual = asr.calcular_wer(resultado.get('titulo', ''), texto_usuario) if score > 0.12 else 1.0
            
            db.guardar_interaccion(texto_usuario, score, pp, tiempo_resp)
            
            status.update(label="Respuesta generada", state="complete")
        else:
            st.error("No se pudo procesar el audio.") 