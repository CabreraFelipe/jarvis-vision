# JARVIS Vision — V0.4.4

Primera versión de aplicación destinada a comprobar el canal autenticado con el gestor seguro. Incluye AssistantCore modular, conserva cámaras, YOLO, Ollama, Vosk, activación por voz y contexto de sesión. Sin nuevas dependencias de aplicación.

## Actualizaciones

Canal oficial: https://github.com/CabreraFelipe/jarvis-vision/releases/latest/download/feed.json

El workflow valida Windows y Linux, genera los artefactos y verifica sus atestaciones antes de publicar. Las releases existentes no se sobrescriben. El gestor seguro requiere GitHub CLI >= 2.102.0 y una cuenta autenticada; verifica feed y ZIP, limita el repositorio y workflow, y pide consentimiento local. Migración del gestor inicial documentada en docs/UPDATE_SECURITY.md.

## Estado y límites

El usuario confirmó el éxito de la migración local del gestor y conservación de respaldo el 26/11/2026. Descarga, instalación y funcionamiento físico de V0.4.4 mediante el nuevo canal aún pendientes. Las pruebas CI simulan dispositivos. No hay actualización automática del gestor ni garantía TUF completa. No almacenar datos de usuario, modelos, capturas ni credenciales en el repositorio. No integrar Asia 2027.

## Pruebas

- En la raíz: `python -m unittest test_release test_security`.
- En app: `python -m unittest test_jarvis test_v04 test_wake041 test_core`.
- UI: `python test_ui.py` y `python test_voice_ui.py` (Linux con Xvfb).
- Próxima prueba física: comprobar versión visible, cámaras, voz y restauración/reaplicación mediante botón Restaurar. No reinstalar ni borrar datos.

## Desarrollo

Autonomía para cambios, commits y releases validadas, con consentimiento local para instalar. Evaluación externa y arquitectura en docs. No se incorporó Pipecat ni memoria persistente todavía.
