"""
potenciador_corpus.py
─────────────────────────────────────────────────────────────────────────────
Genera pares PREGUNTA → RESPUESTA en lenguaje coloquial bonaerense.
Cada entrada tiene contenido informativo real, NO frases vacías.

Propósito dual:
  1. Entrenamiento N-gramas: el texto coloquial mejora la cobertura de vocabulario
     conversacional sin corromper las tablas de transición (las respuestas tienen
     densidad semántica real).
  2. Corpus TF-IDF: se guarda como documento con título, contenido y fuente
     para que el motor de búsqueda lo indexe correctamente.

⚠️  Este script NO reemplaza el scraping real — lo complementa con frases
    que el turista real usa y que no aparecen en los textos históricos formales.
"""

import random
import os
import sys
import sqlite3

# ─── Rutas ────────────────────────────────────────────────────────────────────
OUTPUT_CORPUS = "data/corpus/doc_potenciador_coloquial.txt"
DB_PATH       = "data/database.sqlite"
os.makedirs(os.path.dirname(OUTPUT_CORPUS), exist_ok=True)

# ─── Base de conocimiento real (pares entidad → hechos verificables) ──────────
CONOCIMIENTO = {
    "Capilla de los Negros": {
        "hechos": [
            "fue construida en 1862 por la comunidad afrodescendiente de Chascomús",
            "tiene pisos de tierra originales que se conservan hasta hoy",
            "es el único testimonio vivo de la presencia africana en la provincia de Buenos Aires",
            "cada año se celebra allí una misa en honor a San Baltasar",
            "está ubicada en el camino a Lezama, a pocos kilómetros del centro",
        ],
        "tags": "historia afrodescendiente patrimonio capilla",
    },
    "Casa de Casco": {
        "hechos": [
            "fue construida por Vicente Casco tras sobrevivir un ataque de malones",
            "sus paredes tienen casi un metro de ancho, construidas en adobe para resistir ataques",
            "es uno de los edificios coloniales mejor conservados de la región pampeana",
            "funciona como museo y se puede visitar de martes a domingo",
            "guarda documentos y objetos personales de la familia Casco del siglo XIX",
        ],
        "tags": "historia colonial museo casa adobe",
    },
    "Museo Pampeano": {
        "hechos": [
            "fue fundado en 1939 y es uno de los museos más antiguos de la provincia",
            "alberga la colección de platería criolla más importante de Buenos Aires",
            "tiene una sala dedicada a Raúl Alfonsín con objetos personales del expresidente",
            "exhibe boleadoras, rastras y aperos de la época gaucha",
            "está ubicado frente a la plaza Independencia en el casco histórico",
        ],
        "tags": "museo historia platería criolla gaucho",
    },
    "Raúl Alfonsín": {
        "hechos": [
            "nació en Chascomús el 12 de marzo de 1927",
            "fue el primer presidente de la democracia recuperada en 1983",
            "solía caminar por la plaza principal sin custodia, como un vecino más",
            "su casa natal en Chascomús está señalizada con una placa histórica",
            "el aeropuerto local lleva su nombre en su honor",
        ],
        "tags": "alfonsín historia democracia presidente político",
    },
    "Laguna de Chascomús": {
        "hechos": [
            "tiene una superficie de 3.000 hectáreas y es la más grande del sistema de lagunas encadenadas",
            "es la capital nacional del pejerrey, el pez más buscado por los pescadores",
            "ofrece actividades de windsurf, kayak y navegación durante todo el año",
            "el espigón es el punto de reunión al atardecer para locales y turistas",
            "el bigúa, un ave buceadora, es el emblema oficial de la ciudad",
        ],
        "tags": "laguna pejerrey pesca naturaleza windsurf",
    },
    "Cervecería Haroldo": {
        "hechos": [
            "es una cervecería artesanal ubicada en el casco histórico de Chascomús",
            "elabora cervezas de estilo inglés y alemán con lúpulo patagónico",
            "tiene una terraza con vista a la plaza Independencia",
            "ofrece maridaje con picadas de embutidos y quesos regionales",
            "es uno de los bares más recomendados por los turistas en Chascomús",
        ],
        "tags": "gastronomía cerveza bar haroldo artesanal",
    },
    "Fuerte San Juan": {
        "hechos": [
            "fue fundado en 1779 como parte de la línea de frontera sur de la colonia",
            "es el origen histórico de la ciudad de Chascomús",
            "protegía las estancias de los ataques de los pueblos originarios de la pampa",
            "de él deriva el nombre del partido: 'Chascomús' en lengua mapuche significa 'agua amarga'",
            "sus restos arqueológicos están integrados al recorrido histórico de la ciudad",
        ],
        "tags": "historia fuerte colonial fundación frontera",
    },
    "Torii de Chascomús": {
        "hechos": [
            "es una réplica del torii del santuario de Miyajima, donada por la colectividad japonesa",
            "está ubicado a orillas de la laguna y es uno de los puntos más fotografiados",
            "fue inaugurado en 1990 como símbolo de la amistad argentino-japonesa",
            "el torii original en Japón emerge del agua; el de Chascomús replica esa imagen al amanecer",
            "es el único torii de estas dimensiones en toda la Argentina",
        ],
        "tags": "torii japón cultura laguna fotografía",
    },
}

