import math
import re
import collections
import unicodedata

class ModeloNgramas:
    def __init__(self, n=2, k=0.5, db_instancia=None):
        """
        Inicializa el modelo de N-gramas (por defecto Bigramas con suavizado de Laplace).
        :param n: Grado del n-grama (2 para bigramas, 3 para trigramas, etc.)
        :param k: Parámetro de suavizado de Laplace (k-smoothing)
        :param db_instancia: Instancia de la base de datos para auto-entrenamiento inmediato
        """
        self.n = n
        self.k = k
        self.counts = collections.defaultdict(collections.Counter)
        self.context_counts = collections.Counter()
        self.vocabulario = set()
        
        # Si se pasa la base de datos, ejecutamos el auto-entrenamiento con el historial existente
        if db_instancia:
            self.entrenar_desde_db(db_instancia)

    def _limpiar_y_tokenizar(self, texto):
        """Sanitiza el texto eliminando puntuación, tildes y fragmentándolo en tokens."""
        if not texto:
            return []
        # Normalizar y remover tildes/acentos gráficos
        texto_bajo = ''.join(
            c for c in unicodedata.normalize('NFD', texto.lower()) 
            if unicodedata.category(c) != 'Mn'
        )
        # Filtrar caracteres no alfanuméricos
        texto_limpio = re.sub(r'[^\w\s]', '', texto_bajo)
        return texto_limpio.split()

    def entrenar(self, corpus_textos):
        """
        Entrena el modelo basándose en una lista de strings.
        :param corpus_textos: Lista de oraciones o párrafos históricos
        """
        self.counts.clear()
        self.context_counts.clear()
        self.vocabulario.clear()

        for texto in corpus_textos:
            tokens = self._limpiar_y_tokenizar(texto)
            if not tokens:
                continue
                
            # Registrar palabras en el universo del vocabulario global
            for token in tokens:
                self.vocabulario.add(token)

            # Insertar tokens de padding según el grado N seleccionado
            tokens_con_padding = ["<inicio>"] * (self.n - 1) + tokens
            
            # Construcción de las ventanas deslizantes de n-gramas
            for i in range(self.n - 1, len(tokens_con_padding)):
                contexto = tuple(tokens_con_padding[i - self.n + 1:i])
                palabra = tokens_con_padding[i]
                
                self.counts[contexto][palabra] += 1
                self.context_counts[contexto] += 1

    def entrenar_desde_db(self, db_instancia):
        """Extrae de forma directa las transcripciones guardadas para ajustar el modelo al léxico real."""
        try:
            query = "SELECT texto_transcripto FROM historial WHERE texto_transcripto IS NOT NULL AND texto_transcripto != ''"
            df = db_instancia.ejecutar_query_df(query)
            if df is not None and not df.empty:
                textos = df['texto_transcripto'].tolist()
                self.entrenar(textos)
        except Exception:
            pass # Resguardo silencioso si la tabla aún se está inicializando

    def obtener_probabilidad(self, palabra, contexto):
        """Calcula la probabilidad condicional P(palabra|contexto) aplicando suavizado de Laplace."""
        contexto = tuple(contexto)
        count_ngram = self.counts[contexto][palabra]
        count_contexto = self.context_counts[contexto]
        
        # Tamaño efectivo del vocabulario para el denominador del suavizado
        tamano_vocabulario = len(self.vocabulario)
        if tamano_vocabulario == 0:
            tamano_vocabulario = 1
            
        # Fórmula matemática estándar de Laplace: (C(w_i, w_{i-1}) + k) / (C(w_{i-1}) + k * |V|)
        prob = (count_ngram + self.k) / (count_contexto + self.k * tamano_vocabulario)
        return prob

    def calcular_perplejidad(self, texto):
        """
        Mide la coherencia gramatical y léxica de una secuencia de palabras.
        A menor perplejidad, mayor coherencia sintáctica respecto al corpus entrenado.
        """
        tokens = self._limpiar_y_tokenizar(texto) if isinstance(texto, str) else texto
        
        if not tokens: 
            return 150.0  # Umbral base por defecto ante entradas vacías
            
        if not self.vocabulario:
            return 100.0  # Fallback seguro si el motor se evalúa sin datos previos
        
        log_prob_total = 0.0
        n_tokens = len(tokens)
        tamano_vocabulario = len(self.vocabulario)
        
        # Padding idéntico al entrenamiento para alinear los contextos de bigramas
        tokens_con_padding = ["<inicio>"] * (self.n - 1) + tokens
        
        # Procesamiento secuencial con ventana deslizante
        for i in range(self.n - 1, len(tokens_con_padding)):
            contexto = tuple(tokens_con_padding[i - self.n + 1:i])
            palabra = tokens_con_padding[i]
            
            # --- DETECCIÓN Y PENALIZACIÓN OPTIMIZADA DE PALABRAS FUERA DE VOCABULARIO (OOV) ---
            if palabra != "<inicio>" and palabra not in self.vocabulario:
                # Se asigna una probabilidad base dinámica acorde al universo léxico actual
                prob = 1.0 / (tamano_vocabulario + 1)
            else:
                prob = self.obtener_probabilidad(palabra, contexto)
            
            # Protección estricta frente a subflujos o indeterminaciones numéricas
            if prob <= 0:
                prob = 1e-5
                
            log_prob_total += math.log2(prob)
        
        # Entropía cruzada promedio: H = -1/N * sum(log2(P))
        entropia_promedio = - (log_prob_total / n_tokens)
        
        # Perplejidad = 2^H
        pp = math.pow(2, entropia_promedio)
        
        # Validación de estabilidad para renderizar en Streamlit de forma segura
        if math.isnan(pp) or math.isinf(pp):
            return 200.0
            
        # Rango máximo extendido a 1000.0 para evaluar correctamente la severidad de las desviaciones
        return round(max(min(pp, 1000.0), 1.0), 2)