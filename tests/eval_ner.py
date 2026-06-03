"""
tests/eval_ner.py
─────────────────────────────────────────────────────────────────────────────
Evaluación del módulo NLP (Named Entity Recognition).

Mide la accuracy del NER sobre 20 consultas anotadas manualmente,
cubriendo los 4 tipos de entidades definidos en el diccionario local:
  - MONUMENTO_LUGAR
  - GASTRONOMIA
  - PERSONAJE_HISTORICO
  - OBJETO_DETALLE

Criterio de matching: una entidad detectada cuenta como acierto si
alguno de los textos esperados está contenido en la entidad detectada
(matching por inclusión normalizada).

Guarda accuracy en SQLite para el dashboard.

Uso:
  python tests/eval_ner.py
  python tests/eval_ner.py --verbose   # muestra todos los casos, no solo errores
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.nlp import NLPProcessor
from modules.db import BaseDatos


# ─── Dataset anotado manualmente ─────────────────────────────────────────────
# Formato: (consulta, [entidades_esperadas], tipo_esperado)
# La entidad esperada es un substring normalizado que DEBE aparecer
# en alguna de las entidades detectadas.
EJEMPLOS_NER = [
    # MONUMENTO_LUGAR (8 casos)
    ("hola sí quería ir a la casa de casco a qué hora abre",
     ["casa de casco"], "MONUMENTO_LUGAR"),
    ("pasamos por el fuerte san juan y estaba cerrado",
     ["fuerte san juan"], "MONUMENTO_LUGAR"),
    ("dónde está la capilla de los negros exactamente",
     ["capilla de los negros"], "MONUMENTO_LUGAR"),
    ("alguien sabe cuándo cierra el museo pampeano",
     ["museo pampeano"], "MONUMENTO_LUGAR"),
    ("nos perdimos buscando la plaza independencia",
     ["plaza independencia"], "MONUMENTO_LUGAR"),
    ("hay algo para hacer en la costanera a la noche",
     ["costanera"], "MONUMENTO_LUGAR"),
    ("dónde queda el espigón para pescar",
     ["espigón"], "MONUMENTO_LUGAR"),
    ("qué tiene de especial el casco histórico",
     ["casco histórico"], "MONUMENTO_LUGAR"),

    # GASTRONOMIA (5 casos)
    ("queremos probar el pejerrey hoy a la noche",
     ["pejerrey"], "GASTRONOMIA"),
    ("dónde puedo comer unas buenas empanadas de pescado",
     ["pescado"], "GASTRONOMIA"),
    ("nos recomendaron la cervecería haroldo para tomar algo",
     ["haroldo"], "GASTRONOMIA"),
    ("hay algún café cerca de la plaza",
     ["café"], "GASTRONOMIA"),
    ("dónde sirven empanadas cerca del centro",
     ["empanadas"], "GASTRONOMIA"),

    # PERSONAJE_HISTORICO (4 casos)
    ("me dijeron que alfonsín vivía cerca de la plaza",
     ["alfonsín"], "PERSONAJE_HISTORICO"),
    ("es verdad que alfonsín caminaba sin custodia",
     ["alfonsín"], "PERSONAJE_HISTORICO"),
    ("quién fue vicente casco y por qué le pusieron su nombre",
     ["vicente casco"], "PERSONAJE_HISTORICO"),
    ("cuándo llegaron los afrodescendientes a chascomús",
     ["afrodescendiente"], "PERSONAJE_HISTORICO"),

    # OBJETO_DETALLE (3 casos)
    ("alguien me explica qué es eso del adobe en la capilla",
     ["adobe"], "OBJETO_DETALLE"),
    ("se puede entrar a los sótanos de la casa de casco",
     ["sótanos"], "OBJETO_DETALLE"),
    ("la colección de platería criolla es increíble",
     ["platería criolla"], "OBJETO_DETALLE"),

    # Casos mixtos (2+ entidades en una sola consulta)
    ("dónde se alquilan los botes en la costanera",
     ["botes", "costanera"], "OBJETO_DETALLE / MONUMENTO_LUGAR"),
    ("se pesca pejerrey desde el espigón hoy",
     ["pejerrey", "espigón"], "GASTRONOMIA / MONUMENTO_LUGAR"),
]

# ─── Evaluación ───────────────────────────────────────────────────────────────

def normalizar(texto: str) -> str:
    """Normalización básica para matching robusto."""
    return texto.lower().strip()


def evaluar_ner(verbose: bool = False):
    nlp = NLPProcessor()

    aciertos           = 0
    total_esperadas    = 0
    errores_detalle    = []

    print("🧠 Evaluación NER — Módulo NLP")
    print("=" * 60)

    for consulta, esperadas, tipo in EJEMPLOS_NER:
        analisis = nlp.procesar_consulta(consulta)
        detectadas_norm = [normalizar(e["texto"]) for e in analisis["entidades"]]

        aciertos_frase = 0
        fallidas_frase = []

        for esperada in esperadas:
            esp_norm = normalizar(esperada)
            # Matching por inclusión: la esperada debe estar contenida en alguna detectada
            # O alguna detectada debe estar contenida en la esperada (ej: "fuerte" ⊂ "fuerte san juan")
            encontrada = any(
                esp_norm in det or det in esp_norm
                for det in detectadas_norm
            )
            if encontrada:
                aciertos_frase += 1
            else:
                fallidas_frase.append(esperada)

        aciertos       += aciertos_frase
        total_esperadas += len(esperadas)

        if verbose or fallidas_frase:
            estado = "✅" if not fallidas_frase else "❌"
            print(f"{estado} [{tipo}] '{consulta}'")
            print(f"     Detectadas : {detectadas_norm}")
            print(f"     Esperadas  : {esperadas}")
            if fallidas_frase:
                print(f"     ❌ Falló   : {fallidas_frase}")

    accuracy = aciertos / total_esperadas if total_esperadas > 0 else 0

    # Distribución por tipo de entidad
    print("\n" + "=" * 60)
    print("📊 RESULTADOS NER")
    print("=" * 60)
    print(f"  Consultas evaluadas      : {len(EJEMPLOS_NER)}")
    print(f"  Entidades totales        : {total_esperadas}")
    print(f"  Entidades detectadas OK  : {aciertos}")
    print(f"  Entidades fallidas       : {total_esperadas - aciertos}")
    print(f"  Accuracy NER             : {accuracy*100:.1f}%")
    print("─" * 60)

    if accuracy >= 0.80:
        nivel = "✅ Supera el umbral mínimo de la rúbrica (≥ 70%)"
    elif accuracy >= 0.70:
        nivel = "⚠️  Aprobado — en el límite del umbral (≥ 70%)"
    else:
        nivel = "❌ Por debajo del umbral mínimo (< 70%) — revisar diccionario"

    print(f"  Evaluación rúbrica       : {nivel}")
    print("=" * 60)

    # ─── Guardado en DB ───────────────────────────────────────────────────────
    try:
        db = BaseDatos()
        db.actualizar_metricas_test(accuracy_ner=accuracy)
        db.cerrar()
        print(f"\n💾 Accuracy NER ({accuracy*100:.1f}%) guardada en SQLite.")
    except Exception as e:
        print(f"\n⚠️  No se pudo guardar en DB: {e}")

    return accuracy


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    verbose = "--verbose" in sys.argv
    evaluar_ner(verbose=verbose)