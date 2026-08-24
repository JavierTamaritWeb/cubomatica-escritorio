"""
Puente JavaScript -> Python.

Cada metodo PUBLICO de esta clase llega a JavaScript como

    await window.pywebview.api.<nombre>(...)

Reglas del puente:
- Los metodos que empiezan por "_" NO se exponen a JavaScript.
- Los argumentos y el retorno deben ser tipos simples (str, int, list, dict, bool):
  pywebview los serializa como JSON, y algo raro falla en silencio.
- Esperar en JS al evento "pywebviewready": window.pywebview.api no existe
  todavia cuando la pagina termina de cargar.

Hasta 4.8.2 la clase estaba VACIA a proposito: el juego era autocontenido. Ya
no lo es, y por una razon concreta. El panel de personas adultas ofrece cuatro
salidas al mundo (informe imprimible, CSV, copia .json, restaurar copia) y bajo
WKWebView tres de ellas no funcionaban:

- window.print() no esta implementado en WKWebView. No lanza excepcion: no
  hace absolutamente nada, que es la peor forma de fallar.
- La descarga por <a download href="blob:..."> es PEOR que inutil. WKWebView
  no descarga: NAVEGA a la URL del blob. La ventana se iba del juego, pintaba
  el CSV como texto plano y ya no habia forma de volver: no hay barra de
  direcciones ni boton de atras, y el juego entero desaparecia hasta reabrir
  la aplicacion. Comprobado con una sonda que pulsa el boton de verdad.

De ahi los dos metodos de abajo. En un navegador normal el juego sigue usando
su camino de siempre: JS solo llama aqui si el puente existe.

tests/test_api.py protege el contrato publico/privado y comprueba que las
firmas solo pidan tipos serializables como JSON.
"""

import sys
from pathlib import Path

import webview