# ─── Plantillas de preguntas coloquiales bonaerenses ──────────────────────────
PLANTILLAS_PREGUNTA = [
    "Che, {entidad}, ¿qué onda?",
    "¿Qué me contás de {entidad}?",
    "Decime algo sobre {entidad}.",
    "¿Vale la pena visitar {entidad}?",
    "Contame la historia de {entidad}.",
    "¿Por qué es importante {entidad}?",
    "¿Dónde queda {entidad} y qué tiene de especial?",
    "¿Qué hay para ver en {entidad}?",
    "¿Qué tiene de particular {entidad}?",
    "Me interesa {entidad}, ¿qué sé que no sé?",
]

# ─── Conectores de respuesta para variar el estilo ────────────────────────────
CONECTORES_RESPUESTA = [
    "Mirá, {entidad} es interesante porque",
    "Te cuento: {entidad}",
    "Buena pregunta. {entidad}",
    "Para que tengas una idea, {entidad}",
    "Es un lugar que vale la pena. {entidad}",
]

def generar_respuesta(entidad, datos):
    """Construye una respuesta informativa con 2-3 hechos reales concatenados."""
    hechos_elegidos = random.sample(datos["hechos"], k=min(3, len(datos["hechos"])))
    conector = random.choice(CONECTORES_RESPUESTA).format(entidad=entidad)
    cuerpo = ". Además, ".join(hechos_elegidos) + "."
    return f"{conector} {cuerpo}"

def generar_pares(n_por_entidad=15):
    """Genera n pares pregunta-respuesta por cada entidad del diccionario."""
    pares = []
    for entidad, datos in CONOCIMIENTO.items():
        for _ in range(n_por_entidad):
            pregunta  = random.choice(PLANTILLAS_PREGUNTA).format(entidad=entidad)
            respuesta = generar_respuesta(entidad, datos)
            pares.append({
                "entidad":   entidad,
                "pregunta":  pregunta,
                "respuesta": respuesta,
                "tags":      datos["tags"],
            })
    random.shuffle(pares)
    return pares

def guardar_en_corpus_txt(pares):
    """Escribe el archivo .txt para el lector de corpus manual."""
    with open(OUTPUT_CORPUS, "w", encoding="utf-8") as f:
        f.write("# Corpus coloquial MuseoVivo — generado por potenciador_corpus.py\n")
        f.write("# Formato: PREGUNTA → RESPUESTA (con contenido informativo real)\n\n")
        for p in pares:
            f.write(f"P: {p['pregunta']}\n")
            f.write(f"R: {p['respuesta']}\n")
            f.write(f"TAGS: {p['tags']}\n\n")
    print(f"✅ Corpus TXT guardado en: {OUTPUT_CORPUS} ({len(pares)} pares)")

def cargar_en_db(pares):
    """
    Inserta los pares en la tabla 'conocimiento' de la DB.
    Cada par se guarda como un documento con:
      - titulo  = entidad (ej: 'Capilla de los Negros')
      - contenido = 'P: ... R: ...' (pregunta + respuesta, buscable por TF-IDF)
      - fuente  = 'potenciador_coloquial'
    Evita duplicados comprobando si ya existe un doc con ese título y fuente.
    """
    if not os.path.exists(DB_PATH):
        print(f"⚠️  No se encontró la DB en {DB_PATH}. Ejecutá la app primero para crearla.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    insertados  = 0
    duplicados  = 0

    for p in pares:
        titulo   = f"[Coloquial] {p['entidad']}"
        contenido = f"Pregunta: {p['pregunta']}\nRespuesta: {p['respuesta']}\nEtiquetas: {p['tags']}"
        fuente   = "potenciador_coloquial"

        # Chequeo de duplicado exacto (mismo título + misma fuente)
        cur.execute(
            "SELECT id FROM conocimiento WHERE titulo=? AND fuente=?",
            (titulo, fuente)
        )
        if cur.fetchone():
            duplicados += 1
            continue

        cur.execute(
            "INSERT INTO conocimiento (titulo, contenido, fuente) VALUES (?, ?, ?)",
            (titulo, contenido, fuente)
        )
        insertados += 1

    conn.commit()
    conn.close()
    print(f"✅ DB: {insertados} documentos insertados, {duplicados} duplicados salteados.")

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cargar_db = "--no-db" not in sys.argv

    print(f"🚀 Generando corpus coloquial ({len(CONOCIMIENTO)} entidades)...")
    pares = generar_pares(n_por_entidad=15)   # 8 entidades × 15 = 120 pares

    guardar_en_corpus_txt(pares)

    if cargar_db:
        cargar_en_db(pares)
    else:
        print("ℹ️  Carga a DB salteada (--no-db).")

    print(f"\n📊 Resumen:")
    print(f"   Entidades cubiertas : {len(CONOCIMIENTO)}")
    print(f"   Pares generados     : {len(pares)}")
    print(f"   Archivo TXT         : {OUTPUT_CORPUS}")
    print(f"   DB actualizada      : {'Sí' if cargar_db else 'No'}")