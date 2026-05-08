import spacy
from spacy.matcher import PhraseMatcher

class NLPProcessor:
    def __init__(self):
        # 1. Carga del modelo de lenguaje
        try:
            self.nlp = spacy.load("es_core_news_sm")
        except OSError:
            import os
            os.system("python -m spacy download es_core_news_sm")
            self.nlp = spacy.load("es_core_news_sm")
        
        # 2. Refuerzo Semántico para Chascomús
        # Esto garantiza que palabras clave sueltas se detecten siempre como entidades
        self.matcher = PhraseMatcher(self.nlp.vocab)
        lugares_clave = [
            "Casco", "Casa de Casco", "Laguna", "Laguna de Chascomús", 
            "Capilla", "Capilla de los Negros", "Catedral", "Brazzola", 
            "Teatro Brazzola", "Museo", "Pampero", "Club de Regatas"
        ]
        patterns = [self.nlp.make_doc(texto) for texto in lugares_clave]
        self.matcher.add("LUGAR_CHASCOMUS", patterns)

        # 3. Diccionario de Intenciones
        self.intenciones = {
            "historia": ["cuéntame", "historia", "pasó", "quién", "fundó", "origen", "contame"],
            "ubicación": ["dónde", "queda", "llegar", "ubicación", "dirección", "donde"],
            "información": ["qué es", "precio", "entrada", "horario", "abierto", "que es"]
        }

    def extraer_entidades(self, texto):
        """
        Reconocimiento de entidades (NER) híbrido: 
        Combina el modelo estadístico de spaCy con un buscador de frases exactas.
        """
        doc = self.nlp(texto)
        entidades = []
        
        # A. Detección por modelo estadístico (spaCy estándar)
        for ent in doc.ents:
            label = ent.label_
            if label == "LOC": label = "MONUMENTO_LUGAR"
            if label == "PER": label = "PERSONAJE_HISTORICO"
            if label == "DATE": label = "EPOCA_FECHA"
            entidades.append({"texto": ent.text, "tipo": label})
        
        # B. Detección por Matcher de refuerzo (Chascomús específico)
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            # Solo agregamos si no fue detectado ya por el modelo estándar
            if span.text not in [e["texto"] for e in entidades]:
                entidades.append({"texto": span.text, "tipo": "MONUMENTO_LUGAR"})
        
        return entidades

    def detectar_intencion(self, texto):
        """Clasifica la intención del turista para guiar la respuesta."""
        texto_norm = texto.lower()
        for intencion, palabras in self.intenciones.items():
            if any(p in texto_norm for p in palabras):
                return intencion
        return "general"

    def procesar_consulta(self, texto):
        """Pipeline completo para análisis profundo de la consulta."""
        doc = self.nlp(texto)
        
        # Análisis morfológico (POS Tagging)
        analisis = [
            {
                "token": t.text,
                "lemma": t.lemma_.lower(),
                "pos": t.pos_,
                "es_stop": t.is_stop
            }
            for t in doc
        ]
        
        # Limpieza de tokens para modelos de lenguaje
        tokens_limpios = [t.lemma_.lower() for t in doc if not t.is_stop and not t.is_punct]

        return {
            "texto_original": texto,
            "tokens_limpios": tokens_limpios,
            "analisis_pos": analisis,
            "entidades": self.extraer_entidades(texto),
            "intencion": self.detectar_intencion(texto)
        } 