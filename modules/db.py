import sqlite3
import os

class BaseDatos:
    def __init__(self, db_path="data/database.sqlite"):
        # Aseguramos que la carpeta data exista para evitar errores de conexión
        if not os.path.exists("data"):
            os.makedirs("data")
            
        self.db_path = db_path
        self.conectar()
        self.crear_tablas()

    def conectar(self):
        """Establece la conexión con el archivo SQLite."""
        # check_same_thread=False es vital para que Streamlit no bloquee la DB
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def crear_tablas(self):
        """Crea las 3 tablas obligatorias según los requisitos del proyecto."""
        # 1. Tabla de Conocimiento: Almacena los textos del corpus
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conocimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                contenido TEXT,
                fuente TEXT,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Tabla de Historial: Registra cada interacción con el turista
        # Se añade columna 'feedback' (0: sin voto, 1: útil, -1: no útil)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                texto_transcripto TEXT,
                respuesta_sistema TEXT,
                perplejidad REAL,
                wer REAL,
                tiempo_ms INTEGER,
                score_similitud REAL,
                feedback INTEGER DEFAULT 0
            )
        ''')
        
        # 3. Tabla de Métricas: Datos agregados para el Dashboard
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE UNIQUE,
                total_consultas INTEGER DEFAULT 0,
                wer_promedio REAL DEFAULT 0,
                pp_promedio REAL DEFAULT 0
            )
        ''')
        self.conn.commit()

    def guardar_interaccion(self, pregunta, score, pp, tiempo):
        """
        MÉTODO REQUERIDO POR app.py:
        Registra la métrica de cada consulta en la tabla historial.
        """
        try:
            # Convertimos el tiempo a milisegundos
            tiempo_ms = int(tiempo * 1000)
            
            query = """
                INSERT INTO historial (texto_transcripto, score_similitud, perplejidad, tiempo_ms)
                VALUES (?, ?, ?, ?)
            """
            self.cursor.execute(query, (pregunta, score, pp, tiempo_ms))
            self.conn.commit()
            print(f"✅ Interacción registrada en Historial (PP: {pp})")
        except Exception as e:
            print(f"❌ Error al guardar en historial: {e}")

    def registrar_feedback(self, pregunta, valor):
        """
        Actualiza el voto (👍/👎) en el último registro que coincida con la pregunta.
        """
        try:
            query = """
                UPDATE historial 
                SET feedback = ? 
                WHERE id = (SELECT MAX(id) FROM historial WHERE texto_transcripto = ?)
            """
            self.cursor.execute(query, (valor, pregunta))
            self.conn.commit()
            print(f"🗳️ Feedback registrado ({valor}) para: {pregunta[:30]}...")
        except Exception as e:
            print(f"❌ Error al registrar feedback: {e}")

    def insertar_documento(self, titulo, contenido, fuente):
        """Inserta un nuevo fragmento de historia en la base de datos."""
        self.cursor.execute(
            "INSERT INTO conocimiento (titulo, contenido, fuente) VALUES (?, ?, ?)",
            (titulo, contenido, fuente)
        )
        self.conn.commit()

    def cerrar(self):
        """Cierra la conexión de forma segura."""
        self.conn.close() 