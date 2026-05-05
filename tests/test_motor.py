import sys
import os

# Parche de rutas para reconocer la carpeta 'modules'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db import BaseDatos
from modules.nlp import NLPProcessor
from modules.search import MotorBusqueda
from modules.ngrams import ModeloNgramas

# 1. Inicialización de componentes
db = BaseDatos()
nlp = NLPProcessor()
motor = MotorBusqueda()
modelo_idioma = ModeloNgramas(n=2, k=0.1) # Bigramas con suavizado Add-k

# 2. Entrenamiento y carga de datos
motor.entrenar_con_db(db)

# Obtenemos todos los lemas de la DB para entrenar el modelo de lenguaje
db.cursor.execute("SELECT contenido FROM conocimiento")
todo_el_texto = " ".join([f[0] for f in db.cursor.fetchall()])
tokens_entrenamiento = nlp.procesar_consulta(todo_el_texto)["tokens_limpios"]
modelo_idioma.entrenar(tokens_entrenamiento)

# 3. Interacción con el Turista
pregunta = "Contame la historia de la Capilla de los Negros"
print(f"\n📢 Turista dice: '{pregunta}'")

# 4. Procesamiento NLP (Bloque 1)
procesado = nlp.procesar_consulta(pregunta)
tokens = procesado["tokens_limpios"]

# 5. Validación de Coherencia (Bloque 2 - Función 2 y 5)
validacion = modelo_idioma.validar_coherencia(tokens)
print(f"📊 Perplejidad (PP): {validacion['perplejidad']}")
print(f"✅ ¿Es coherente?: {'SÍ' if validacion['es_coherente'] else 'NO (Posible ruido)'}")

# 6. Sugerencia de Autocompletado (Bloque 2 - Función 4)
if len(tokens) >= 1:
    contexto_actual = tokens[-1:]
    sugerencias = modelo_idioma.predecir_siguiente(contexto_actual)
    print(f"🔮 Sugerencias para '{contexto_actual[0]}': {[s['palabra'] for s in sugerencias]}")

# 7. Recuperación de Información (Bloque 3)
if validacion['es_coherente']:
    resultados = motor.buscar(tokens)
    if resultados:
        print(f"\n🏛️ Guía MuseoVivo dice: {resultados[0]['contenido'][:250]}...")
        print(f"(Fuente: {resultados[0]['fuente']} | Score RI: {resultados[0]['score']})")
    else:
        print("\n😶 Guía: Entiendo tus palabras, pero no tengo registros sobre ese tema.")
else:
    print("\n🤔 Guía: Perdón, el audio es confuso. ¿Podrías repetirme la pregunta sobre Chascomús?")