# Seguridad del actualizador — transición V0.4.4

Estado: trabajo preparatorio, V0.4.3 sigue siendo la versión publicada. El flujo de release genera y verifica atestaciones de procedencia para el ZIP y feed antes de publicar. Una release anterior no se reemplaza. Una atestación de una reconstrucción no implica que el ZIP previamente publicado esté atestado: comparar los digests.

## Límite del protocolo 1

El gestor local se instala en .jarvis/manager.py y solo instala los archivos app/ declarados en release.json. No sustituye al gestor con una actualización normal. SHA-256 detecta alteraciones pero no autentica por sí solo el editor. Las atestaciones en CI no implican verificación en el cliente. No afirmar que V0.4.3 valida firmas.

## Próximo hito obligatorio

- Evaluar verificación de Sigstore/atestaciones de GitHub y TUF, con identidad y repositorio fijados y política de revocación.
- Diseñar migración del gestor explícita, comprobada y reversible, sin ejecutar un gestor recibido como parte de un ZIP sin verificación.
- Probar firma inválida, origen incorrecto, manipulación del ZIP y feed, metadatos antiguos, recuperación sin red, restauración y conservación de todos los archivos de usuario.
- Mantener consentimiento local antes de instalar. No almacenar credenciales ni claves privadas en repositorio, paquetes o logs.
- No publicar V0.4.4 como actualizador autenticado hasta que el gestor local realmente aplique las comprobaciones antes de instalar.

La publicación de código se automatiza, no el acceso a los datos personales ni la ejecución desatendida en el PC.

## Candidato de verificación local

Se incorpora un gestor candidato que verifica feed y ZIP con GitHub CLI instalado por separado, limita la identidad al repositorio y workflow oficiales, exige main y runner hospedado, y bloquea descargas si la autenticación falla. Se verifica también el ZIP elegido manualmente. El estado conserva la versión máxima observada para impedir retrocesos por metadatos antiguos; la restauración local explícita sigue disponible. No es TUF completo: no hay garantía de frescura temporal ni revocación independiente de GitHub. El CLI puede requerir autenticación y conectividad. No se instala ni modifica automáticamente el CLI.

El gestor sigue sin automigrar: se añadirá como artefacto atestado independiente en las nuevas releases. La migración inicial requiere verificar ese archivo desde una instalación confiable de GitHub CLI antes de reemplazar el gestor local, con respaldo y prueba física. V0.4.3 no se reemplaza. Las pruebas de esta rama no prueban criptografía real en el PC; simulan resultados del verificador. La publicación V0.4.4 continúa bloqueada hasta completar la migración y los controles pertinentes.

## Migración inicial y versión mínima del verificador

Se exige gh >= 2.102.0 por GHSA-wjmr-j3rp-mh2g y GHSA-4mq3-hpgx-9cx8. El workflow se fija incluyendo @refs/heads/main. El gestor candidato implementa --migrate con ruta explícita a la instalación, bloqueo de instancia, verificación del gestor descargado, respaldo identificado por SHA-256 y reemplazo atómico. No altera datos ni estado. El bootstrap se publica como prerelease independiente y no cambia el canal latest. Verificar el archivo externamente con gh antes de ejecutarlo; la autoverificación no sustituye ese paso. La actualización automática del gestor futuro todavía no está implementada. La validación de hardware y migración real se mantiene pendiente.

## Confirmación de bootstrap y versión de prueba — 26/11/2026

El usuario informó «Gestor actualizado. Respaldo conservado.» después de verificar y ejecutar el bootstrap. Se prepara V0.4.4 con el núcleo modular validado para comprobar la actualización autenticada real. No equivale a haber instalado V0.4.4 ni a validar sus cámaras/micrófono. El gestor inicial no se autoactualiza. Antes de avanzar en publicación funcional amplia, probar descarga, arranque, restauración y retorno a V0.4.4 desde el botón Restaurar.

## Entrega acumulativa V0.5.0
El usuario confirmó detección automática de la actualización mediante JARVIS.bat. No hay confirmación explícita de la instalación de V0.4.4. V0.5.0 se publica solo si CI y atestaciones pasan. El gestor nuevo se distribuye como asset autenticado separado y no se sustituye por la actualización de aplicación. Los datos de memoria local se añaden a la regresión de actualización y restauración.


## Recuperación de instancia (candidato posterior a V0.5.1)
Se conserva el bloqueo exclusivo del sistema operativo. En un segundo inicio normal, el gestor candidato escribe una señal fija local de foco, sin comandos ni datos sensibles. La ventana del gestor o aplicación candidata consume la señal, con expiración de 15 segundos, e intenta deiconify/lift/focus_set. Windows puede impedir el foco por sus políticas; no se fuerza ni se cierra ningún proceso. Abrir ACTUALIZACIONES con una sesión activa sigue mostrando una indicación para cerrarla. No se libera el lock de otra instancia. No se modifica una instalación antigua automáticamente. Requiere nueva app y migración autenticada del gestor; probar segundo clic durante ventana abierta/minimizada y cierre, además de CI. La señal es de mejor esfuerzo, no confirma foco real.


## Actualización autenticada del propio gestor (candidato)
La revisión 1 del gestor entiende el campo opcional manager del feed firmado, con revisión monotónica, URL exacta de la release y SHA-256 del artefacto. El empaquetador genera el manager.py y su digest a partir de los mismos bytes, y CI atesta todos los archivos. El gestor consulta el feed incluso si no hay nueva app, pide consentimiento separado, vuelve a verificar el manifiesto tras la aprobación y exige que la oferta coincida. Verifica hash, procedencia y revisión declarada; conserva respaldo y reemplaza atómicamente bajo el bloqueo existente. El código nuevo no se ejecuta en el proceso actual, se aplica al próximo inicio. Se conserva el protocolo 1 y compatibilidad con feeds anteriores. Se requiere una última migración autenticada desde el gestor antiguo, que no contiene el mecanismo. El método manual sigue siendo recuperación explícita. No es TUF ni una garantía de frescura temporal. La prueba de actualización real de revisión 1 a una posterior y la migración inicial siguen pendientes. No se cambia la aplicación estable V0.5.1 ni se promete eliminación de consolas sin prueba física.

La revisión integrada de foco admite hasta dos segundos de desfase negativo del reloj del sistema de archivos. Se mantiene la caducidad de 15 segundos. Las colas CI quedan aisladas por referencia para evitar cancelar validaciones de PR al actualizar main.

## Entrega V0.5.2
CI de PR10 y regresión integrada del foco superada en Windows y Linux (45877438162, 45877381189). La revisión 1 se publica como artefacto manager.py firmado y con SHA-256 incluido en feed.json. Confirmar publicación antes de migrar. Tras instalar la app V0.5.2, cerrar completamente el gestor y la app; descargar el manager.py de v0.5.2 en un directorio temporal, verificar su digest publicado y su atestación fijando repositorio y workflow, y ejecutar python manager.py --migrate RUTA_INSTALACION. No migrar con la aplicación abierta. Mantener respaldo. Probar apertura doble y arranque normal, sin reinstalar. El protocolo de autoactualización ha sido probado con candidatos simulados; su primera transición real posterior a revisión 1 aún no existe. No declarar eliminación completa de consolas sin prueba física.
