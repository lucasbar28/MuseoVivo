import collections
import math
import re
from modules.db import BaseDatos 

class ModeloNgramas:
    def __init__(self, n=2, k=0.5): # Subimos k a 0.5 para un suavizado más robusto
        self.n = n  
        self.k = k  
        self.counts = collections.defaultdict(collections.Counter)
        self.context_counts = collections.defaultdict(int)
        self.vocabulario = set()
        
        # Cargamos los datos de Chascomús automáticamente
        db = BaseDatos()
        self.entrenar_desde_db(db)
        db.cerrar() # Importante cerrar la conexión aquí

    def _limpiar_y_tokenizar(self, texto):
        """Unifica la limpieza de texto tanto para entrenamiento como para consulta."""
        if not texto:
            return []
        # Pasamos a minúsculas y removemos puntuación, tildes y signos de expresión
        texto_limpio = texto.lower()
        texto_limpio = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()¿?¡!]', '', texto_limpio)
        return texto_limpio.split()

    def entrenar_desde_db(self, db_instancia):
        """Carga el texto de la DB y entrena el modelo."""
        try:
            db_instancia.cursor.execute("SELECT contenido FROM conocimiento")
            filas = db_instancia.cursor.fetchall()
            
            for (contenido,) in filas:
                tokens = self._limpiar_y_tokenizar(contenido)
                self.entrenar(tokens)
            print(f"📈 N-Grams: Entrenado con {len(self.vocabulario)} palabras únicas.")
        except Exception as e:
            print(f"⚠️ Error al entrenar n-gramas: {e}")

    def entrenar(self, corpus_tokens):
        for i in range(len(corpus_tokens) - self.n + 1):
            contexto = tuple(corpus_tokens[i:i+self.n-1])
            siguiente = corpus_tokens[i+self.n-1]
            self.counts[contexto][siguiente] += 1
            self.context_counts[contexto] += 1
            self.vocabulario.add(siguiente)

    def obtener_probabilidad(self, palabra, contexto):
        contexto = tuple(contexto)
        count_secuencia = self.counts[contexto][palabra]
        count_contexto = self.context_counts[contexto]
        
        tam_vocab = max(len(self.vocabulario), 1)
        denominador = count_contexto + (self.k * tam_vocab)
        return (count_secuencia + self.k) / denominador

    def calcular_perplejidad(self, texto):
        """Mide la coherencia de la secuencia de palabras de forma matemática estable."""
        tokens = self._limpiar_y_tokenizar(texto) if isinstance(texto, str) else texto
        
        if not tokens: 
            return 150.0  # Umbral base por defecto ante vacíos
        
        # Corrección matemática para consultas más cortas que el tamaño del n-grama (ej. unigramas)
        if len(tokens) < self.n:
            palabra = tokens[0]
            if palabra in self.vocabulario:
                # Si la palabra existe en el corpus de Chascomús, calculamos su probabilidad unigrama aproximada
                total_conteos = sum(self.context_counts.values()) or 1
                conteo_palabra = sum(self.counts[ctx][palabra] for ctx in self.counts)
                prob = (conteo_palabra + self.k) / (total_conteos + (self.k * len(self.vocabulario)))
                return round(math.pow(2, -math.log2(prob)), 2)
            else:
                return 180.0 # Penalización controlada pero sana para una palabra OOV sola

        log_prob_total = 0
        N = len(tokens) - self.n + 1
        
        for i in range(N):
            contexto = tokens[i:i+self.n-1]
            palabra = tokens[i+self.n-1]
            prob = self.obtener_probabilidad(palabra, contexto)
            log_prob_total += math.log2(prob)
        
        avg_log_prob = log_prob_total / N
        pp = math.pow(2, -avg_log_prob)
        
        # Evitamos saltos numéricos infinitos o aberrantes en el Dashboard por ruido de audio o palabras OOV
        if math.isnan(pp) or math.isinf(pp):
            return 200.0
            
        return round(min(pp, 350.0), 2) # Seteamos un techo técnico de dispersión

    def validar_coherencia(self, texto, umbral=150.0):
        pp = self.calcular_perplejidad(texto)
        return {"es_coherente": pp < umbral, "perplejidad": pp} 