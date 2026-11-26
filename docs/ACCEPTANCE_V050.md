# Validación física V0.5.0
No se afirma que estos controles hayan sido ejecutados en el PC. CI con simulaciones es requisito previo, no sustituto.

1. Cerrar JARVIS y abrir acceso directo administrado o JARVIS.bat. Comprobar aviso y aceptar V0.5.0; si falla no reinstalar, registrar el mensaje.
2. Comprobar versión visible, configuración previa, modelos y capturas; probar cámara principal y secundaria, selección y apagado.
3. En conversación sin cámara, comprobar Ollama y contexto de sesión. Probar YOLO y guardado de foto voluntario.
4. En memoria, añadir una nota de prueba no sensible, activar uso, preguntar por una palabra de la nota, editarla, cerrar/reabrir, verificar persistencia y eliminarla. Desactivar uso y comprobar que la nota no se adjunta.
5. Herramientas > Diagnóstico: verificar estados; no debe activar dispositivos por sí mismo.
6. Activar voz y probar «Hola, JARVIS» con pronunciación natural, por separado y en una frase. Repetir cinco veces; observar la transcripción de Vosk si falla. Probar «hola» sola y frases no dirigidas. No guardar audio. Opcionalmente habilitar JARVIS aislado antes de activar escucha; probar cancelación y pausa.
7. Si se desea, crear acceso directo desde Herramientas y abrirlo; comprobar ausencia de CMD permanente. El gestor antiguo todavía puede producir destellos auxiliares.
8. Si hay regresión, usar Restaurar y comunicar el resultado. No borrar archivos ni reemplazar versiones manualmente.

Pendientes fuera de V0.5.0: actualización autenticada del propio gestor sin migración repetida, modelo acústico especializado, Pipecat, memoria semántica, control de PC.