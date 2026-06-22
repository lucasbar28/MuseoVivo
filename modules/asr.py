import speech_recognition as sr

class ASREngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Ajuste dinámico para ambientes con ruido (ej: Viento en la laguna)
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Un poco más de tiempo para frases largas

    def transcribir_desde_mic(self):
        """Captura audio del micrófono local (útil para pruebas fuera de Streamlit)."""
        with sr.Microphone() as source:
            print(">>> Escuchando... (hablá ahora)")
            # Reducimos duración para que no se sienta lento el inicio
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source)

        try:
            texto = self.recognizer.recognize_google(audio, language="es-AR")
            return texto
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"ASR: Error en el servicio de Google; {e}")
            return None

    def transcribir_desde_archivo(self, ruta_archivo):
        """Procesa el audio enviado desde el componente st.audio_input de Streamlit."""
        try:
            with sr.AudioFile(ruta_archivo) as source:
                # Importante: No abusar del ajuste de ruido en archivos digitales limpios
                audio = self.recognizer.record(source)
            
            return self.recognizer.recognize_google(audio, language="es-AR")
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            print("ASR: Error de red o cuota de API excedida.")
            return None
        except Exception as e:
            print(f"ASR: Error crítico: {e}")
            return None

    def calcular_wer(self, referencia, hipotesis):
        """
        Métrica: Word Error Rate (WER) basada en distancia de Levenshtein.
        Calcula la precisión del ASR comparando el audio con el resultado esperado.
        """
        if not referencia:
            return 1.0 if hipotesis else 0.0
        if not hipotesis:
            return 1.0

        r = referencia.lower().split()
        h = hipotesis.lower().split()
        
        # Matriz de Levenshtein
        d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
        
        for i in range(len(r) + 1): d[i][0] = i
        for j in range(len(h) + 1): d[0][j] = j
            
        for i in range(1, len(r) + 1):
            for j in range(1, len(h) + 1):
                if r[i-1] == h[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        # Cálculo final
        wer_value = float(d[len(r)][len(h)]) / len(r)
        return min(wer_value, 1.0) 