# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar modelo de spaCy (obligatorio)
python -m spacy download es_core_news_sm

# 4. Inicializar la base de datos
python init_db.py

# 5. Correr la app
streamlit run app_unificada.py