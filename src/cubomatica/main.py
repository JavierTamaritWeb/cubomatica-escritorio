"""
Punto de entrada de la aplicacion.

Abre una ventana nativa que carga tu web (HTML + CSS + JS vanilla).
La apariencia visual es IDENTICA a la del navegador.
"""

import os
import sys
import threading
from pathlib import Path

import webview

from cubomatica.api import Api

# Pantallas del juego que se pueden abrir desde la barra de menus.
# Los identificadores son los mismos que usan los botones data-ir del HTML.
MENU_PANTALLAS = [
    ("¿Quién juega?", "p-perfiles"),
    ("Ajustes", "p-ajustes"),
    None,  # separador
    ("Ayuda", "p-ayuda"),
    ("Créditos", "p-creditos"),
]

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


# Mantiene vivos los objetos que reciben los clics del menu. Cocoa NO retiene
# el "target" de un NSMenuItem, asi que si Python los recolecta el menu se
# queda mudo: se despliega, se puede pulsar, y no pasa absolutamente nada.
_REFERENCIAS_MENU: list = []


def accion_ir_a(ventana, pantalla: str):
    """
    Devuelve la funcion que lleva el juego a una pantalla.

    OJO con el hilo. webview.evaluate_js encola el trabajo en el hilo de la
    interfaz y se queda esperando el resultado, asi que ejecutarlo EN ese hilo
    congela la app para siempre. Por eso el JS sale a un hilo aparte.
    """
    # El guion comprueba que el juego este cargado: pulsar el menu durante el
    # arranque no debe romper nada, solo no hacer nada.
    guion = (
        "(function () {"
        "  try {"
        "    if (window.CB && CB.pantallas && CB.pantallas.ir) {"
        f"      CB.pantallas.ir('{pantalla}'); return 'ok';"
        "    }"
        "    return 'no-listo';"
        "  } catch (e) { return 'error: ' + e.message; }"
        "})()"
    )

    def accion() -> None:
        def ejecutar() -> None:
            try:
                resultado = ventana.evaluate_js(guion)
            except Exception as e:  # noqa: BLE001 - un menu nunca debe tumbar la app
                resultado = f"excepcion: {e}"
            if os.environ.get("CUBOMATICA_DEBUG") == "1":
                print(f"[cubomatica] menu {pantalla} -> {resultado}", file=sys.stderr)

        threading.Thread(target=ejecutar, daemon=True).start()

    return accion


def instalar_menu(ventana) -> None:
    """
    Añade el menu "Juego" a la barra de macOS.

    Se construye a mano con PyObjC en vez de usar el parametro menu= de
    webview.start(), porque en pywebview 5.3.2 ese camino no funciona en macOS
    por dos motivos distintos:

    1. start() monta el menu ANTES de crear la ventana, y al crearla pywebview
       llama a _clear_main_menu() y lo borra. El menu ni siquiera aparece.
    2. Aunque aparezca, sus objetos internos se pierden por recoleccion de
       basura y los elementos quedan mudos.

    Por eso se instala con el evento loaded (ya pasado el borrado) y guardando
    las referencias en _REFERENCIAS_MENU.
    """
    if sys.platform != "darwin":
        return

    puesto = threading.Event()

    def montar() -> None:
        import AppKit
        import objc
        from Foundation import NSObject

        class DestinoMenu(NSObject):
            """Recibe los clics. Un solo selector; el tag dice cual es."""

            def activar_(self, remitente) -> None:
                try:
                    self.acciones[remitente.tag()]()
                except Exception as e:  # noqa: BLE001
                    print(f"[cubomatica] menu: {e}", file=sys.stderr)

        destino = DestinoMenu.alloc().init()
        destino.acciones = []
        _REFERENCIAS_MENU.append(destino)

        submenu = AppKit.NSMenu.alloc().initWithTitle_("Juego")
        # Sin esto macOS decide solo que elementos estan activos y los apaga.
        submenu.setAutoenablesItems_(False)

        for entrada in MENU_PANTALLAS:
            if entrada is None:
                submenu.addItem_(AppKit.NSMenuItem.separatorItem())
                continue

            titulo, pantalla = entrada
            elemento = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                titulo, objc.selector(DestinoMenu.activar_, signature=b"v@:@"), ""
            )
            elemento.setTarget_(destino)
            elemento.setTag_(len(destino.acciones))
            elemento.setEnabled_(True)
            destino.acciones.append(accion_ir_a(ventana, pantalla))
            submenu.addItem_(elemento)

        raiz = AppKit.NSMenuItem.alloc().init()
        raiz.setTitle_("Juego")
        raiz.setSubmenu_(submenu)

        barra = AppKit.NSApplication.sharedApplication().mainMenu()
        if barra is not None:
            barra.addItem_(raiz)
            _REFERENCIAS_MENU.append(raiz)

    def al_cargar(*_) -> None:
        if puesto.is_set():  # si la pagina se recarga, no repetimos el menu
            return
        puesto.set()
        try:
            from PyObjCTools import AppHelper

            # Tocar el menu es tocar la interfaz: tiene que ir al hilo principal.
            AppHelper.callAfter(montar)
        except Exception as e:  # noqa: BLE001 - sin menu la app sigue siendo usable
            print(f"[cubomatica] no he podido montar el menu: {e}", file=sys.stderr)

    ventana.events.loaded += al_cargar


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
    ventana = webview.create_window(
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
    instalar_menu(ventana)

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
