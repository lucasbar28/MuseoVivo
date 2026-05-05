import collections
import math
import numpy as np
from modules.db import BaseDatos # Necesario para cargar el conocimiento

class ModeloNgramas:
    def __init__(self, n=2, k=0.1):
        self.n = n  
        self.k = k  
        self.counts = collections.defaultdict(collections.Counter)
        self.context_counts = collections.defaultdict(int)
        self.vocabulario = set()
        
        # Cargamos los datos de Chascomús automáticamente al inicializar
        self.entrenar_desde_db(BaseDatos())

    def entrenar_desde_db(self, db_instancia):
        """Carga el texto de la DB y entrena el modelo."""
        try:
            db_instancia.cursor.execute("SELECT contenido FROM conocimiento")
            filas = db_instancia.cursor.fetchall()
            
            for (contenido,) in filas:
                # Tokenización simple para entrenamiento
                tokens = contenido.lower().split()
                self.entrenar(tokens)
        except Exception as e:
            print(f"⚠️ Error al entrenar n-gramas: {e}")

    def entrenar(self, corpus_tokens):
        """Entrena el modelo a partir de los tokens del corpus."""
        for i in range(len(corpus_tokens) - self.n + 1):
            contexto = tuple(corpus_tokens[i:i+self.n-1])
            siguiente = corpus_tokens[i+self.n-1]
            self.counts[contexto][siguiente] += 1
            self.context_counts[contexto] += 1
            self.vocabulario.add(siguiente)

    def obtener_probabilidad(self, palabra, contexto):
        """Calcula P(w|contexto) con protección contra división por cero."""
        contexto = tuple(contexto)
        count_secuencia = self.counts[contexto][palabra]
        count_contexto = self.context_counts[contexto]
        
        # PROTECCIÓN: Si el vocabulario está vacío, usamos 1 para evitar ZeroDivisionError
        tam_vocab = max(len(self.vocabulario), 1)
        
        # Fórmula: (count + k) / (total_contexto + k * tamaño_vocabulario)
        denominador = count_contexto + (self.k * tam_vocab)
        prob = (count_secuencia + self.k) / denominador
        return prob

    def calcular_perplejidad(self, texto):
        """Mide la coherencia. Acepta string (desde app.py) o lista."""
        # Convertimos a tokens si llega como string directo del ASR
        tokens = texto.lower().split() if isinstance(texto, str) else texto
        
        if not tokens or len(tokens) < self.n: 
            return 999.0 # Perplejidad alta para entradas inválidas
        
        log_prob_total = 0
        for i in range(len(tokens) - self.n + 1):
            contexto = tokens[i:i+self.n-1]
            palabra = tokens[i+self.n-1]
            prob = self.obtener_probabilidad(palabra, contexto)
            log_prob_total += math.log2(prob)
        
        avg_log_prob = log_prob_total / (len(tokens) - self.n + 1)
        return round(math.pow(2, -avg_log_prob), 2)

    def validar_coherencia(self, texto, umbral=150.0):
        """Detecta si la consulta es 'ruido'."""
        pp = self.calcular_perplejidad(texto)
        return {"es_coherente": pp < umbral, "perplejidad": pp} 