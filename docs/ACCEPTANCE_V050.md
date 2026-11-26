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

## Resultado comunicado por el usuario (26/11/2026)
Confirmadas las ocho comprobaciones de alto nivel: actualización automática V0.5.0, cámaras, activación Hola JARVIS y nombre aislado, detección de pausas, memoria/personalidad, diagnóstico e inicio por acceso directo sin CMD. No se infiere validación exhaustiva de cada subpaso, ni tasa acústica, ni migración del nuevo gestor. Incidencia previa de instancia administrada abierta, posteriormente pudo abrir la app. Mejora futura: recuperar/enfocar instancia existente sin saltarse el bloqueo. Nueva observación: webcam a 5 FPS; causa no confirmada. Probar 720p MJPG 30 FPS y 480p MJPG 30 FPS con buena luz, una sola cámara y YOLO desactivado, comparar con otra aplicación. El modo automático actual prioriza resolución y no mide rendimiento durante la negociación. Pendiente diseño de perfil equilibrado que conserve opciones manuales.
