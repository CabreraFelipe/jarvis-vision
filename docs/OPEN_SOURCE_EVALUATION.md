# V0.5 — evaluación de componentes externos (revisión documental inicial)

Fecha: 2026-11-26. No se ha importado ni ejecutado código de terceros. Esta revisión de documentación y metadatos GitHub orienta las pruebas de integración; no certifica seguridad ni compatibilidad física.

| Proyecto | Licencia declarada por GitHub | Decisión inicial |
| --- | --- | --- |
| [Dix01/JARVIS](https://github.com/Dix01/JARVIS) | MIT | Referencia para interfaz Windows y separación frontend/backend; no adoptar su ejecución de herramientas indiscriminadamente. |
| [Leon](https://github.com/leon-ai/leon) | MIT | Referencia para registro de skills y memoria; evitar incorporar su runtime completo Node/TypeScript en esta etapa. |
| [Pipecat](https://github.com/pipecat-ai/pipecat) | BSD-2-Clause | Candidato preferido a dependencia opcional para voz en streaming; validar audio Windows, STT español, VAD, interrupción y TTS local. |
| [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) | Apache-2.0 | Evaluar interfaces de proveedor de inferencia; no sustituir Ollama sin ventaja comprobada. |

## Fuentes concretas

- https://github.com/Dix01/JARVIS/blob/main/README.md y https://github.com/Dix01/JARVIS/blob/main/SECURITY.md
- https://github.com/leon-ai/leon/blob/develop/core/context/ARCHITECTURE.md
- https://github.com/pipecat-ai/pipecat/blob/main/examples/getting-started/06a-voice-agent-local.py
- https://github.com/pipecat-ai/pipecat/blob/main/pyproject.toml
- https://github.com/open-jarvis/OpenJarvis/blob/main/docs/architecture/engine.md

## Estrategia de integración

Conservar interfaz Tkinter y módulos camera.py, voice.py, vision.py y conversation.py durante el primer incremento. Introducir contratos independientes para audio, visión, proveedor de chat, memoria y registro de herramientas; usar las implementaciones actuales como adaptadores de referencia. SQLite local para memoria inicialmente, sin guardar imágenes ni transcripciones por defecto. Separar motor de herramientas de la UI: ninguna ejecución arbitraria de shell, instalación, envío de datos o cambios en archivos fuera de alcance habilitados por defecto.

Pipecat es la primera prueba externa: experimento aislado, dependencias fijadas, ejecución opcional y retorno inmediato al flujo Vosk actual. Validar activación en español, latencia, interrupción, no autoactivación por voz sintetizada y liberación de micrófono. No transmitir audio a servicios externos sin consentimiento.

Antes de reutilizar código: registrar commit upstream, licencia exacta y avisos, dependencias transitivas y auditoría de archivos específicos. Probar en Windows/Linux con mocks y en hardware real. Mantener nuevas dependencias fuera de instalación obligatoria hasta validar. No integrar Asia 2027.

## Criterios de avance

1. Cerrar bootstrap del gestor y validar canal real.
2. Probar contratos internos sin cambiar comportamiento observable.
3. Evaluar memoria persistente local y configuración de personalidad.
4. Evaluar Pipecat mediante prueba de audio opcional.
5. Adoptar solo piezas que reduzcan complejidad o aporten mejora medible. No reemplazar aplicación estable por un fork sin equivalencia de funcionalidades y migración.
