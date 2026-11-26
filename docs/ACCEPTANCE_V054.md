# Validación física V0.5.4 — 26 de noviembre de 2026

Versión publicada: v0.5.4, commit cab8673b6829057390617d79e0d420e349b0b6a2. CI 45879620857 superada.

## Confirmaciones del usuario (6/10)
- Cabecera V0.5.4.
- Gestor revisión 2 actualizado.
- Redragon sigue funcionando fluidamente.
- Acceso directo sin CMD.
- Recuperación de instancia existente.
- Cinco cierres sin procesos residuales de JARVIS.

## Pendiente de confirmación (4/10)
- Action camera conecta correctamente cinco veces.
- Ambas cámaras funcionan simultáneamente.
- Transcripción de voz mejorada.
- Reconoce «Hola, JARVIS».

Pendiente no significa necesariamente fallo repetido en esta versión: no se comunicó qué modo, backend, índice, micrófono o modelo de voz se usó ni si se completaron las pruebas. No afirmar instalación de Vosk completo ni atribuir causa a USB o modelo sin evidencia. Cinco cierres y revisión 2 confirmados; no garantiza cierre bajo todos los bloqueos. Mantener intactos los componentes que funcionan.

## Diagnóstico físico siguiente
1. Conservar perfil Redragon. Probar action camera sola en modo Compatibilidad, formato Automático y controlador DirectShow, mismo índice conocido. Anotar estado exacto y si hay imagen. Si falla, probar Media Foundation por separado y confirmar identidad física, pues índice puede variar. Repetir con Redragon activa para distinguir fallo individual de concurrencia.
2. Desactivar escucha continua. Herramientas > Micrófono y reconocimiento: identificar entrada y modelo; transcribir frase normal sin IA. Registrar texto reconocido y comparar con frase pronunciada. Si se instaló modelo Completo, confirmar selección y repetir con mismo micrófono. Probar activación por separado. No recopilar audio sin consentimiento.
3. Si fallan, usar evidencia para elegir siguiente corrección. No ampliar variantes de palabra de activación como sustituto de un buen reconocimiento general. Priorizar comparación de motor y diagnóstico de captura antes de nuevas releases.
