import sqlite3
import os

class BaseDatos:
    def __init__(self, db_path="data/database.sqlite"):
        if not os.path.exists("data"):
            os.makedirs("data")
            
        self.db_path = db_path
        self.conectar()
        self.crear_tablas()

    def conectar(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def crear_tablas(self):
        # 1. Tabla de Conocimiento
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conocimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                contenido TEXT,
                fuente TEXT,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Tabla de Historial (Métricas individuales)
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
        
        # 3. Tabla de Métricas (Datos agregados)
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

    def contar_documentos(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM conocimiento")
            resultado = self.cursor.fetchone()
            return resultado[0] if resultado else 0
        except Exception as e:
            print(f"❌ Error al contar documentos: {e}")
            return 0

    # --- CAMBIO IMPORTANTE: Ahora acepta wer_val ---
    def guardar_interaccion(self, pregunta, score, pp, tiempo, wer_val=0.0):
        """Registra todas las métricas, incluyendo el WER."""
        try:
            tiempo_ms = int(tiempo * 1000)
            query = """
                INSERT INTO historial (texto_transcripto, score_similitud, perplejidad, tiempo_ms, wer)
                VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (pregunta, score, pp, tiempo_ms, wer_val))
            self.conn.commit()
            print(f"✅ Interacción registrada (PP: {pp:.2f}, WER: {wer_val:.2f})")
        except Exception as e:
            print(f"❌ Error al guardar en historial: {e}")

    def registrar_feedback(self, pregunta, valor):
        try:
            query = """
                UPDATE historial 
                SET feedback = ? 
                WHERE id = (SELECT MAX(id) FROM historial WHERE texto_transcripto = ?)
            """
            self.cursor.execute(query, (valor, pregunta))
            self.conn.commit()
            print(f"🗳️ Feedback registrado ({valor})")
        except Exception as e:
            print(f"❌ Error al registrar feedback: {e}")

    def insertar_documento(self, titulo, contenido, fuente):
        self.cursor.execute(
            "INSERT INTO conocimiento (titulo, contenido, fuente) VALUES (?, ?, ?)",
            (titulo, contenido, fuente)
        )
        self.conn.commit()

    def cerrar(self):
        self.conn.close() 