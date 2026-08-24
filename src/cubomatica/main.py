"""
Punto de entrada de la aplicacion.

Abre una ventana nativa que carga tu web (HTML + CSS + JS vanilla).
La apariencia visual es IDENTICA a la del navegador.
"""

import os
import sys
import threading
import time
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
# En macOS no se usa (ver arriba); en Windows/Linux, una carpeta oculta en casa.
STORAGE_DIR = Path.home() / ".cubomatica"

# Rotulos de pywebview. Su diccionario por defecto esta en ingles y se cuela
# en los dialogos nativos: el titulo del panel de guardar decia "Save file" en
# una aplicacion que por lo demas esta entera en espanol.
TEXTOS = {
    "global.quitConfirmation": "¿Seguro que quieres salir?",
    "global.ok": "Vale",
    "global.quit": "Salir",
    "global.cancel": "Cancelar",
    "global.saveFile": "Guardar fichero",
    "cocoa.menu.about": "Acerca de",
    "cocoa.menu.services": "Servicios",
    "cocoa.menu.view": "Ver",
    "cocoa.menu.hide": "Ocultar",
    "cocoa.menu.hideOthers": "Ocultar los demás",
    "cocoa.menu.showAll": "Mostrar todo",
    "cocoa.menu.quit": "Salir",
    "cocoa.menu.fullscreen": "Pantalla completa",
}

# Constantes de Cocoa. Se escriben aqui para no importar AppKit al arrancar
# (en Windows y Linux ni existe) y para que el numero lleve su nombre al lado.
MASCARA_PANTALLA_COMPLETA = 1 << 14        # NSWindowStyleMaskFullScreen
COMPORTAMIENTO_PANTALLA_COMPLETA = 1 << 7  # NSWindowCollectionBehaviorFullScreenPrimary


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


def pantalla_completa(ventana) -> None:
    """
    Abre el juego a pantalla completa, igual que al pulsar el boton verde.

    NO sirve fullscreen=True de create_window. pywebview llama a
    toggleFullScreen_ antes de que la ventana este en pantalla y macOS
    descarta la orden sin avisar. Tampoco basta con pedirlo una vez desde el
    evento shown: arrancando varias veces se ve que unas entra y otras se
    queda en 1280x800, porque la orden puede llegar antes de que el bucle de
    eventos de Cocoa este corriendo.

    Asi que en vez de pedirlo se COMPRUEBA: se mira el styleMask de la ventana
    nativa, que es la unica fuente fiable de si esta o no a pantalla completa,
    y se insiste hasta que lo diga. Cuatro intentos, unos siete segundos como
    mucho; en la practica entra al primero.

    Todo lo que toca AppKit va por AppHelper.callAfter, porque es interfaz y
    solo se puede tocar desde el hilo principal. El hilo de aqui unicamente
    duerme entre intentos: hacerlo en el hilo de la interfaz la congelaria.
    """
    if sys.platform != "darwin":
        return

    lanzado = threading.Event()

    def al_mostrar(*_) -> None:
        if lanzado.is_set():  # una recarga no vuelve a lanzar esto
            return
        lanzado.set()

        logrado = threading.Event()

        def ventana_nativa():
            import AppKit

            for candidata in AppKit.NSApplication.sharedApplication().windows():
                if candidata.title() == ventana.title:
                    return candidata
            return None

        def comprobar() -> None:
            nativa = ventana_nativa()
            if nativa is not None and nativa.styleMask() & MASCARA_PANTALLA_COMPLETA:
                logrado.set()

        def entrar() -> None:
            nativa = ventana_nativa()
            if nativa is None or nativa.styleMask() & MASCARA_PANTALLA_COMPLETA:
                return  # ya esta: volver a pedirlo la SACARIA de pantalla completa
            nativa.setCollectionBehavior_(COMPORTAMIENTO_PANTALLA_COMPLETA)
            nativa.toggleFullScreen_(None)

        def ejecutar() -> None:
            from PyObjCTools import AppHelper

            for _ in range(4):
                AppHelper.callAfter(comprobar)
                time.sleep(0.3)
                if logrado.is_set():
                    return
                AppHelper.callAfter(entrar)
                time.sleep(1.5)  # la animacion de macOS tarda cerca de un segundo

            AppHelper.callAfter(comprobar)
            time.sleep(0.3)
            if not logrado.is_set():
                print("[cubomatica] no he podido ir a pantalla completa", file=sys.stderr)

        threading.Thread(target=ejecutar, daemon=True).start()

    ventana.events.shown += al_mostrar


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
        # La pantalla completa NO se pide aqui (ver pantalla_completa mas abajo).
        # width/height son el tamano al que vuelve la ventana al salir de ella.
        width=1280,
        height=800,
        min_size=(1024, 640),  # el juego esta pensado para apaisado
        resizable=True,
        confirm_close=False,
        # text_select viene apagado por defecto en pywebview, que inyecta
        #   body { -webkit-user-select: none; cursor: default; }
        # en CUALQUIER pagina. Eso deja el panel de personas adultas -texto
        # legal, metricas, recomendaciones- imposible de seleccionar y de
        # copiar. Se enciende aqui y es el CSS del juego el que decide donde
        # vale la pena (.pantalla--documento y los creditos): en las pantallas
        # de juego la seleccion sigue apagada, porque arrastrar sobre un
        # bloque de respuesta pintaria el texto en azul.
        text_select=True,
    )

    # El puente necesita la ventana para los dialogos nativos y para imprimir.
    # Es un metodo privado: no llega a JavaScript.
    api._asociar(ventana)

    # private_mode=False es CRITICO: es lo UNICO que hace que localStorage
    # persista. Con private_mode=True el backend Cocoa usa un almacen
    # no persistente y el juego pierde perfiles y progreso al cerrar.
    # DevTools solo bajo demanda:  CUBOMATICA_DEBUG=1 uv run cubomatica
    pantalla_completa(ventana)
    instalar_menu(ventana)

    opciones = {
        "private_mode": False,
        "debug": os.environ.get("CUBOMATICA_DEBUG") == "1",
        # Los rotulos que pone pywebview. Los botones de los dialogos (Cancelar,
        # Guardar, Imprimir) los pone macOS y NO se traducen desde aqui: eso lo
        # decide CFBundleLocalizations en Cubomatica.spec.
        "localization": TEXTOS,
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
