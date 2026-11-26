# Inicio de escritorio Windows

La ventana CMD permanente se debe al lanzador .bat. El acceso directo JARVIS.lnk apunta a pythonw.exe y .jarvis/manager.py (no al archivo de una versión específica), conservando el canal y el consentimiento de instalación. La opción Herramientas > Crear acceso directo de JARVIS se ofrece únicamente en Windows administrado; solicita confirmación y usa PowerShell sin consola con rutas transmitidas por entorno. No modifica ni elimina BAT existentes. No crea accesos directos sin intervención del usuario.

El gestor candidato añade CREATE_NO_WINDOW en Windows para los procesos de verificación GitHub CLI y la aplicación. El gestor instalado anteriormente no cambia mediante ZIP de aplicación; esta mejora requiere una futura migración autenticada del gestor. No sustituirlo silenciosamente. El acceso directo ya creado manualmente sigue siendo compatible. No se ha comprobado el comportamiento del escritorio real, ni se ha creado un icono personalizado. Las pruebas unitarias validan rutas y configuración, no automatizan COM del escritorio físico.

La versión de aplicación permanece 0.4.4 hasta confirmar su instalación física y validar las nuevas pruebas. No sobrescribir la release existente.
