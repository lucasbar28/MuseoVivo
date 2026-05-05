import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from modules.db import BaseDatos 

class MotorBusqueda:
    def __init__(self):
        self.vectorizador = TfidfVectorizer()
        self.metadata = [] 
        self.tfidf_matrix = None
        self.entrenar_con_db(BaseDatos())

    def limpiar_texto_historico(self, texto):
        """Elimina metadatos de carga y ruido de la web."""
        # Elimina fechas de sistema (ej: octubre 6, 2025)
        texto = re.sub(r'[a-zA-Záéíóú]+ \d{1,2}, \d{4}', '', texto)
        # Elimina pies de página comunes en los documentos cargados
        ruido = [
            "Deja una respuesta", "Cancelar la respuesta", 
            "También podría gustarte", "Publicado en"
        ]
        for frase in ruido:
            texto = texto.split(frase)[0]
        return texto.strip()

    def entrenar_con_db(self, db_instancia):
        """Carga el conocimiento y construye el índice TF-IDF."""
        try:
            db_instancia.cursor.execute("SELECT titulo, contenido, fuente FROM conocimiento")
            filas = db_instancia.cursor.fetchall()
            
            if not filas:
                return

            textos_entrenamiento = []
            self.metadata = []
            
            for f in filas:
                # Limpiamos el contenido antes de indexarlo para mejorar el match
                contenido_limpio = self.limpiar_texto_historico(f[1])
                textos_entrenamiento.append(f"{f[0]} {contenido_limpio}")
                
                self.metadata.append({
                    "titulo": f[0], 
                    "fuente": f[2], 
                    "contenido": contenido_limpio
                })
            
            self.tfidf_matrix = self.vectorizador.fit_transform(textos_entrenamiento)
            print(f"✅ Motor entrenado: {len(self.metadata)} docs limpios.")
        except Exception as e:
            print(f"❌ Error entrenamiento: {e}")

    def buscar_mas_relevante(self, consulta_texto):
        """Implementa búsqueda por similitud del coseno."""
        if self.tfidf_matrix is None:
            return {"contenido": "Error: Motor no entrenado"}, 0.0

        query_vector = self.vectorizador.transform([consulta_texto.lower()])
        similitudes = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        idx_mejor = similitudes.argmax()
        score = round(float(similitudes[idx_mejor]), 4)
        
        if score > 0.15: # Umbral ajustado para mayor precisión
            return self.metadata[idx_mejor], score
        
        return {"contenido": "No encontré información relevante en el archivo."}, 0.0 