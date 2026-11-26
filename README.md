# JARVIS Vision — V0.4.3

Repositorio independiente para la distribución de JARVIS. La aplicación es idéntica a V0.4.2 excepto por su versión visible, para comprobar la actualización remota sin introducir cambios funcionales.

## Publicación

1. Crear `CabreraFelipe/jarvis-vision` y dar acceso al conector GitHub. El canal del actualizador V0.4.2 requiere assets públicamente accesibles por HTTPS; si se prefiere un repositorio privado habrá que adaptar el mecanismo antes de publicar. No incluir archivos personales, credenciales, configuraciones, capturas ni modelos.
2. Subir los archivos fuente de este paquete a `main`, incluyendo `.github/workflows/release.yml`. No subir el ZIP de distribución como código fuente.
3. En Actions, ejecutar manualmente **Validar y publicar JARVIS** sobre `main`. La publicación queda bloqueada hasta pasar las pruebas en Linux y Windows (hardware y modelos simulados). No ejecutar nuevamente si ya existe el tag `v0.4.3`.
4. Comprobar la release, sus dos assets y el SHA-256 anunciado. El gestor V0.4.2 admite el canal `https://github.com/CabreraFelipe/jarvis-vision/releases/latest/download/feed.json`.
5. En el PC, abrir el gestor, configurar ese canal, buscar actualizaciones, aceptar V0.4.3 y comprobar que se conservan cámaras, voz, preferencias y datos. Probar restauración V0.4.2 y vuelta a V0.4.3.

## Seguridad y límites

El protocolo 1 verifica SHA-256 e integridad de archivos y exige confirmación local, pero aún no proporciona autenticación criptográfica independiente de GitHub. Proteger la cuenta con 2FA y no configurar fuentes de confianza desconocida. No se ha habilitado ninguna instalación desatendida. La firma de actualizaciones se abordará antes de ampliar el canal de distribución.

## Pruebas locales

```sh
python -m pip install numpy opencv-python-headless Pillow
python -m unittest test_release
cd app
python -m unittest test_jarvis test_v04 test_wake041
python test_ui.py
python test_voice_ui.py
```

En Linux, ejecutar los dos scripts de interfaz con `xvfb-run -a`. Las pruebas locales en Linux no sustituyen las de Windows ni la comprobación física del PC.
