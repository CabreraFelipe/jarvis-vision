# V0.7 — base experimental de recuperación semántica

Rama independiente, no integrada ni publicada. Usa API Ollama local /api/tags y /api/embed, modelo candidato bge-m3:latest. La instalación del modelo será explícita; no se descarga ni se modifica la base SQLite. No persistir embeddings o preguntas. No hay activación en la interfaz en esta etapa.

Antes de integrar: opt-in separado, únicamente notas autorizadas; selección en worker, fallback léxico, límite MAX_CONTEXT existente, rechazo de resultados obsoletos al modificar o desactivar memoria, pruebas de relevancia y latencia reales en español, revisión del modelo y su licencia. No enviar audio, imágenes ni historial al modelo de embeddings. El umbral inicial 0.65 es provisional, no representa precisión validada. El modelo puede cargar RAM adicional y competir con gemma3. Validar en PC antes de habilitar por defecto (debe permanecer opt-in).

Referencia: https://docs.ollama.com/api/embed

Pruebas aisladas: cd app; python -m unittest test_semantic_memory. Aún no forman parte del ZIP o CI de la versión estable; incorporar explícitamente en build_release y workflow al integrar.

Base actualizada sobre V0.6.2: recuperación híbrida conserva coincidencias léxicas, añade semánticas dentro del presupuesto existente y reporta fallback. Cancelación descarta selección; no revoca peticiones locales en curso. Pruebas añadidas a CI y allowlist en esta rama. Aún no integrada con la interfaz ni publicada.
