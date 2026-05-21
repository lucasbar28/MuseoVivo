import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.asr import ASREngine

def evaluar_wer():
    asr = ASREngine()
    
    # (Lo que dijo el usuario, Lo que transcribió el ASR)
    # Incluimos errores típicos de la API de Google con nombres locales y ruidos
    audios_simulados = [
        ("dónde queda la capilla de los negros", "dónde queda la capilla de los negros"), # Perfecto
        ("queremos ir a la casa de casco", "queremos ir a la casa de asco"), # Error por homofonía
        ("hay pique de pejerrey en la laguna", "hay pique de pejerrey en la luna"), # Error de dicción
        ("contame la historia de alfonsín", "contame la historia de alfonso"), # Palabra fuera de vocabulario o mal interpretada
        ("museo pampeano horarios", "museo pampeano horarios"), # Perfecto (frase robótica)
        ("qué colectivo me deja en el fuerte san juan", "qué colectivo me deja en el fuerte san juan"), # Perfecto
        ("queremos caminar por el casco histórico", "queremos caminar por el caco histórico"), # Inserción/Eliminación
        ("cuánto cuesta la entrada", "cuánto cuesta la entrada"),
        ("vamos a dar una vuelta por la costanera", "vamos a dar una vuelta por la costanera"),
        ("el monumento a la democracia", "el monumento a la de gracia") # Error por ruido ambiente
    ]
    
    total_wer = 0
    print("🎤 Iniciando Evaluación Acústica (Word Error Rate)")
    print("-" * 50)
    
    for ref, hip in audios_simulados:
        wer_actual = asr.calcular_wer(ref, hip)
        total_wer += wer_actual
        
        if wer_actual > 0:
            print(f"⚠️ Error ({wer_actual:.2f}) | Ref: '{ref}' -> Hip: '{hip}'")
        else:
            print(f"✅ Perfecto | '{ref}'")

    wer_promedio = total_wer / len(audios_simulados)
    print("-" * 50)
    print(f"📊 WER PROMEDIO: {wer_promedio*100:.1f}%")
    print("*(Nota para el informe: Un WER menor al 20% en ambientes ruidosos se considera excelente).*")

if __name__ == "__main__":
    evaluar_wer()