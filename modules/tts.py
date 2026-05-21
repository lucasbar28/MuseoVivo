import os
import re
from gtts import gTTS

class TTSEngine:
    def __init__(self):
        self.idioma = 'es'
        self.tld = 'com.ar'  # Acento regional argentino
        self.output_dir = "data"
        
        # Aseguramos que la carpeta data exista para evitar errores de ruta
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def limpiar_texto(self, texto):
        """
        Elimina ruido del texto para que la locución sea más natural.
        Limpia URLs, corchetes de referencias y exceso de espacios.
        """
        if not texto:
            return ""
        # Elimina URLs (http/https)
        texto = re.sub(r'http\S+', '', texto)
        # Elimina referencias entre corchetes tipo [1], [fuente]
        texto = re.sub(r'\[.*?\]', '', texto)
        # Reemplaza saltos de línea por espacios para una lectura continua
        texto = texto.replace("\n", " ").strip()
        # Elimina espacios múltiples
        texto = re.sub(r'\s+', ' ', texto)
        return texto

    def sintetizar_para_web(self, texto):
        """
        Convierte texto a audio y devuelve la ruta del archivo MP3.
        Optimizado para respuestas rápidas limitando la longitud.
        """
        if not texto:
            return None
            
        try:
            # 1. Pre-procesamiento del texto
            texto_limpio = self.limpiar_texto(texto)
            
            # 2. Recorte de seguridad (Max 500 caracteres para el audio)
            # Esto mejora la latencia y evita que el usuario espere demasiado la descarga
            if len(texto_limpio) > 500:
                texto_final = texto_limpio[:500] + "..."
            else:
                texto_final = texto_limpio
                
            # 3. Generación del audio
            tts = gTTS(text=texto_final, lang=self.idioma, tld=self.tld, slow=False)
            filename = os.path.join(self.output_dir, "temp_res.mp3")
            
            # 4. Guardado (sobrescribe el anterior para ahorrar espacio)
            tts.save(filename)
            
            print(f"🔊 TTS: Audio generado con éxito ({len(texto_final)} caracteres).")
            return filename 
            
        except Exception as e:
            print(f"❌ Error en TTS: {e}")
            return None 