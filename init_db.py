"""
init_db.py
─────────────────────────────────────────────────────────────────────────────
Inicializador y sincronizador de la base de datos de MuseoVivo.

Modos de uso:
  python init_db.py              # sincroniza corpus → DB (sin duplicados)
  python init_db.py --reset      # borra la DB y la reconstruye desde cero
  python init_db.py --status     # muestra el estado actual sin modificar nada

El script es IDEMPOTENTE: podés ejecutarlo después de cualquier modificación
a los módulos sin riesgo de duplicar documentos en la DB.
"""

import os
import sys
from modules.db import BaseDatos

# ⚠️ Asegurate de que tus .txt limpios estén dentro de esta ruta exacta
CORPUS_DIR = "data/corpus/"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def parsear_encabezado(lineas, nombre_archivo=""):
    """
    Detecta el formato del archivo y extrae (titulo, fuente, inicio_cuerpo).
    """
    fuente = ""
    titulo = ""

    # Detectamos si el archivo tiene encabezado estructurado (primeras 5 líneas)
    tiene_encabezado = any(
        l.strip().startswith("FUENTE:") or l.strip().startswith("TITULO:")
        for l in lineas[:5]
    )

    if tiene_encabezado:
        # ── Formato A o B ─────────────────────────────────────────────────────
        inicio_cuerpo = 0
        for i, linea in enumerate(lineas):
            s = linea.strip()
            if s.startswith("FUENTE:"):
                fuente = s.replace("FUENTE:", "").strip()
            elif s.startswith("TITULO:"):
                titulo = s.replace("TITULO:", "").strip()
            elif s == "" and fuente:
                inicio_cuerpo = i + 1
                break

        if not titulo:
            slug   = fuente.split("/")[-1].replace("-", " ").replace("_", " ").strip()
            titulo = slug.title() if slug else nombre_archivo

        return titulo, fuente or nombre_archivo, inicio_cuerpo

    else:
        # ── Formato C — sin encabezado (archivos manuales) ────────────────────
        primera = lineas[0].strip() if lineas else ""

        # Primera línea corta sin punto final → es el título del doc
        if primera and len(primera) < 80 and not primera.endswith("."):
            titulo        = primera
            inicio_cuerpo = 1
        else:
            # Todo el archivo es cuerpo; título desde nombre de archivo
            slug          = nombre_archivo.replace(".txt", "").replace("_", " ").replace("-", " ")
            titulo        = slug.title()
            inicio_cuerpo = 0

        # La fuente es el nombre del archivo (no hay URL)
        return titulo, nombre_archivo, inicio_cuerpo


def sincronizar_corpus(db):
    """
    Carga todos los .txt del corpus a la DB evitando duplicados.
    """
    if not os.path.exists(CORPUS_DIR):
        print(f"❌ No se encontró la carpeta de corpus en: {CORPUS_DIR}")
        return 0, 0, 0

    archivos = sorted(f for f in os.listdir(CORPUS_DIR) if f.endswith(".txt"))
    total    = len(archivos)

    if total == 0:
        print("⚠️  La carpeta corpus está vacía. Colocá tus archivos .txt limpios allí.")
        return 0, 0, 0

    print(f"\n📂 Sincronizando {total} archivos con la DB...\n")
    insertados = duplicados = errores = 0

    for nombre in archivos:
        # 🛠️ AJUSTE CLAVE: Evitamos cargar las preguntas de prueba de NLP al conocimiento del chatbot
        if "consultas_coloquiales" in nombre.lower() or nombre == "DEV_Test_Consultas_Coloquiales.txt":
            continue

        ruta = os.path.join(CORPUS_DIR, nombre)
        try:
            with open(ruta, encoding="utf-8") as f:
                lineas = f.readlines()

            titulo, fuente, inicio_cuerpo = parsear_encabezado(lineas, nombre)
            contenido = "".join(lineas[inicio_cuerpo:]).strip()

            if len(contenido) < 50:
                print(f"  ⚠️  {nombre}: contenido demasiado corto ({len(contenido)} chars), salteado.")
                errores += 1
                continue

            # Control de duplicados por fuente
            db.cursor.execute(
                "SELECT id FROM conocimiento WHERE fuente=?", (fuente,)
            )
            if db.cursor.fetchone():
                print(f"  ♻️  {nombre}: ya existe en DB (duplicado salteado).")
                duplicados += 1
                continue

            db.insertar_documento(titulo, contenido, fuente)
            print(f"  ✅ {nombre} → '{titulo}' ({len(contenido)} chars)")
            insertados += 1

        except Exception as e:
            print(f"  ❌ {nombre}: error al procesar → {e}")
            errores += 1

    return insertados, duplicados, errores


def mostrar_status(db):
    """Muestra el estado actual de la DB sin modificar nada."""
    try:
        db.cursor.execute("SELECT COUNT(*) FROM conocimiento")
        total = db.cursor.fetchone()[0]

        db.cursor.execute("SELECT fuente, titulo FROM conocimiento ORDER BY id DESC LIMIT 5")
        recientes = db.cursor.fetchall()

        db.cursor.execute("SELECT COUNT(*) FROM historial")
        interacciones = db.cursor.fetchone()[0]

        print(f"\n{'═'*55}")
        print(f"  📊 ESTADO ACTUAL DE LA BASE DE DATOS")
        print(f"{'═'*55}")
        print(f"  Documentos en conocimiento : {total}")
        print(f"  Interacciones registradas  : {interacciones}")
        print(f"\n  Últimos 5 documentos cargados:")
        for fuente, titulo in recientes:
            fuente_corta = fuente[:30] + "..." if len(fuente) > 30 else fuente
            print(f"  Â· {titulo[:45]:<45} ({fuente_corta})")
        print(f"{'═'*55}\n")
    except Exception as e:
        print(f"❌ Error al leer el estado: {e}")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    # Modo --status: solo lectura
    if "--status" in args:
        db = BaseDatos()
        mostrar_status(db)
        db.cerrar()
        sys.exit(0)

    # Modo --reset: borra tabla conocimiento y reconstruye desde cero
    if "--reset" in args:
        confirma = input(
            "⚠️  Esto borrará TODOS los documentos de la tabla 'conocimiento'.\n"
            "   El historial de interacciones se conserva.\n"
            "   ¿Continuar? (s/N): "
        ).strip().lower()

        if confirma != "s":
            print("Operación cancelada.")
            sys.exit(0)

        db = BaseDatos()
        db.cursor.execute("DELETE FROM conocimiento")
        db.conn.commit()
        print("🗑️  Tabla 'conocimiento' vaciada.\n")
    else:
        db = BaseDatos()

    # Sincronización principal
    insertados, duplicados, errores = sincronizar_corpus(db)

    print(f"\n{'─'*45}")
    print(f"  ✅ Insertados  : {insertados}")
    print(f"  ♻️  Duplicados  : {duplicados}  ← ya estaban en DB")
    print(f"  ❌ Errores     : {errores}  ← contenido < 50 chars")
    print(f"{'─'*45}")
    print(f"  Total documentos en DB: {db.contar_documentos()}")
    print(f"{'─'*45}\n")

    if insertados > 0:
        print("💡 Recordá reiniciar la app de Streamlit para que el motor")
        print("   TF-IDF re-entrene con los nuevos documentos.\n")

    db.cerrar() 