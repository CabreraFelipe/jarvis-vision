# JARVIS Vision — V0.5.0

Entrega acumulativa: memoria local explícita y selectiva, personalidad, diagnóstico, acceso directo Windows y reconocimiento de voz mejorado. Mantiene cámaras, YOLO, Ollama, Vosk, modo fijo de seis segundos, activación por voz y contexto de sesión. Sin dependencias obligatorias nuevas.

## Actualizaciones
Canal oficial: https://github.com/CabreraFelipe/jarvis-vision/releases/latest/download/feed.json

GitHub valida Windows y Linux, genera y verifica atestaciones de los artefactos antes de publicar. No sobrescribe releases. El gestor instalado verifica feed y ZIP mediante GitHub CLI >=2.102.0. La instalación exige consentimiento local. Abrir mediante JARVIS.bat o el acceso directo al gestor, nunca mediante INICIAR.bat si se quiere comprobar actualizaciones. El gestor de V0.5.0 incorpora ocultación de consolas auxiliares, pero no se reemplaza automáticamente: requiere migración independiente autenticada. No eliminar el respaldo.

## Privacidad y límites
La memoria guarda únicamente notas explícitas, desactivada por defecto, en SQLite local sin cifrado de aplicación. No se graban transcripciones ni audio ni imágenes automáticamente. Recuperación por palabras, no semántica. El diagnóstico no abre dispositivos. La activación sigue dependiendo de Vosk; no es detector acústico especializado, ni identificación de hablante. Pipecat aún no integrado. No almacenar datos, capturas, modelos o credenciales en GitHub. Asia 2027 independiente.

## Pruebas
- Raíz: python -m unittest test_release test_security.
- app: python -m unittest test_jarvis test_v04 test_wake041 test_core test_memory test_launcher test_diagnostics test_speech_turn.
- UI simulada: python test_ui.py y python test_voice_ui.py (Linux con Xvfb).
- El usuario confirmó la migración del gestor y la detección automática al abrir JARVIS.bat; no confirmó explícitamente instalación física de V0.4.4. La prueba acumulativa V0.5.0 debe comprobar versión visible, dos cámaras, voz real, memoria y diagnóstico. Ver docs/ACCEPTANCE_V050.md.

## Desarrollo
Autonomía para cambios y releases validadas, con consentimiento local para instalar. No confundir CI con validación física.
