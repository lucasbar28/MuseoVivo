"""
tests/eval_search.py
─────────────────────────────────────────────────────────────────────────────
Evaluación del motor de búsqueda TF-IDF (Precisión, Recall, F1).

Mide el rendimiento del motor sobre 10 consultas de prueba con relevancia
etiquetada manualmente. Usa dos umbrales alineados con la app:

  UMBRAL_NIVEL1 = 0.08  → el mismo que app_unificada.py usa para Nivel 1
  UMBRAL_NIVEL2 = 0.04  → el mismo que app_unificada.py usa para Nivel 2

Las métricas se calculan dos veces (con cada umbral) para mostrar
el impacto en P/R/F1 y justificar el umbral elegido en el informe.

Guarda las métricas del umbral principal (Nivel 1) en SQLite.

Uso:
  python tests/eval_search.py
  python tests/eval_search.py --verbose   # muestra scores individuales
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.search import MotorBusqueda
from modules.nlp import NLPProcessor
from modules.db import BaseDatos


# ─── Dataset etiquetado ───────────────────────────────────────────────────────
# Formato: (consulta_coloquial, [palabras_clave_relevantes], descripcion)
# Una recuperación es CORRECTA si:
#   a) el score supera el umbral, Y
#   b) al menos una palabra clave aparece en título o contenido del resultado
CASOS_PRUEBA = [
    (
        "che qué onda esa capilla de barro que está por ahí",
        ["capilla", "negros", "afrodescendiente"],
        "Capilla de los Negros — consulta coloquial con OOV ('barro')"
    ),
    (
        "dónde puedo comer pejerrey fresco cerca del agua",
        ["pejerrey", "pesca", "laguna", "gastronomía"],
        "Gastronomía — pejerrey y laguna"
    ),
    (
        "qué pasó en la casa esa de paredes anchas",
        ["casco", "adobe", "colonial", "vicente"],
        "Casa de Casco — descripción indirecta sin nombre"
    ),
    (
        "hay algún museo para ver cosas de los gauchos",
        ["museo", "pampeano", "platería", "gaucho"],
        "Museo Pampeano — consulta por dominio temático"
    ),
    (
        "contame del monumento del ex presidente que era de acá",
        ["alfonsín", "democracia", "presidente", "monumento"],
        "Alfonsín — referencia indirecta a persona"
    ),
    (
        "estamos buscando un lugar para tomar mate mirando el agua",
        ["laguna", "atardecer", "espigón", "costanera"],
        "Laguna / Costanera — consulta de ambiente/paseo"
    ),
    (
        "quién fue el que construyó el fuerte original de la ciudad",
        ["fuerte", "san juan", "fundación", "frontera"],
        "Fuerte San Juan — consulta histórica sobre fundación"
    ),
    (
        "quiero saber la historia de la iglesia de los africanos",
        ["capilla", "negros", "afrodescendiente", "1862"],
        "Capilla de los Negros — variante con 'iglesia' y 'africanos'"
    ),
    (
        "dónde vivía el presidente que caminaba sin custodia",
        ["alfonsín", "casa", "plaza", "vecino"],
        "Alfonsín — consulta inferencial (sin mencionar el nombre)"
    ),
    (
        "qué artesanías o souvenirs puedo llevar de chascomús",
        ["artesanías", "regional", "tienda", "comercio"],
        "Comercios / Regionales — consulta de compras turísticas"
    ),
]

# ─── Umbrales (alineados con app_unificada.py) ────────────────────────────────
UMBRAL_NIVEL1 = 0.08   # Nivel 1: respuesta con confianza alta
UMBRAL_NIVEL2 = 0.04   # Nivel 2: respuesta con ambigüedad controlada


# ─── Evaluación ───────────────────────────────────────────────────────────────

def evaluar_con_umbral(buscador, nlp, umbral: float, verbose: bool = False):
    """Corre la evaluación completa para un umbral dado. Devuelve (P, R, F1)."""
    aciertos         = 0
    falsos_positivos = 0
    falsos_negativos = 0

    for consulta, palabras_clave, descripcion in CASOS_PRUEBA:
        # Optimizamos la consulta igual que lo hace la app
        analisis = nlp.procesar_consulta(consulta)
        consulta_opt = nlp.optimizar_consulta_tfidf(analisis)

        resultado, score = buscador.buscar_mas_relevante(consulta_opt)
        titulo    = resultado.get("titulo", "").lower()
        contenido = resultado.get("contenido", "").lower()
        texto     = titulo + " " + contenido

        relevante = any(p.lower() in texto for p in palabras_clave)

        if score >= umbral:
            if relevante:
                aciertos += 1
                if verbose:
                    print(f"  ✅ ({score*100:.1f}%) {descripcion}")
                    print(f"     → '{resultado.get('titulo')}'")
            else:
                falsos_positivos += 1
                if verbose:
                    print(f"  ❌ FP ({score*100:.1f}%) {descripcion}")
                    print(f"     → Trajo: '{resultado.get('titulo')}' (irrelevante)")
        else:
            falsos_negativos += 1
            if verbose:
                print(f"  ⚠️  FN ({score*100:.1f}%) {descripcion}")
                print(f"     → Score bajo, no superó umbral {umbral}")

    precision = aciertos / (aciertos + falsos_positivos) if (aciertos + falsos_positivos) > 0 else 0
    recall    = aciertos / len(CASOS_PRUEBA)
    f1        = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1, aciertos, falsos_positivos, falsos_negativos


def evaluar_busqueda(verbose: bool = False):
    buscador = MotorBusqueda()
    nlp      = NLPProcessor()

    print("🔍 Evaluación P/R/F1 — Motor TF-IDF")
    print("=" * 60)
    print(f"  Consultas evaluadas : {len(CASOS_PRUEBA)}")
    print(f"  Optimización NLP    : activada (Query Boosting)")
    print("=" * 60)

    # ── Evaluación con umbral Nivel 1 (principal) ─────────────────────────────
    print(f"\n▶ Umbral Nivel 1 (score ≥ {UMBRAL_NIVEL1}) — Confianza alta")
    if verbose:
        print()
    p1, r1, f1_1, ok1, fp1, fn1 = evaluar_con_umbral(buscador, nlp, UMBRAL_NIVEL1, verbose)

    print(f"\n  Aciertos          : {ok1}")
    print(f"  Falsos positivos  : {fp1}")
    print(f"  Falsos negativos  : {fn1}")
    print(f"  Precisión         : {p1:.3f} ({p1*100:.1f}%)")
    print(f"  Recall            : {r1:.3f} ({r1*100:.1f}%)")
    print(f"  F1-Score          : {f1_1:.3f} ({f1_1*100:.1f}%)")

    # ── Evaluación con umbral Nivel 2 (comparativo) ───────────────────────────
    print(f"\n▶ Umbral Nivel 2 (score ≥ {UMBRAL_NIVEL2}) — Ambigüedad controlada")
    p2, r2, f1_2, ok2, fp2, fn2 = evaluar_con_umbral(buscador, nlp, UMBRAL_NIVEL2, False)

    print(f"\n  Aciertos          : {ok2}")
    print(f"  Falsos positivos  : {fp2}")
    print(f"  Falsos negativos  : {fn2}")
    print(f"  Precisión         : {p2:.3f} ({p2*100:.1f}%)")
    print(f"  Recall            : {r2:.3f} ({r2*100:.1f}%)")
    print(f"  F1-Score          : {f1_2:.3f} ({f1_2*100:.1f}%)")

    print("\n" + "=" * 60)
    print("📊 RESUMEN COMPARATIVO DE UMBRALES")
    print("=" * 60)
    print(f"  {'Métrica':<20} {'Nivel 1 (≥0.08)':>16} {'Nivel 2 (≥0.04)':>16}")
    print(f"  {'─'*20} {'─'*16} {'─'*16}")
    print(f"  {'Precisión':<20} {p1*100:>15.1f}% {p2*100:>15.1f}%")
    print(f"  {'Recall':<20} {r1*100:>15.1f}% {r2*100:>15.1f}%")
    print(f"  {'F1-Score':<20} {f1_1*100:>15.1f}% {f1_2*100:>15.1f}%")
    print("─" * 60)
    print("  Las métricas del Nivel 1 son las que se reportan en la")
    print("  rúbrica y se guardan en el dashboard.")
    print("=" * 60)

    # ─── Guardado en DB ───────────────────────────────────────────────────────
    try:
        db = BaseDatos()
        db.actualizar_metricas_test(precision=p1, recall=r1, f1=f1_1)
        db.cerrar()
        print(f"\n💾 Métricas Nivel 1 guardadas en SQLite.")
    except Exception as e:
        print(f"\n⚠️  No se pudo guardar en DB: {e}")

    return p1, r1, f1_1


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    verbose = "--verbose" in sys.argv
    evaluar_busqueda(verbose=verbose)