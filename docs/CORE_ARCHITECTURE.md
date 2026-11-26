# Núcleo modular (primer incremento V0.5, sin publicar)

AssistantCore separa la preparación de solicitudes, el proveedor de inferencia, el contexto y la aceptación de respuestas de la UI. La UI sigue controlando los permisos y la generación de cámara. Los frames se copian antes de llamar al proveedor; el historial se conserva solo en RAM y no incluye imágenes. El motor Ollama existente es el primer adaptador. No se han incorporado dependencias externas ni acceso a herramientas. Las pruebas de regresión siguen ejecutándose junto con test_core.

Siguiente: contratos de voz y detección, memoria local explícita y prueba aislada de Pipecat. El incremento permanece en rama de desarrollo sin cambio de VERSION hasta validar el bootstrap de seguridad; nunca reconstruir/sobrescribir v0.4.3.
