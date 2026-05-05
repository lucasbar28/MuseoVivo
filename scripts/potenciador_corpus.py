import random
import os

# Definimos los bloques de construcción para las frases
sujetos = ["Contame", "Decime", "Explicame", "¿Me contás?", "¿Sabés", "Quiero saber", "Me interesa"]
conectores = ["sobre", "la historia de", "un poco de", "qué pasó con", "la importancia de"]
lugares = [
    "la Capilla de los Negros", "la Laguna", "Raúl Alfonsín", "la Casa de Casco", 
    "el Castillo de la Amistad", "la Vieja Estación", "el Pejerrey", "el Torii",
    "la Catedral", "los Casco", "el Reloj de los Italianos", "el Club de Pelota"
]
modificadores = ["ahora", "en el pasado", "hoy en día", "por favor", "me interesa mucho", "che"]

# Ruta donde se guardará el archivo (data/corpus/)
output_path = "data/corpus/doc_33_consultas_coloquiales.txt"

# Aseguramos que la carpeta exista
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print("🚀 Generando frases para el corpus...")

with open(output_path, "w", encoding="utf-8") as f:
    # Generamos 1000 variaciones combinando los bloques anteriores
    for _ in range(1000):
        linea = f"{random.choice(sujetos)} {random.choice(conectores)} {random.choice(lugares)} {random.choice(modificadores)}.\n"
        f.write(linea)

print(f"✅ ¡Listo! Se generaron 1000 consultas en: {output_path}")