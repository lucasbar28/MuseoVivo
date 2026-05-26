# [cite_start][ÉPICA] Trabajo Integrador: Técnicas de Procesamiento del Habla [cite: 4, 5]

## Descripción
[cite_start]Diseñar, desarrollar y presentar un producto de software funcional que integre los cuatro bloques de la unidad: Procesamiento del Lenguaje Natural, Modelos de N-gramas, Recuperación de Información y Reconocimiento y Síntesis del Habla[cite: 12]. [cite_start]El producto debe ser una aplicación web con interfaz gráfica, reconocimiento de voz real, persistencia en base de datos SQLite y un dashboard[cite: 13]. [cite_start]No es un ejercicio académico, sino un prototipo funcional orientado a un cliente real[cite: 14].

## 📅 Cronograma y Entregables

### [cite_start]Mes 1: Pipeline funcional (Semanas 1 a 4) [cite: 149]
- [ ] [cite_start]**Semana 1:** Formar el grupo, elegir la opción de proyecto y crear el repositorio Git[cite: 151, 152].
- [ ] [cite_start]**Semana 1:** Recopilar y curar el corpus del dominio (mínimo 50 documentos/relatos/clips)[cite: 153].
- [ ] [cite_start]**Semana 1:** Diseñar el esquema de la base de datos SQLite con un mínimo de 3 tablas[cite: 154].
- [ ] [cite_start]**Semana 2:** Implementar la tokenización y el NER del dominio extrayendo al menos 3 tipos de entidades[cite: 35, 157].
- [ ] [cite_start]**Semana 2:** Construir el índice invertido sobre el corpus e implementar TF-IDF y búsqueda por similitud del coseno[cite: 158, 159].
- [ ] [cite_start]**Semana 3:** Entrenar el modelo de N-gramas (bigramas/trigramas) e implementar suavizado Add-k con k configurable[cite: 163, 164].
- [ ] [cite_start]**Semana 3:** Integrar ASR (SpeechRecognition) y medir WER sobre 10 frases de referencia[cite: 165, 166].
- [ ] [cite_start]**Semana 4 (ENTREGA PARCIAL - 30%):** Integrar todos los módulos en un pipeline end-to-end funcional por consola (micrófono → ASR → NLP → N-gramas → búsqueda → respuesta → TTS)[cite: 169, 171, 173]. [cite_start]Toda la actividad debe quedar registrada en la base de datos[cite: 172].

### [cite_start]Mes 2: Interfaz y evaluación (Semanas 5 a 8) [cite: 174]
- [ ] [cite_start]**Semana 5:** Crear la app Streamlit con la vista del usuario (botón de micrófono, campo de texto, resultados, audio TTS e historial)[cite: 176, 177, 178].
- [ ] [cite_start]**Semana 6:** Crear la vista del dashboard con Streamlit mostrando métricas globales y evolución temporal con datos reales[cite: 182, 183, 184].
- [ ] [cite_start]**Semana 7:** Simular más de 20 interacciones completas para realizar una evaluación end-to-end[cite: 188].
- [ ] [cite_start]**Semana 7:** Calcular métricas requeridas: WER, Perplejidad (PP), P/R/F1, accuracy NER y tiempo de respuesta[cite: 190].
- [ ] [cite_start]**Semana 8 (ENTREGA FINAL - 70%):** Limpiar el código, agregar docstrings y completar el README[cite: 196].
- [ ] [cite_start]**Semana 8:** Grabar el video demo (3-5 minutos) mostrando la app con voz real[cite: 194].
- [ ] [cite_start]**Semana 8:** Finalizar el informe técnico (3-5 páginas) y preparar la defensa oral (15 minutos)[cite: 195, 197].

## [cite_start]⚠️ Criterios de Desaprobación Automática [cite: 209]
- [ ] [cite_start]El sistema no funciona en la demostración en vivo[cite: 210].
- [ ] [cite_start]El reconocimiento de voz no está implementado (no hay ASR real)[cite: 211].
- [ ] [cite_start]No hay base de datos (todo se pierde al cerrar la app)[cite: 212].
- [ ] [cite_start]Se usaron APIs de LLMs (ChatGPT, Claude, Gemini, etc.) como motor de respuestas[cite: 213].
- [ ] [cite_start]Plagio de código o un integrante no puede explicar ninguna parte del código en la defensa oral[cite: 214, 215].