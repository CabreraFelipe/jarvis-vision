# Evaluación acústica de activación (26/11/2026)

No se modifica V0.5.0 ni el motor estable. La mejora de variantes de transcripción ya pasó CI, pero no hay medición acústica real. No introducir modelos externos sin evaluar licencias, dependencias y comportamiento.

## Candidatos

- openWakeWord: https://github.com/dscripka/openWakeWord/blob/main/README.md — modelo incluido "hey jarvis" en inglés; código Apache-2.0, modelos preentrenados CC BY-NC-SA 4.0. Útil como comparación personal, no asumir soporte nativo para "Hola, JARVIS" en español ni permiso comercial.
- sherpa-onnx: https://github.com/k2-fsa/sherpa-onnx — explorar motor local y modelo comunitario español https://huggingface.co/jguerrisi/sherpa-onnx-kws-zipformer-es-3M-2026-08-08 . El modelo declara Apache-2.0 pero la ficha exige comprobar licencias de voces de entrenamiento antes de redistribuir. Palabras configurables mediante BPE, 16 kHz mono; la evaluación publicada es pequeña y no incluye JARVIS. No descargar ni redistribuir hasta revisar procedencia. Candidato preferido para prueba española aislada.
- Porcupine: https://picovoice.ai/docs/quick-start/porcupine-python/ y https://picovoice.ai/docs/model-api/porcupine/ — admite español y Windows, requiere AccessKey y modelo específico. No contratar ni solicitar credenciales sin decisión explícita.

## Protocolo de evaluación

Usar WAV PCM mono 16 bits de procedencia autorizada. No publicar audio personal, transcripciones ni nombres de archivos. El banco tools/wake_benchmark.py mide el motor actual con audios locales elegidos explícitamente. Por cada clip positivo se mide si hubo activación; por clip negativo, si hubo activación falsa. Clips de positivos con una sola frase; negativos con conversaciones, ruido y música autorizados. Reporta conteos y tasa por clip, no falsas activaciones por hora (se detiene en la primera por clip). La detección de un nombre sin comando cuenta como activación. Repetir en diferentes condiciones con los mismos archivos. No confundir con latencia real del micrófono.

Objetivo inicial de evaluación, no resultado: al menos 20 clips positivos y 20 negativos; aspirar a >=90% de positivos y <=5% de negativos activados antes de integrar un candidato. Para estimar falsos positivos por hora hace falta un ensayo continuo más largo con recuento de eventos y rearmado. Mantener Vosk de respaldo. Nada de grabación continua adicional, nube o instalación obligatoria.
