import spacy
import re
import unicodedata

class NLPProcessor:
    def __init__(self):
        # 1. Carga del modelo de lenguaje (spaCy) de forma segura
        try:
            self.nlp = spacy.load("es_core_news_sm")
        except OSError:
            import os
            os.system("python -m spacy download es_core_news_sm")
            self.nlp = spacy.load("es_core_news_sm")
        
        # 2. Refuerzo Semántico para Chascomús (Diccionario limpio de tildes internamente)
        self.diccionario_local = {
            "MONUMENTO_LUGAR": [
                "casa de casco", "capilla de los negros", "fuerte san juan", 
                "museo pampeano", "laguna", "laguna de chascomus", "casco historico", 
                "plaza independencia", "costanera", "espigon", "catedral", 
                "teatro brazzola", "club de regatas"
            ],
            "PERSONAJE_HISTORICO": [
                "alfonsin", "vicente casco", "blandengues", "afrodescendiente"
            ],
            "GASTRONOMIA": [
                "pejerrey", "pescado", "empanadas", "cafe mule", 
                "haroldo", "cerveceria haroldo", "teofilo", "bach", "franklin"
            ],
            "OBJETO_DETALLE": [
                "adobe", "plateria criolla", "sotanos", "botes", "monumento", "democracia"
            ]
        }

        # 3. Diccionario de Intenciones Originales
        self.intenciones = {
            "historia": ["cuentame", "historia", "paso", "quien", "fundo", "origen", "contame"],
            "ubicacion": ["donde", "queda", "llegar", "ubicacion", "direccion"],
            "informacion": ["que es", "precio", "entrada", "horario", "abierto", "cuanto"]
        }

        # 4. Diccionario de Intenciones Genéricas Mapeadas a Filtros Geo
        self.intenciones_geo = {
            "Gastronomia": [
                "comer", "almorzar", "cenar", "tomar", "desayunar", "merendar",
                "restaurant", "restaurante", "bar", "cafeteria", "cafe", 
                "parrilla", "cerveceria", "bodegon", "hamburguesa"
            ],
            "Historico": [
                "pasear", "caminar", "recorrer", "visitar", "conocer", "pescar", 
                "jugar", "comprar", "artesanias", "regionales", "museo", "plaza", 
                "parque", "laguna", "atractivos", "entretenimiento", "aire libre"
            ]
        }

    def _normalizar_texto(self, texto):
        """Remueve tildes y fuerza minúsculas para un macheo de strings infalible."""
        if not texto:
            return ""
        texto_norm = texto.lower()
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto_norm)
            if unicodedata.category(c) != 'Mn'
        )

    def extraer_entidades(self, texto):
        """Reconocimiento de entidades (NER) híbrido libre de bugs por tildes."""
        doc = self.nlp(texto)
        entidades = []
        texto_norm = self._normalizar_texto(texto)
        textos_ya_detectados = set()

        # A. Detección Local Estricta (Utiliza regex segura para caracteres unicode/tildes)
        for tipo, palabras_clave in self.diccionario_local.items():
            for palabra in palabras_clave:
                # Reemplazamos \b por aserciones de inicio/fin de línea o caracteres no alfanuméricos
                pattern = r'(?:^|[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ])' + re.escape(palabra) + r'(?:$|[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ])'
                if re.search(pattern, texto_norm):
                    entidades.append({"texto": palabra, "tipo": tipo})
                    textos_ya_detectados.add(palabra)
        
        # B. Detección por modelo estadístico (spaCy estándar como red de seguridad)
        for ent in doc.ents:
            ent_norm = self._normalizar_texto(ent.text)
            if ent_norm not in textos_ya_detectados:
                label = ent.label_
                if label == "LOC": label = "MONUMENTO_LUGAR"
                elif label == "PER": label = "PERSONAJE_HISTORICO"
                elif label == "DATE": label = "EPOCA_FECHA"
                
                if label in ["MONUMENTO_LUGAR", "PERSONAJE_HISTORICO", "EPOCA_FECHA"]:
                    entidades.append({"texto": ent.text, "tipo": label})
        
        return entidades

    def detectar_intencion(self, texto):
        """Clasifica la intención ignorando variaciones de tildes."""
        texto_norm = self._normalizar_texto(texto)
        for intencion, palabras in self.intenciones.items():
            if any(p in texto_norm for p in palabras):
                return intencion
        return "general"

    def procesar_consulta(self, texto):
        """Pipeline morfológico y semántico completo."""
        doc = self.nlp(texto)
        
        analisis = [
            {
                "token": t.text,
                "lemma": t.lemma_.lower(),
                "pos": t.pos_,
                "es_stop": t.is_stop
            }
            for t in doc
        ]
        
        tokens_limpios = [t.lemma_.lower() for t in doc if not t.is_stop and not t.is_punct]

        return {
            "texto_original": texto,
            "tokens_limpios": tokens_limpios,
            "analisis_pos": analisis,
            "entidades": self.extraer_entidades(texto),
            "intencion": self.detectar_intencion(texto)
        }

    def optimizar_consulta_tfidf(self, analisis_nlp):
        """Aplica Query Boosting multiplicando los términos clave para el buscador."""
        tokens = analisis_nlp["tokens_limpios"]
        query_base = " ".join(tokens)
        
        entidades = analisis_nlp["entidades"]
        if entidades:
            nombres = " ".join([e["texto"] for e in entidades])
            query_base += f" {nombres} {nombres} {nombres} {nombres}"
            
        return query_base if query_base.strip() else analisis_nlp["texto_original"]
    
    def generar_introduccion_espontanea(self, titulo_documento):
        """Genera una plantilla de respuesta dinámica (corregido el hardcodeo)."""
        import random
        introducciones = [
            f"Qué bueno que preguntes. Encontré esto en el registro sobre **{titulo_documento}**:",
            f"Excelente elección. Te presento los detalles oficiales para **{titulo_documento}**:",
            f"Acá tenés la ficha del patrimonio histórico y comercial de **{titulo_documento}**:",
            f"Sincronizando... Esto es lo que registra el corpus de la ciudad sobre **{titulo_documento}**:"
        ]
        return random.choice(introducciones)

    def evaluar_intencion_geo_generica(self, texto):
        """Determina si la consulta contiene términos genéricos de acción para Haversine."""
        texto_norm = self._normalizar_texto(texto)
        for categoria, palabras in self.intenciones_geo.items():
            if any(p in texto_norm for p in palabras):
                return categoria
        return None 