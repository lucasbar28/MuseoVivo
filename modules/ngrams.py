import collections
import math
from modules.db import BaseDatos 

class ModeloNgramas:
    def __init__(self, n=2, k=0.1):
        self.n = n  
        self.k = k  
        self.counts = collections.defaultdict(collections.Counter)
        self.context_counts = collections.defaultdict(int)
        self.vocabulario = set()
        
        # Cargamos los datos de Chascomús automáticamente
        db = BaseDatos()
        self.entrenar_desde_db(db)
        db.cerrar() # Importante cerrar la conexión aquí

    def entrenar_desde_db(self, db_instancia):
        """Carga el texto de la DB y entrena el modelo."""
        try:
            db_instancia.cursor.execute("SELECT contenido FROM conocimiento")
            filas = db_instancia.cursor.fetchall()
            
            for (contenido,) in filas:
                # Tokenización más limpia (eliminamos puntuación básica)
                tokens = contenido.lower().replace(".", "").replace(",", "").split()
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
        """Mide la coherencia. Si es una sola palabra, usa Unigramas."""
        tokens = texto.lower().split() if isinstance(texto, str) else texto
        
        if not tokens: 
            return 999.0
        
        # Mejora: Si es una sola palabra y n=2, calculamos probabilidad simple (unigrama)
        # para no devolver siempre 999.0
        if len(tokens) < self.n:
            prob = (tokens[0] in self.vocabulario)
            # Si la palabra existe, damos una PP baja (buena), si no, alta.
            return 50.0 if prob else 500.0

        log_prob_total = 0
        for i in range(len(tokens) - self.n + 1):
            contexto = tokens[i:i+self.n-1]
            palabra = tokens[i+self.n-1]
            prob = self.obtener_probabilidad(palabra, contexto)
            log_prob_total += math.log2(prob)
        
        avg_log_prob = log_prob_total / (len(tokens) - self.n + 1)
        return round(math.pow(2, -avg_log_prob), 2)

    def validar_coherencia(self, texto, umbral=150.0):
        pp = self.calcular_perplejidad(texto)
        return {"es_coherente": pp < umbral, "perplejidad": pp} 