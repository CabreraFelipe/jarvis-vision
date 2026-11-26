# Diagnóstico y memoria selectiva

El diagnóstico muestra versiones de dependencias, existencia de modelos, servicio Ollama y modelo local (GET a 127.0.0.1, sin proxy ni redirecciones), estado de las cámaras y actividad del micrófono según la UI. No abre dispositivos, no ejecuta inferencia ni guarda diagnósticos; no confirma funcionamiento físico. La comprobación se ejecuta fuera del hilo UI.

La memoria conserva su esquema SQLite. Añade edición, búsqueda por texto normalizado y selección por coincidencia de palabras (sin acentos, sin palabras comunes). Solo se adjuntan recuerdos coincidentes, sin fallback indiscriminado. No es búsqueda semántica ni vectorial; sinónimos y variantes pueden no coincidir. No adjunta recuerdos si el contexto está desactivado, incluso si otro componente los pasa. No se guardan consultas ni se modifica la base existente fuera de acciones explícitas.

Las mejoras permanecen sin publicar hasta superar CI y confirmar la instalación de V0.4.4.
