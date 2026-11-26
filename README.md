# JARVIS Vision — V0.5.2

V0.5.2: compatibilidad USB opcional, recuperación cooperativa de instancia y gestor revisión 1 con autoactualización autenticada. La última migración del gestor requiere verificación externa y consentimiento. Ambas cámaras confirmadas funcionales por el usuario en V0.5.1; FPS exactos no informados. CI integrada superada antes del incremento de versión; CI de publicación y pruebas físicas de V0.5.2 pendientes.

Corrección de cámaras anterior: selección de modos por FPS medidos, controladores configurables y vista previa optimizada. Validación simulada de PR7 completada; la prueba física de Redragon sigue pendiente. Se conservan las funciones de V0.5.0.

Entrega acumulativa anterior: memoria local explícita y selectiva, personalidad, diagnóstico, acceso directo Windows y reconocimiento de voz mejorado. Mantiene cámaras, YOLO, Ollama, Vosk, modo fijo de seis segundos, activación por voz y contexto de sesión. Sin dependencias obligatorias nuevas.

## Actualizaciones
Canal oficial: https://github.com/CabreraFelipe/jarvis-vision/releases/latest/download/feed.json

GitHub valida Windows y Linux, genera y verifica atestaciones de los artefactos antes de publicar. No sobrescribe releases. El gestor instalado verifica feed y ZIP mediante GitHub CLI >=2.102.0. La instalación exige consentimiento local. Abrir mediante JARVIS.bat o el acceso directo al gestor, nunca mediante INICIAR.bat si se quiere comprobar actualizaciones. El gestor anterior requiere una última migración autenticada al gestor revisión 1; las futuras revisiones se ofrecen desde el feed firmado con consentimiento separado. El ZIP de app no sustituye al gestor. No eliminar el respaldo.

## Privacidad y límites
La memoria guarda únicamente notas explícitas, desactivada por defecto, en SQLite local sin cifrado de aplicación. No se graban transcripciones ni audio ni imágenes automáticamente. Recuperación por palabras, no semántica. El diagnóstico no abre dispositivos. La activación sigue dependiendo de Vosk; no es detector acústico especializado, ni identificación de hablante. Pipecat aún no integrado. No almacenar datos, capturas, modelos o credenciales en GitHub. Asia 2027 independiente.

## Pruebas
- Raíz: python -m unittest test_release test_security.
- app: python -m unittest test_jarvis test_v04 test_wake041 test_core test_memory test_launcher test_diagnostics test_speech_turn test_camera_performance.
- UI simulada: python test_ui.py y python test_voice_ui.py (Linux con Xvfb).
- El usuario confirmó la migración del gestor y la detección automática al abrir JARVIS.bat; no confirmó explícitamente instalación física de V0.4.4. El usuario confirmó las ocho comprobaciones de alto nivel de V0.5.0 en su PC. Webcam a 5 FPS reportada posteriormente; rendimiento pendiente de diagnóstico. Ver docs/ACCEPTANCE_V050.md.

## Desarrollo
Autonomía para cambios y releases validadas, con consentimiento local para instalar. No confundir CI con validación física.
