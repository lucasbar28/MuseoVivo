"""
scraping_chascomus.py
─────────────────────────────────────────────────────────────────────────────
Pipeline completo de construcción del corpus para MuseoVivo Chascomús.

Flujo por URL:
  1. Descarga con rotación de User-Agent y pausa anti-429
  2. Limpieza del HTML (elimina nav, footer, scripts)
  3. Guarda el .txt en data/corpus/  (respaldo en disco)
  4. Inserta directamente en la tabla 'conocimiento' de la SQLite
     → Evita el paso manual intermedio de carga

Uso:
  python scraping_chascomus.py           # interactivo (Enter por URL)
  python scraping_chascomus.py --auto    # sin confirmaciones (modo headless)
  python scraping_chascomus.py --db-only # solo recarga a DB los .txt ya guardados
"""

import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import random
import sqlite3
from urllib.parse import urlparse

# ─── Rutas ────────────────────────────────────────────────────────────────────
CORPUS_PATH = "data/corpus/"
DB_PATH     = "data/database.sqlite"
os.makedirs(CORPUS_PATH, exist_ok=True)

# ─── URLs del proyecto ────────────────────────────────────────────────────────
urls_proyecto = [
    "https://guiachascomus.com.ar/alojamientos-chascomus/",
    "https://guiachascomus.com.ar/guia-de-comercios-y-servicios/gastronomia/",
    "https://guiachascomus.com.ar/guia-de-comercios-y-servicios/regionales/",
    "https://guiachascomus.com.ar/guia-de-comercios-y-servicios/tiendas-comercios/",
    "https://guiachascomus.com.ar/guia-de-comercios-y-servicios/aire-libre-diversion/",
    "https://guiachascomus.com.ar/castillo-amistad-chascomus/",
    "https://guiachascomus.com.ar/arquitectura-chascomus/",
    "https://guiachascomus.com.ar/chascomus-capital-del-pejerrey/",
    "https://guiachascomus.com.ar/alfonsin-chascomus/",
    "https://guiachascomus.com.ar/capilla-negros-chascomus/",
    "https://guiachascomus.com.ar/que-hacer-chascomus-con-chicos/",
    "https://guiachascomus.com.ar/semana-santa-chascomus/",
    "https://guiachascomus.com.ar/casa-casco-chascomus/",
    "https://guiachascomus.com.ar/estacion-hidrobiologica-chascomus/",
    "https://guiachascomus.com.ar/historia-chascomus/",
    "https://guiachascomus.com.ar/torii-chascomus/",
    "https://guiachascomus.com.ar/club-pelota-chascomus/",
    "https://guiachascomus.com.ar/catedral-chascomus/",
    "https://guiachascomus.com.ar/cabanas-chascomus/",
    "https://guiachascomus.com.ar/reloj-italianos-chascomus/",
    "https://guiachascomus.com.ar/conecta-naturaleza-chascomus/",
    "https://guiachascomus.com.ar/actividades-en-pareja-chascomus/",
    "https://guiachascomus.com.ar/10-razones-escapada-chascomus/",
    "https://guiachascomus.com.ar/fiestas-tradicionales-chascomus/",
    "https://guiachascomus.com.ar/bigua-ave-emblema-chascomus/",
    "https://guiachascomus.com.ar/cementerio-protestante-chascomus/",
    "https://guiachascomus.com.ar/laguna-chascomus/",
    "https://guiachascomus.com.ar/vieja-estacion-chascomus/",
    "https://guiachascomus.com.ar/espigon-chascomus-pesca-atardeceres/",
    "https://guiachascomus.com.ar/chascomus-laguna-windsurf/",
    "https://destinochascomus.com/atractivos/",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/123.0.0.0",
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def limpiar_texto(soup):
    """Elimina ruido HTML y devuelve el texto limpio del artículo principal."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
        tag.decompose()
    contenedor = soup.find("article") or soup.find("main") or soup.find("body")
    if not contenedor:
        return ""
    return " ".join(contenedor.get_text(separator=" ").split())


def url_a_nombre_archivo(url, indice):
    """Convierte una URL en un nombre de archivo legible."""
    partes = urlparse(url).path.strip("/").split("/")
    slug   = partes[-1].replace("-", "_") if partes[-1] else "index"
    return f"doc_{indice + 1:02d}_{slug}.txt"


def titulo_desde_slug(slug):
    """Convierte 'capilla-negros-chascomus' en 'Capilla Negros Chascomus'."""
    return slug.replace("-", " ").replace("_", " ").title()


def insertar_en_db(titulo, contenido, fuente):
    """
    Inserta un documento en la tabla 'conocimiento'.
    Evita duplicados por fuente (URL). Devuelve True si insertó, False si era duplicado.
    """
    if not os.path.exists(DB_PATH):
        print(f"  ⚠️  DB no encontrada en {DB_PATH}. Ejecutá la app al menos una vez.")
        return False

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("SELECT id FROM conocimiento WHERE fuente=?", (fuente,))
    if cur.fetchone():
        conn.close()
        return False   # Duplicado

    cur.execute(
        "INSERT INTO conocimiento (titulo, contenido, fuente) VALUES (?, ?, ?)",
        (titulo, contenido, fuente)
    )
    conn.commit()
    conn.close()
    return True


def procesar_url(url, indice, modo_auto=False):
    """
    Descarga, limpia, guarda en disco e inserta en DB una URL.
    Devuelve un dict con el resultado del procesamiento.
    """
    nombre_archivo = url_a_nombre_archivo(url, indice)
    ruta_txt       = os.path.join(CORPUS_PATH, nombre_archivo)

    # Slug para título legible
    partes = urlparse(url).path.strip("/").split("/")
    slug   = partes[-1] if partes[-1] else partes[0] if partes else "pagina"
    titulo = titulo_desde_slug(slug)

    print(f"\n[{indice + 1:02d}/{len(urls_proyecto)}] {url}")

    if not modo_auto:
        input("  → Presioná Enter para descargar...")

    try:
        headers  = {"User-Agent": random.choice(USER_AGENTS)}
        delay    = random.uniform(2.0, 4.5)
        time.sleep(delay)

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 429:
            print("  ❌ ERROR 429: Servidor bloqueó la petición.")
            print("     Sugerencia: esperá 2 minutos o cambiá de red.")
            return {"url": url, "estado": "bloqueado_429", "archivo": None}

        response.raise_for_status()
        soup  = BeautifulSoup(response.text, "html.parser")
        texto = limpiar_texto(soup)

        if len(texto) < 100:
            print(f"  ⚠️  Contenido demasiado corto ({len(texto)} chars). Salteando.")
            return {"url": url, "estado": "contenido_vacio", "archivo": None}

        # 1. Guardar .txt en disco (respaldo)
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(f"FUENTE: {url}\nTITULO: {titulo}\n\n{texto}")
        print(f"  💾 TXT guardado: {nombre_archivo}")

        # 2. Insertar en DB directamente
        insertado = insertar_en_db(titulo, texto, url)
        if insertado:
            print(f"  ✅ DB: documento '{titulo}' insertado.")
        else:
            print(f"  ♻️  DB: '{titulo}' ya existía (duplicado salteado).")

        return {
            "url":      url,
            "estado":   "ok",
            "archivo":  nombre_archivo,
            "titulo":   titulo,
            "chars":    len(texto),
            "db":       "insertado" if insertado else "duplicado",
        }

    except requests.exceptions.ConnectionError:
        print(f"  ❌ Sin conexión a {url}")
        return {"url": url, "estado": "sin_conexion", "archivo": None}
    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")
        return {"url": url, "estado": f"error: {e}", "archivo": None}


def modo_db_only():
    """
    Re-carga a la DB todos los .txt que ya están en data/corpus/
    sin volver a descargar nada de internet.
    Útil si la DB se resetea pero el corpus en disco sigue intacto.
    """
    archivos = sorted(f for f in os.listdir(CORPUS_PATH) if f.endswith(".txt"))
    if not archivos:
        print("⚠️  No hay archivos .txt en data/corpus/. Ejecutá el scraping primero.")
        return

    print(f"📂 Recargando {len(archivos)} archivos desde disco a DB...\n")
    insertados = duplicados = errores = 0

    for nombre in archivos:
        ruta = os.path.join(CORPUS_PATH, nombre)
        try:
            with open(ruta, encoding="utf-8") as f:
                lineas = f.read().splitlines()

            # Extraer FUENTE y TITULO del encabezado
            fuente = titulo = ""
            cuerpo_inicio = 0
            for i, linea in enumerate(lineas):
                if linea.startswith("FUENTE:"):
                    fuente = linea.replace("FUENTE:", "").strip()
                elif linea.startswith("TITULO:"):
                    titulo = linea.replace("TITULO:", "").strip()
                elif linea.strip() == "" and fuente:
                    cuerpo_inicio = i + 1
                    break

            contenido = "\n".join(lineas[cuerpo_inicio:]).strip()

            if not fuente:
                fuente = nombre   # fallback
            if not titulo:
                titulo = nombre.replace(".txt", "").replace("_", " ").title()

            ok = insertar_en_db(titulo, contenido, fuente)
            if ok:
                print(f"  ✅ {nombre}")
                insertados += 1
            else:
                print(f"  ♻️  {nombre} (duplicado)")
                duplicados += 1
        except Exception as e:
            print(f"  ❌ {nombre}: {e}")
            errores += 1

    print(f"\n📊 Resultado: {insertados} insertados | {duplicados} duplicados | {errores} errores")


def ejecutar_scraping(modo_auto=False):
    """Bucle principal de scraping con reporte final."""
    print("─" * 60)
    print("  MuseoVivo — Pipeline de construcción de corpus")
    print(f"  URLs a procesar: {len(urls_proyecto)}")
    print(f"  Modo: {'automático' if modo_auto else 'interactivo (Enter por URL)'}")
    print("─" * 60)

    resultados = []
    for i, url in enumerate(urls_proyecto):
        res = procesar_url(url, i, modo_auto=modo_auto)
        resultados.append(res)

    # ─── Reporte final ────────────────────────────────────────────────────────
    ok        = [r for r in resultados if r["estado"] == "ok"]
    vacios    = [r for r in resultados if r["estado"] == "contenido_vacio"]
    bloqueados= [r for r in resultados if r["estado"] == "bloqueado_429"]
    errores   = [r for r in resultados if r["estado"] not in ("ok", "contenido_vacio", "bloqueado_429")]

    print("\n" + "═" * 60)
    print("  REPORTE FINAL")
    print("═" * 60)
    print(f"  ✅ Exitosos          : {len(ok)}")
    print(f"  ♻️  Duplicados en DB  : {len([r for r in ok if r.get('db') == 'duplicado'])}")
    print(f"  ⚠️  Contenido vacío   : {len(vacios)}")
    print(f"  🚫 Bloqueados (429)  : {len(bloqueados)}")
    print(f"  ❌ Errores           : {len(errores)}")
    print(f"  📁 Corpus en disco   : {CORPUS_PATH}")
    print(f"  🗄️  DB actualizada    : {DB_PATH}")
    print("═" * 60)

    if bloqueados:
        print("\n⚠️  URLs bloqueadas — reintentá más tarde:")
        for r in bloqueados:
            print(f"   - {r['url']}")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--db-only" in args:
        modo_db_only()
    else:
        modo_auto = "--auto" in args
        ejecutar_scraping(modo_auto=modo_auto)