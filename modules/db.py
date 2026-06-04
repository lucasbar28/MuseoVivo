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

    def guardar_interaccion(self, pregunta, score, pp, tiempo, wer_val=0.0):
        """Registra todas las métricas, incluyendo el WER y devuelve el ID único generado."""
        try:
            tiempo_ms = int(tiempo * 1000)
            query = """
                INSERT INTO historial (texto_transcripto, score_similitud, perplejidad, tiempo_ms, wer)
                VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (pregunta, score, pp, tiempo_ms, wer_val))
            self.conn.commit()
            print(f"✅ Interacción registrada (PP: {pp:.2f}, WER: {wer_val:.2f})")
            return self.cursor.lastrowid  # Retorna el ID autoincremental de la fila insertada
        except Exception as e:
            print(f"❌ Error al guardar en historial: {e}")
            return None

    def registrar_feedback(self, pregunta, valor):
        """Método heredado (Búsqueda por texto plano)."""
        try:
            query = """
                UPDATE historial 
                SET feedback = ? 
                WHERE id = (SELECT MAX(id) FROM historial WHERE texto_transcripto = ?)
            """
            self.cursor.execute(query, (valor, pregunta))
            self.conn.commit()
            print(f"🗳️ Feedback registrado ({valor}) por texto")
        except Exception as e:
            print(f"❌ Error al registrar feedback por texto: {e}")

    def registrar_feedback_por_id(self, interaccion_id, valor):
        """Actualiza la métrica de feedback de forma segura y directa usando el ID numérico."""
        try:
            query = "UPDATE historial SET feedback = ? WHERE id = ?"
            self.cursor.execute(query, (valor, interaccion_id))
            self.conn.commit()
            print(f"🗳️ Feedback registrado ({valor}) para registro ID {interaccion_id}")
        except Exception as e:
            print(f"❌ Error al registrar feedback por ID: {e}")

    def insertar_documento(self, titulo, contenido, fuente):
        self.cursor.execute(
            "INSERT INTO conocimiento (titulo, contenido, fuente) VALUES (?, ?, ?)",
            (titulo, contenido, fuente)
        )
        self.conn.commit()

    def cerrar(self):
        self.conn.close() 

    def actualizar_metricas_test(self, precision=None, recall=None, f1=None, accuracy_ner=None):
        """Guarda automáticamente los resultados de los tests de consola en la BD."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluaciones_tests (
                    id INTEGER PRIMARY KEY, 
                    precision REAL, 
                    recall REAL, 
                    f1 REAL, 
                    accuracy_ner REAL
                )
            """)
            self.cursor.execute("SELECT * FROM evaluaciones_tests WHERE id=1")
            row = self.cursor.fetchone()
            if not row:
                self.cursor.execute("INSERT INTO evaluaciones_tests (id, precision, recall, f1, accuracy_ner) VALUES (1, 0.0, 0.0, 0.0, 0.0)")
                row = (1, 0.0, 0.0, 0.0, 0.0)
                
            p = precision if precision is not None else row[1]
            r = recall if recall is not None else row[2]
            f = f1 if f1 is not None else row[3]
            a = accuracy_ner if accuracy_ner is not None else row[4]
            
            self.cursor.execute("UPDATE evaluaciones_tests SET precision=?, recall=?, f1=?, accuracy_ner=? WHERE id=1", (p, r, f, a))
            self.conn.commit()
        except Exception as e:
            print(f"❌ Error al actualizar métricas de test: {e}")

    def obtener_metricas_test(self):
        """Devuelve los últimos resultados al Dashboard."""
        try:
            self.cursor.execute("SELECT precision, recall, f1, accuracy_ner FROM evaluaciones_tests WHERE id=1")
            row = self.cursor.fetchone()
            if row:
                return {"precision": row[0], "recall": row[1], "f1": row[2], "accuracy_ner": row[3]}
        except:
            pass
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "accuracy_ner": 0.0} 