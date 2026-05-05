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
    st.success("Base de Datos: 33 archivos indexados")
    
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
            
            # B. NLP & BÚSQUEDA
            resultado, score = search.buscar_mas_relevante(texto_usuario)
            
            # C. VALIDACIÓN (N-Grams)
            pp = ngrams.calcular_perplejidad(texto_usuario)
            st.session_state.ultima_pp = pp
            
            # D. RESULTADOS Y TTS
            if score > 0.3:
                with st.chat_message("assistant", avatar="🏛️"):
                    st.subheader(f"📍 {resultado.get('titulo', 'Información Encontrada')}")
                    
                    contenido = resultado['contenido']
                    cuerpo = contenido.split("Etiquetas:")[0].split("También podría gustarte")[0].strip()
                    st.write(cuerpo)
                    
                    with st.expander("Ver ficha técnica y etiquetas"):
                        st.caption(f"**Fuente:** {resultado.get('fuente')}")
                        st.caption(f"**Confianza:** {score*100:.1f}%")

                # E. AUDIO DE RESPUESTA
                path_audio_res = tts.sintetizar_para_web(cuerpo)
                st.audio(path_audio_res)

                # --- SISTEMA DE FEEDBACK ESTILIZADO ---
                st.markdown("---")
                with st.container():
                    st.write("¿Te resultó útil esta información?")
                    col_f1, col_f2, _ = st.columns([1, 1, 4])
                    
                    with col_f1:
                        if st.button("👍 Sí", use_container_width=True):
                            db.registrar_feedback(texto_usuario, 1)
                            st.toast("¡Gracias! Me alegra ayudar.", icon="😊")
                    
                    with col_f2:
                        if st.button("👎 No", use_container_width=True):
                            db.registrar_feedback(texto_usuario, -1)
                            st.toast("Entendido, seguiré aprendiendo.", icon="🫡")
            else:
                st.warning("No encontré información específica. ¿Podrías intentar reformular?")
            
            # F. PERSISTENCIA Y MÉTRICA WER
            tiempo_resp = time.time() - start_time
            
            # Calculamos el WER comparando la transcripción con el título del resultado 
            # como referencia de éxito semántico.
            wer_actual = asr.calcular_wer(resultado.get('titulo', ''), texto_usuario)
            
            # Guardamos todo en la DB
            db.guardar_interaccion(texto_usuario, score, pp, tiempo_resp)
            # Nota: Asegúrate de que db.guardar_interaccion acepte el valor de WER si quieres trackearlo
            
            status.update(label="Respuesta generada", state="complete")
        else:
            st.error("No se pudo procesar el audio.") 