class Api:
    def __init__(self) -> None:
        # Con guion bajo: NO se expone a JavaScript. Lo rellena main.py en
        # cuanto existe la ventana, porque los dialogos nativos y la impresion
        # cuelgan de ella.
        self._ventana = None

    def _asociar(self, ventana) -> None:
        self._ventana = ventana

    # ------------------------------------------------------------------
    # Guardar un fichero con el dialogo nativo del sistema.
    # Sustituye a la descarga por blob, que en WKWebView se lleva por delante
    # la pagina entera. Devuelve siempre un dict, nunca lanza: quien llama es
    # JavaScript y una excepcion aqui solo deja una promesa rechazada.
    # ------------------------------------------------------------------
    def guardar_texto(self, nombre: str, contenido: str) -> dict:
        if self._ventana is None:
            return {"ok": False, "motivo": "sin ventana"}
        try:
            elegido = self._ventana.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=str(Path.home() / "Downloads"),
                save_filename=nombre,
            )
        except Exception as e:  # noqa: BLE001 - el puente no debe romperse nunca
            return {"ok": False, "motivo": str(e)}

        # El dialogo devuelve None si se cancela. Segun backend, una cadena o
        # una secuencia de una sola cadena.
        if not elegido:
            return {"ok": False, "motivo": "cancelado"}
        ruta = Path(elegido if isinstance(elegido, str) else elegido[0])

        try:
            ruta.write_text(contenido, encoding="utf-8")
        except OSError as e:
            return {"ok": False, "motivo": str(e)}
        return {"ok": True, "ruta": str(ruta), "nombre": ruta.name}

    # ------------------------------------------------------------------
    # Leer un fichero con el dialogo nativo. Es la pareja de guardar_texto,
    # para restaurar una copia de seguridad.
    #
    # El <input type="file"> del HTML tambien funciona bajo WKWebView -pywebview
    # implementa runOpenPanelWithParameters-, pero solo si el clic viene de un
    # gesto humano de verdad: WebKit exige activacion del usuario para abrir el
    # selector, y aqui el clic lo dispara JavaScript desde el manejador del
    # boton. Eso deja el boton pendiendo de un hilo. Por el puente no hay
    # gesto que valga.
    # ------------------------------------------------------------------
    TOPE_BYTES = 2 * 1024 * 1024

    def abrir_texto(self, extension: str) -> dict:
        if self._ventana is None:
            return {"ok": False, "motivo": "sin ventana"}
        sufijo = extension if extension.startswith(".") else "." + extension
        try:
            elegido = self._ventana.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=(f"Copia de Cubomática (*{sufijo})",),
            )
        except Exception as e:  # noqa: BLE001 - el puente no debe romperse nunca
            return {"ok": False, "motivo": str(e)}

        if not elegido:
            return {"ok": False, "motivo": "cancelado"}
        ruta = Path(elegido if isinstance(elegido, str) else elegido[0])

        try:
            # El tamano se mira ANTES de leer: una copia de Cubomatica son unos
            # kilobytes, y no hay razon para cargar en memoria lo que sea que
            # alguien haya elegido por error.
            if ruta.stat().st_size > self.TOPE_BYTES:
                return {"ok": False, "motivo": "demasiado grande"}
            contenido = ruta.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return {"ok": False, "motivo": str(e)}
        return {"ok": True, "nombre": ruta.name, "contenido": contenido}

    # ------------------------------------------------------------------
    # Imprimir lo que se ve. El panel de impresion de macOS incluye
    # "PDF -> Guardar como PDF", asi que esto cubre tambien el informe en
    # papel electronico sin escribir un generador de PDF.
    # ------------------------------------------------------------------
    def imprimir(self) -> dict:
        if sys.platform != "darwin":
            return {"ok": False, "motivo": "sistema"}
        if self._ventana is None:
            return {"ok": False, "motivo": "sin ventana"}
        try:
            import AppKit
            from PyObjCTools import AppHelper
        except ImportError:
            return {"ok": False, "motivo": "sin PyObjC"}

        nativa = getattr(self._ventana, "native", None)
        if nativa is None:
            return {"ok": False, "motivo": "sin ventana nativa"}
        vista = nativa.contentView()
        # printOperationWithPrintInfo: es de WKWebView (macOS 11+). Si no
        # esta, se dice y JavaScript avisa al adulto en vez de callarse.
        if not hasattr(vista, "printOperationWithPrintInfo_"):
            return {"ok": False, "motivo": "sin impresion"}

        def montar() -> None:
            info = AppKit.NSPrintInfo.sharedPrintInfo().copy()
            # La ventana es apaisada y ancha; sin esto el informe sale cortado
            # por la derecha. El nombre de la constante cambio de nombre entre
            # versiones del SDK, de ahi el getattr.
            ajustar = getattr(AppKit, "NSPrintingPaginationModeFit",
                              getattr(AppKit, "NSFitPagination", None))
            if ajustar is not None:
                info.setHorizontalPagination_(ajustar)
            info.setHorizontallyCentered_(False)
            info.setVerticallyCentered_(False)
            operacion = vista.printOperationWithPrintInfo_(info)
            operacion.setShowsPrintPanel_(True)
            operacion.setShowsProgressPanel_(True)
            try:
                # Como lamina sobre la ventana: no bloquea el hilo de interfaz.
                operacion.runOperationModalForWindow_delegate_didRunSelector_contextInfo_(
                    nativa, None, None, None
                )
            except Exception:  # noqa: BLE001 - hay SDK donde la firma no cuadra
                operacion.runOperation()

        def lanzar() -> None:
            # Corre en el hilo principal DESPUES de haber devuelto ok: True.
            # Una excepcion aqui no llega a JavaScript, asi que al menos se
            # deja escrita en vez de perderse en silencio.
            try:
                montar()
            except Exception as exc:  # noqa: BLE001 - se traza, no se oculta
                print(f"[cubomatica] imprimir(): {exc!r}", file=sys.stderr)

        # Todo lo que toca AppKit va al hilo principal, como en main.py.
        AppHelper.callAfter(lanzar)
        return {"ok": True}
