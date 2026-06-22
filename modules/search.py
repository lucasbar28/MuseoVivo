import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from modules.db import BaseDatos 

class MotorBusqueda:
    def __init__(self):
        # Implementamos N-gramas (1, 2) para entender conceptos compuestos (ej: "Casa de Casco")
        self.vectorizador = TfidfVectorizer(
            ngram_range=(1, 2), 
            strip_accents='unicode',
            lowercase=True
        )
        self.metadata = [] 
        self.tfidf_matrix = None
        
        # --- MEJORA: Conexión temporal para entrenamiento ---
        db = BaseDatos()
        self.entrenar_con_db(db)
        db.cerrar() # Cerramos para liberar el archivo .sqlite

    def limpiar_texto_historico(self, texto):
        """Elimina metadatos de carga y mejora el formato visual para el usuario."""
        if not texto:
            return ""
            
        # 1. Elimina fechas de sistema (ej: Enero 12, 2024)
        texto = re.sub(r'[a-zA-Záéíóú]+ \d{1,2}, \d{4}', '', texto)
        
        # 2. Corta ruido web común en el corpus
        ruido = ["Deja una respuesta", "Cancelar la respuesta", "También podría gustarte", "Publicado en"]
        for frase in ruido:
            texto = texto.split(frase)[0]
        
        # 3. Reparar puntos pegados ("casa.En") para crear párrafos legibles
        texto = re.sub(r'\.([a-zA-Záéíóú])', r'. \1', texto)
        
        # 4. Formateo de párrafos para Streamlit
        texto = texto.replace(". ", ".\n\n")
        
        return texto.strip()

    def entrenar_con_db(self, db_instancia):
        """Carga el conocimiento y construye el índice TF-IDF con Keyword Boosting."""
        try:
            db_instancia.cursor.execute("SELECT titulo, contenido, fuente FROM conocimiento")
            filas = db_instancia.cursor.fetchall()
            
            if not filas: 
                print("⚠️ Motor: No hay documentos en la DB para entrenar.")
                return

            textos_entrenamiento = []
            self.metadata = []
            
            for f in filas:
                contenido_limpio = self.limpiar_texto_historico(f[1])
                
                # --- KEYWORD BOOSTING OPTIMIZADO (X4) ---
                # Multiplicamos la presencia del título para que los nombres propios 
                # dominen la matriz de similitud frente a cuerpos de texto cortos.
                titulo_boosted = f"{f[0]} " * 4
                textos_entrenamiento.append(f"{titulo_boosted}{contenido_limpio}")
                
                self.metadata.append({
                    "titulo": f[0].replace("_", " ").upper(),
                    "fuente": f[2], 
                    "contenido": contenido_limpio
                })
            
            # Construcción de la matriz dispersa
            self.tfidf_matrix = self.vectorizador.fit_transform(textos_entrenamiento)
            print(f"✅ Motor TF-IDF (N-Grams 1,2) listo con Boosting x4: {len(self.metadata)} documentos.")
            
        except Exception as e:
            print(f"❌ Error entrenamiento: {e}")

    def buscar_mas_relevante(self, consulta_texto):
        """Búsqueda por similitud del coseno entre la consulta y el corpus."""
        if self.tfidf_matrix is None or not consulta_texto:
            return {"contenido": "Error: Motor no disponible"}, 0.0

        # Transformamos la consulta al espacio vectorial del modelo
        query_vector = self.vectorizador.transform([consulta_texto.lower()])
        
        # Calculamos la similitud contra todos los documentos
        similitudes = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Obtenemos el índice del mejor resultado
        idx_mejor = similitudes.argmax()
        score = round(float(similitudes[idx_mejor]), 4)
        
        # --- CONTROL DE SEGURIDAD MÍNIMO ---
        # Si la similitud matemática es exactamente 0.0 (la query no comparte ninguna 
        # palabra con el corpus), devolvemos el fallback genérico directamente.
        if score == 0.0:
            return {"contenido": "No encontré información específica en el archivo histórico de Chascomús."}, 0.0
        
        # --- LIBERACIÓN DE UMBRALES ---
        # Se remueve la regla estricta de 0.12. Delegamos el score real de coma flotante 
        # a app_unificada.py para que ejecute sus propias lógicas de visualización (Niveles 1, 2 y 3).
        return self.metadata[idx_mejor], score 