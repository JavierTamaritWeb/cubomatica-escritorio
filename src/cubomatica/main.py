"""
Punto de entrada de la aplicacion.

Abre una ventana nativa que carga tu web (HTML + CSS + JS vanilla).
La apariencia visual es IDENTICA a la del navegador.
"""

import os
import sys
from pathlib import Path

import webview

from cubomatica.api import Api

# Carpeta de datos persistentes para los backends que la respetan (Windows, Linux).
# OJO: en macOS pywebview la IGNORA. El backend Cocoa usa siempre
# WKWebsiteDataStore.defaultDataStore(), que guarda en
#   ~/Library/WebKit/<bundle id>/WebsiteData/
# Por eso el .app (es.javiertamarit.cubomatica) y el modo desarrollo
# (org.python.python) NO comparten perfiles ni progreso.
STORAGE_DIR = Path.home() / "Library" / "Application Support" / "Cubomatica"


def localizar_index() -> Path:
    """
    Devuelve la ruta de index.html en desarrollo y dentro del .app.

    En desarrollo la web cuelga del propio paquete. Dentro del .app la
    coloca PyInstaller segun el 'datas' del .spec, y la raiz es sys._MEIPASS.
    Se prueban las dos y se coge la que exista de verdad: asi un cambio en el
    empaquetado no se manifiesta como una ventana en blanco silenciosa.
    """
    candidatos = [Path(__file__).parent / "web" / "index.html"]

    raiz = getattr(sys, "_MEIPASS", None)
    if raiz:
        candidatos.append(Path(raiz) / "cubomatica" / "web" / "index.html")

    for candidato in candidatos:
        if candidato.is_file():
            return candidato.resolve()

    raise SystemExit(
        "No encuentro index.html. Rutas probadas:\n  "
        + "\n  ".join(str(c) for c in candidatos)
    )


def main() -> None:
    api = Api()
    index = localizar_index()

    if os.environ.get("CUBOMATICA_DEBUG") == "1":
        print(f"[cubomatica] index: {index}", file=sys.stderr)
        print(f"[cubomatica] url  : {index.as_uri()}", file=sys.stderr)

    # OJO con el esquema de la URL. Si se pasa una ruta suelta ("/Users/.../index.html"),
    # pywebview la considera "local" y levanta un servidor HTTP interno. Con
    # private_mode=False ese servidor usa SIEMPRE el puerto fijo 42001, asi que
    # una segunda instancia (o una que se quedo colgada) no puede abrirlo y la
    # ventana acaba mostrando "Error: 404 Not Found" en vez del juego.
    #
    # Con file:// no se levanta ningun servidor: no hay puerto, no hay colision,
    # y no queda un socket a la escucha en el equipo. Comprobado que localStorage
    # persiste igual entre arranques.
    webview.create_window(
        title="Cubomática",
        url=index.as_uri(),
        js_api=api,          # <-- puente JavaScript -> Python
        # Arranca ocupando toda la pantalla. width/height son el tamano al que
        # vuelve la ventana si el usuario la restaura, no el de arranque.
        maximized=True,
        width=1280,
        height=800,
        min_size=(1024, 640),  # el juego esta pensado para apaisado
        resizable=True,
        confirm_close=False,
    )

    # private_mode=False es CRITICO: es lo UNICO que hace que localStorage
    # persista. Con private_mode=True el backend Cocoa usa un almacen
    # no persistente y el juego pierde perfiles y progreso al cerrar.
    # DevTools solo bajo demanda:  CUBOMATICA_DEBUG=1 uv run cubomatica
    opciones = {
        "private_mode": False,
        "debug": os.environ.get("CUBOMATICA_DEBUG") == "1",
    }

    # storage_path solo en Windows y Linux. En macOS pywebview lo ignora, pero
    # aun asi CREA la carpeta (webview.__set_storage_path), y quedaria una
    # carpeta vacia para siempre en Application Support.
    if sys.platform != "darwin":
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        opciones["storage_path"] = str(STORAGE_DIR)

    webview.start(**opciones)


if __name__ == "__main__":
    main()
