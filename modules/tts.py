import os
import re
import hashlib
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
        # Reemplaza asteriscos de formato Markdown (evita que gTTS intente leer "asterisco")
        texto = texto.replace("**", "").replace("*", "")
        # Reemplaza saltos de línea por espacios para una lectura continua
        texto = texto.replace("\n", " ").strip()
        # Elimina espacios múltiples
        texto = re.sub(r'\s+', ' ', texto)
        return texto

    def _recortar_texto_inteligente(self, texto, max_chars=500):
        """Corta el texto respetando los límites de las palabras para no romper la dicción."""
        if len(texto) <= max_chars:
            return texto
            
        # Buscamos cortar en el último espacio disponible antes del límite
        corte = texto[:max_chars].rfind(' ')
        if corte == -1:
            corte = max_chars
            
        return texto[:corte].strip() + "..."

    def sintetizar_para_web(self, texto):
        """
        Convierte texto a audio devolviendo una ruta única basada en hash MD5.
        Previene bloqueos de archivo en Windows y actúa como caché de audio.
        """
        if not texto:
            return None
            
        try:
            # 1. Pre-procesamiento y corte limpio de oraciones
            texto_limpio = self.limpiar_texto(texto)
            texto_final = self._recortar_texto_inteligente(texto_limpio, max_chars=500)
            
            if not texto_final.replace("...", "").strip():
                return None

            # 2. Generar un nombre único basado en el contenido (Caché Dinámica)
            # Evita el error de bloqueo de archivo de Windows (PermissionError)
            text_hash = hashlib.md5(texto_final.encode('utf-8')).hexdigest()
            filename = os.path.join(self.output_dir, f"tts_{text_hash}.mp3")
            
            # 3. Si el audio ya fue generado antes, lo reutilizamos al instante
            if os.path.exists(filename):
                print(f"🔊 TTS Cache: Reutilizando audio existente -> {filename}")
                return filename
            
            # 4. Generación y guardado del nuevo audio
            tts = gTTS(text=texto_final, lang=self.idioma, tld=self.tld, slow=False)
            tts.save(filename)
            
            print(f"🔊 TTS: Nuevo audio generado con éxito ({len(texto_final)} caracteres).")
            return filename 
            
        except Exception as e:
            print(f"❌ Error en TTS: {e}")
            return None 