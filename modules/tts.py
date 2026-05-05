from gtts import gTTS
import os

class TTSEngine:
    def __init__(self):
        self.idioma = 'es'
        self.tld = 'com.ar'  # Acento regional para Chascomús
        self.output_dir = "data"
        
        # Aseguramos que la carpeta data exista para guardar el audio temporal
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def sintetizar_para_web(self, texto):
        """
        Convierte texto a audio y devuelve la ruta del archivo.
        No intenta reproducir con el sistema operativo para evitar errores en la nube.
        """
        try:
            tts = gTTS(text=texto, lang=self.idioma, tld=self.tld, slow=False)
            filename = os.path.join(self.output_dir, "temp_res.mp3")
            tts.save(filename)
            return filename  # Retornamos la ruta para que st.audio() la use
            
        except Exception as e:
            print(f"Error en TTS: {e}")
            return None 