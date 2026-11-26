# Voz local — fase de turnos naturales

El primer incremento conserva Vosk y pyttsx3. Agrega la opción de terminar la captura al detectar el primer segmento finalizado no vacío de Vosk, con límite de 12 s y cancelación existente. La captura fija de 6 s y el modo wake no cambian. No se activa el micrófono sin solicitud. El endpoint puede cortar una frase con pausa larga; el modo anterior permanece como alternativa. No se incorpora Pipecat todavía, ni streaming de TTS, ni barge-in, ni audio remoto.

La siguiente fase experimentará con un adaptador externo aislado solo después de verificar versiones, requisitos, licencia y comportamiento en Windows. Las pruebas actuales usan un reconocedor simulado; no validan latencia ni calidad de reconocimiento física.

## Activación mejorada
Se conserva Hola JARVIS y Hola asistente. Se añaden variantes explícitas y fragmentación del nombre con vencimiento a 2 s; no se usa coincidencia difusa ilimitada. Opción desactivada por defecto para activar con el nombre aislado, sin activar por frases que solo lo mencionan. La escucha mantiene consentimiento y cancelación. Las pruebas cubren el procesamiento de transcripciones, no la tasa de reconocimiento acústico en hardware. Próximo paso: calibrar con el texto reconocido en la prueba física, comparar motor especializado si Vosk sigue confundiendo el nombre.
