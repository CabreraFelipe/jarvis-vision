# Validación física V0.5.2
Confirmado por usuario: cabecera V0.5.2, Redragon fluida, acceso directo sin CMD, doble apertura recupera ventana existente. Pendiente: action camera, ambas cámaras simultáneas, reconocimiento y respuestas. Reporta que la action camera tarda en arrancar, Vosk transcribe mal casi todo y quedan procesos Python tras cierre. No asumir causa ni validación física de la corrección. Mantener motor de cámaras normal y ofrecer Inicio rápido explícito sin sondeo, no fijar automáticamente backend/resolución. Selección de entrada y modelo Vosk completo opcional, prueba sin enviar consultas. El motor pequeño permanece por defecto hasta instalar/seleccionar otro. No hay prueba acústica real. Cierre corregido en PR12 con CI superada; falta prueba local.

V0.5.3 candidata: PR12 y PR13 validadas en ambos OS e integradas. Confirmaciones físicas de V0.5.2 no se trasladan automáticamente a V0.5.3. Pendientes publicación y prueba real de las correcciones; no dar por resueltas las incidencias.


Nueva observación: en otro intento V0.5.2 la action camera no mostró imagen. Incidencia intermitente. Mantener abierta hasta validar arranques repetidos y funcionamiento simultáneo, incluso tras cierre y reapertura. No sustituir V0.5.3 publicada con bytes distintos.
