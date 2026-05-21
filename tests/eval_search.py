import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.search import MotorBusqueda
from modules.db import BaseDatos  # Importamos la base de datos para automatizar el guardado

def evaluar_busqueda():
    buscador = MotorBusqueda()
    
    # Bajamos el umbral a 0.04 (el Nivel 2 de nuestra app) para evitar falsos negativos en queries coloquiales
    UMBRAL_TEST = 0.04 
    
    # Query vs Palabras clave que DEBEN estar en el documento encontrado
    casos_prueba = [
        ("che qué onda esa capilla de barro que está por ahí", ["capilla", "negros", "doc 10"]),
        ("dónde puedo comer pejerrey fresco", ["pejerrey", "gastronomía", "pesca", "espigón"]),
        ("qué pasó en la casa esa de paredes anchas", ["casa", "casco", "doc 33"]),
        ("hay algún museo para ver cosas de los gauchos", ["museo", "pampeano", "gauchos"]),
        ("contame del monumento del ex presidente", ["alfonsín", "monumento", "democracia"]),
        ("estamos buscando un lugar para tomar mate mirando el agua", ["laguna", "atardecer", "espigon"]),
        ("quién fue el que construyó el fuerte", ["fuerte", "san juan", "bautista"]),
        ("quiero saber la historia de la iglesia de los africanos", ["capilla", "negros", "afrodescendiente"]),
        ("dónde vivía alfonsín", ["alfonsín", "casa"])
    ]
    
    aciertos = 0
    falsos_positivos = 0
    falsos_negativos = 0
    
    print("🔍 Iniciando Test de Estrés: Motor de Búsqueda (TF-IDF)")
    print("-" * 50)
    
    for query, palabras_clave in casos_prueba:
        resultado, score = buscador.buscar_mas_relevante(query)
        titulo = resultado.get('titulo', '').lower()
        contenido = resultado.get('contenido', '').lower()
        texto_completo = titulo + " " + contenido
        
        # Es un acierto si el score supera el umbral Y el documento trae la info correcta
        es_acierto = any(p in texto_completo for p in palabras_clave)
        
        if score >= UMBRAL_TEST:
            if es_acierto:
                aciertos += 1
                print(f"✅ ÉXITO | Query: '{query}' -> Doc: {resultado.get('titulo')} (Score: {score*100:.1f}%)")
            else:
                falsos_positivos += 1
                print(f"❌ FALSO POSITIVO | Query: '{query}' -> Trajo info irrelevante: {resultado.get('titulo')}")
        else:
            falsos_negativos += 1
            print(f"⚠️ FALSO NEGATIVO | Query: '{query}' -> Score muy bajo ({score*100:.1f}%)")

    precision = aciertos / (aciertos + falsos_positivos) if (aciertos + falsos_positivos) > 0 else 0
    recall = aciertos / len(casos_prueba)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("-" * 50)
    print(f"📊 RESULTADOS FINALES BÚSQUEDA")
    print(f"Precisión: {precision:.2f}")
    print(f"Recall:    {recall:.2f}")
    print(f"F1-Score:  {f1:.2f}")

    # --- GUARDADO AUTOMÁTICO EN LA BASE DE DATOS ---
    try:
        db = BaseDatos()
        db.actualizar_metricas_test(precision=precision, recall=recall, f1=f1)
        db.cerrar()
        print("💾 Métricas de búsqueda guardadas automáticamente en SQLite.")
    except Exception as e:
        print(f"⚠️ Error al intentar guardar las métricas en la base de datos: {e}")

if __name__ == "__main__":
    evaluar_busqueda()