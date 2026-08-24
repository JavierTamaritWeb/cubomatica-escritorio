"""
Aqui va la LOGICA en Python.

Cada metodo publico de esta clase se puede llamar desde JavaScript asi:

    const resultado = await window.pywebview.api.saludar("Javi");

Reglas:
- Los metodos que empiezan por "_" NO se exponen a JavaScript.
- Los argumentos y el retorno deben ser tipos simples (str, int, list, dict, bool).

El juego actual es autocontenido y no usa este puente,
pero queda disponible para futuras funciones (guardar informes,
exportar progreso, dialogos de archivo...).
"""

import platform
from datetime import datetime


class Api:
    # ---------- EJEMPLO 1: devolver texto ----------
    def saludar(self, nombre: str) -> str:
        return f"Hola, {nombre}"

    # ---------- EJEMPLO 2: devolver un diccionario ----------
    def info_sistema(self) -> dict:
        return {
            "sistema": platform.system(),
            "version_python": platform.python_version(),
            "hora": datetime.now().strftime("%H:%M:%S"),
        }

    # ---------- EJEMPLO 3: abrir dialogo de archivo ----------
    def elegir_archivo(self) -> str | None:
        import webview

        ventana = webview.windows[0]
        resultado = ventana.create_file_dialog(webview.OPEN_DIALOG)
        if not resultado:
            return None
        return resultado[0]

    # ---------- metodo privado: NO visible desde JS ----------
    def _ayuda_interna(self) -> None:
        pass
