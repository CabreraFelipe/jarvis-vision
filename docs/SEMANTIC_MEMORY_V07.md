# V0.7 — base experimental de recuperación semántica

Rama independiente, no integrada ni publicada. Usa API Ollama local /api/tags y /api/embed, modelo candidato bge-m3:latest. La instalación del modelo será explícita; no se descarga ni se modifica la base SQLite. No persistir embeddings o preguntas. No hay activación en la interfaz en esta etapa.

Antes de integrar: opt-in separado, únicamente notas autorizadas; selección en worker, fallback léxico, límite MAX_CONTEXT existente, rechazo de resultados obsoletos al modificar o desactivar memoria, pruebas de relevancia y latencia reales en español, revisión del modelo y su licencia. No enviar audio, imágenes ni historial al modelo de embeddings. El umbral inicial 0.65 es provisional, no representa precisión validada. El modelo puede cargar RAM adicional y competir con gemma3. Validar en PC antes de habilitar por defecto (debe permanecer opt-in).

Referencia: https://docs.ollama.com/api/embed

Pruebas aisladas: cd app; python -m unittest test_semantic_memory. Aún no forman parte del ZIP o CI de la versión estable; incorporar explícitamente en build_release y workflow al integrar.

Base actualizada sobre V0.6.2: recuperación híbrida conserva coincidencias léxicas, añade semánticas dentro del presupuesto existente y reporta fallback. Cancelación descarta selección; no revoca peticiones locales en curso. Pruebas añadidas a CI y allowlist en esta rama. Aún no integrada con la interfaz ni publicada.

Integración candidata 0.7.0: tabla adicional semantic_settings, predeterminada desactivada; no altera notas ni settings anteriores. Opción separada de consentimiento, desactivada al apagar memoria. Contexto apagado nunca entrega notas. Worker compara únicamente pregunta y notas explícitas; mantiene coincidencias léxicas y agrega semánticas dentro de 1800 caracteres. Cancelación descarta resultados y evita iniciar respuesta si ya fue detectada; no puede revocar una petición local ya enviada. Fallback visible por palabras. Modelo BGE-M3 candidato multilingüe (aprox. 1,2 GB en catálogo Ollama); no descarga automática. Pendiente banco real español, latencia, licencia y validación física antes de publicar. PR debe permanecer borrador.

CI inicial 45900935821: Linux correcto; Windows 156/157 pruebas, error de limpieza WinError 32 en test_legacy_database_migration. El context manager de sqlite3 no cierra la conexión: cerrar explícitamente mediante contextlib.closing, sin omitir la prueba. Se refuerza cancelación antes de enviar notas a /api/embed y prueba del presupuesto de contexto. Licencia MIT declarada por BAAI en https://huggingface.co/BAAI/bge-m3 ; modelo distribuido por Ollama https://ollama.com/library/bge-m3 . No redistribuimos pesos.

CI 45901255069 superó Windows/Linux en el commit 5b3bcbf1. Comandos explícitos añadidos: «recordá que ...», «olvidá ...» (coincidencia exacta y única), «qué sabés sobre mí» (abre ventana, sin leer notas en voz alta), «cambiá estilo a conciso/detallado/conversacional/normal». Ruta local, sin consultar modelo, confirmación visual para cada escritura o borrado. Desactiva escucha y seguimiento antes de solicitar confirmación; reactivar manualmente. No interpreta sugerencias del LLM como comandos. No guardar automáticamente ni borrar por coincidencia aproximada. Falta validación física y CI del nuevo commit.
