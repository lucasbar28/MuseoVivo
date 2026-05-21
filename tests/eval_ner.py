import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.nlp import NLPProcessor
from modules.db import BaseDatos  # Importamos la base de datos para la automatización

def evaluar_ner():
    nlp = NLPProcessor()
    
    # 20 Oraciones reales con entidades clave que el sistema DEBE rescatar (Requisito de la Rúbrica)
    ejemplos_ner = [
        ("hola sí quería ir a la casa de casco a qué hora abre", ["casa de casco"]),
        ("me dijeron que alfonsín vivía cerca de la plaza", ["alfonsín", "plaza"]),
        ("pasamos por el fuerte san juan y estaba cerrado", ["fuerte san juan"]),
        ("alguien me explica qué es eso del adobe en la capilla", ["adobe", "capilla"]),
        ("queremos probar el pejerrey hoy a la noche", ["pejerrey"]),
        ("cuántos años tiene el museo pampeano", ["museo pampeano"]),
        ("dónde me recomiendan tomar mate en la laguna", ["laguna"]),
        ("a qué hora cierra el casco histórico", ["casco histórico"]),
        ("dónde está el monumento a la democracia", ["democracia"]),
        ("la capilla de los negros cobra entrada", ["capilla de los negros"]),
        ("dónde puedo comer unas buenas empanadas de pescado", ["pescado"]),
        ("se puede entrar a los sótanos de la casa de casco", ["casa de casco", "sótanos"]),
        ("estamos perdidos, dónde queda la plaza independencia", ["plaza independencia"]),
        ("hay réplicas de los blandengues en el museo", ["blandengues", "museo"]),
        ("es verdad que alfonsín caminaba sin custodia", ["alfonsín"]),
        ("dónde se alquilan los botes en la costanera", ["botes", "costanera"]),
        ("a qué distancia está la réplica del fuerte", ["fuerte"]),
        ("queríamos saber el origen de la comunidad afrodescendiente", ["afrodescendiente"]),
        ("la colección de platería criolla es increíble", ["platería criolla"]),
        ("se pesca pejerrey desde el espigón hoy", ["pejerrey", "espigón"])
    ]
    
    aciertos = 0
    total_entidades_esperadas = sum(len(esperadas) for _, esperadas in ejemplos_ner)
    
    print("🧠 Iniciando Test de Extracción (NER)")
    print("-" * 50)
    
    for query, esperadas in ejemplos_ner:
        analisis = nlp.procesar_consulta(query)
        entidades_detectadas = [e['texto'].lower() for e in analisis['entidades']]
        
        # Corrección: Sintaxis correcta de Python (for / if)
        match = [e for e in esperadas if any(e in det for det in entidades_detectadas)]
        aciertos += len(match)
        
        print(f"Query: '{query}'")
        print(f"  Detectó: {entidades_detectadas} | Esperaba: {esperadas}")

    accuracy = aciertos / total_entidades_esperadas if total_entidades_esperadas > 0 else 0
    print("-" * 50)
    print(f"📊 ACCURACY NER: {accuracy*100:.1f}%")
    print(f"Total evaluado: {total_entidades_esperadas} entidades en 20 consultas.")

    # --- GUARDADO AUTOMÁTICO EN LA BASE DE DATOS ---
    try:
        db = BaseDatos()
        db.actualizar_metricas_test(accuracy_ner=accuracy)
        db.cerrar()
        print("💾 Accuracy NER guardado automáticamente en SQLite.")
    except Exception as e:
        print(f"⚠️ Error al intentar guardar las métricas en la base de datos: {e}")

if __name__ == "__main__":
    evaluar_ner()