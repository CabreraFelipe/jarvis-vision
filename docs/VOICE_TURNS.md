# Voz local — fase de turnos naturales

El primer incremento conserva Vosk y pyttsx3. Agrega la opción de terminar la captura al detectar el primer segmento finalizado no vacío de Vosk, con límite de 12 s y cancelación existente. La captura fija de 6 s y el modo wake no cambian. No se activa el micrófono sin solicitud. El endpoint puede cortar una frase con pausa larga; el modo anterior permanece como alternativa. No se incorpora Pipecat todavía, ni streaming de TTS, ni barge-in, ni audio remoto.

La siguiente fase experimentará con un adaptador externo aislado solo después de verificar versiones, requisitos, licencia y comportamiento en Windows. Las pruebas actuales usan un reconocedor simulado; no validan latencia ni calidad de reconocimiento física.
