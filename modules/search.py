import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from modules.db import BaseDatos 

class MotorBusqueda:
    def __init__(self):
        # Implementamos N-gramas (1, 2) para entender conceptos compuestos
        self.vectorizador = TfidfVectorizer(
            ngram_range=(1, 2), 
            strip_accents='unicode',
            lowercase=True
        )
        self.metadata = [] 
        self.tfidf_matrix = None
        self.entrenar_con_db(BaseDatos())

    def limpiar_texto_historico(self, texto):
        """Elimina metadatos de carga y mejora el formato visual."""
        # 1. Elimina fechas de sistema
        texto = re.sub(r'[a-zA-Záéíóú]+ \d{1,2}, \d{4}', '', texto)
        
        # 2. Corta ruido web
        ruido = ["Deja una respuesta", "Cancelar la respuesta", "También podría gustarte", "Publicado en"]
        for frase in ruido:
            texto = texto.split(frase)[0]
        
        # 3. INTERACTIVIDAD: Reparar puntos pegados para crear párrafos
        # Esto cambia "vivienda.En 1829" por "vivienda. En 1829"
        texto = re.sub(r'\.([a-zA-Záéíóú])', r'. \1', texto)
        
        # 4. Agrega saltos de línea después de cada punto para que Streamlit lo vea menos "pesado"
        texto = texto.replace(". ", ".\n\n")
        
        return texto.strip()

    def entrenar_con_db(self, db_instancia):
        """Carga el conocimiento y construye el índice TF-IDF."""
        try:
            db_instancia.cursor.execute("SELECT titulo, contenido, fuente FROM conocimiento")
            filas = db_instancia.cursor.fetchall()
            
            if not filas: return

            textos_entrenamiento = []
            self.metadata = []
            
            for f in filas:
                contenido_limpio = self.limpiar_texto_historico(f[1])
                # Indexamos título + contenido para darle más peso al nombre del lugar
                textos_entrenamiento.append(f"{f[0]} {f[0]} {contenido_limpio}")
                
                self.metadata.append({
                    "titulo": f[0].replace("_", " ").upper(), # Limpiamos el título doc_13...
                    "fuente": f[2], 
                    "contenido": contenido_limpio
                })
            
            self.tfidf_matrix = self.vectorizador.fit_transform(textos_entrenamiento)
            print(f"✅ Motor N-Grams listo: {len(self.metadata)} docs.")
        except Exception as e:
            print(f"❌ Error entrenamiento: {e}")

    def buscar_mas_relevante(self, consulta_texto):
        """Búsqueda avanzada por similitud del coseno."""
        if self.tfidf_matrix is None:
            return {"contenido": "Error: Motor no entrenado"}, 0.0

        query_vector = self.vectorizador.transform([consulta_texto.lower()])
        similitudes = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        idx_mejor = similitudes.argmax()
        score = round(float(similitudes[idx_mejor]), 4)
        
        # Con N-Grams, el score suele ser más preciso pero más bajo
        if score > 0.12: 
            return self.metadata[idx_mejor], score
        
        return {"contenido": "No encontré información específica en el archivo histórico."}, 0.0 