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
