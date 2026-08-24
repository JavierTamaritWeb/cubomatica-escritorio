#!/usr/bin/env python3
"""
Deja index.html legible sin cambiar lo que el navegador pinta.

Aquí no hay minificador, así que el HTML minificado NO tiene gemelo: es el
único fichero del bundle que no se puede leer. Esto lo desminifica en el sitio.

La regla que gobierna todo: en HTML el espacio en blanco SE VE. Entre dos
elementos en línea, un salto de línea con sangría es un espacio de verdad, y
donde no había ninguno aparece un hueco que antes no estaba. Por eso:

- Los elementos de texto (p, h1, li, button…) salen ENTEROS en una línea. No se
  toca ni un espacio de su interior.
- Un elemento con contenido mixto (texto suelto junto a etiquetas) también sale
  entero: repartirlo en líneas movería sus espacios.
- Solo se parten los contenedores cuyos hijos son todos elementos, que es donde
  el espacio en blanco no se pinta.

Uso:
    python3 herramientas/formatear-html.py src/cubomatica/web/index.html
    python3 herramientas/formatear-html.py --comprobar <fichero>   # sin escribir
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

SANGRIA = "  "

# Etiquetas que se cierran solas.
VACIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
          "link", "meta", "source", "track", "wbr"}

# Elementos de texto: su interior no se toca jamás.
DE_TEXTO = {"a", "b", "button", "code", "em", "h1", "h2", "h3", "h4", "h5",
            "h6", "i", "label", "li", "p", "script", "small", "span", "strong",
            "sub", "sup", "title"}


class Arbol(HTMLParser):
    """Construye el árbol. convert_charrefs deja las entidades ya resueltas."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.raiz: list = []
        self.pila: list[list] = [self.raiz]
        self.doctype = ""

    def _meter(self, nodo) -> None:
        self.pila[-1].append(nodo)

    def handle_decl(self, decl: str) -> None:
        self.doctype = f"<!{decl}>"

    def handle_starttag(self, tag, attrs) -> None:
        nodo = {"tag": tag, "attrs": attrs, "hijos": []}
        self._meter(nodo)
        if tag not in VACIAS:
            self.pila.append(nodo["hijos"])

    def handle_startendtag(self, tag, attrs) -> None:
        self._meter({"tag": tag, "attrs": attrs, "hijos": []})

    def handle_endtag(self, tag) -> None:
        if tag not in VACIAS and len(self.pila) > 1:
            self.pila.pop()

    def handle_data(self, data: str) -> None:
        self._meter(data)

    def handle_comment(self, data: str) -> None:
        self._meter({"comentario": data})


def escapar_texto(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escapar_atributo(t: str) -> str:
    # Solo lo imprescindible. Escapar la comilla simple destrozaría el data-uri
    # del favicon, que va lleno de ellas dentro de comillas dobles.
    return t.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def apertura(nodo) -> str:
    partes = [nodo["tag"]]
    for nombre, valor in nodo["attrs"]:
        if valor is None:  # data-salir, hidden: sin valor a propósito
            partes.append(nombre)
        else:
            partes.append(f'{nombre}="{escapar_atributo(valor)}"')
    return "<" + " ".join(partes) + ">"


def en_una_linea(nodo) -> str:
    if isinstance(nodo, str):
        return escapar_texto(nodo)
    if "comentario" in nodo:
        return f"<!--{nodo['comentario']}-->"
    dentro = "".join(en_una_linea(h) for h in nodo["hijos"])
    if nodo["tag"] in VACIAS:
        return apertura(nodo)
    return f"{apertura(nodo)}{dentro}</{nodo['tag']}>"


def se_parte(nodo) -> bool:
    """Solo se parte lo que no tiene texto propio."""
    if isinstance(nodo, str) or "comentario" in nodo:
        return False
    if nodo["tag"] in DE_TEXTO or nodo["tag"] in VACIAS:
        return False
    hijos = nodo["hijos"]
    if not any(isinstance(h, dict) for h in hijos):
        return False
    # Contenido mixto: texto de verdad conviviendo con etiquetas.
    return not any(isinstance(h, str) and h.strip() for h in hijos)


def escribir(nodo, nivel: int, salida: list[str]) -> None:
    margen = SANGRIA * nivel
    if not se_parte(nodo):
        texto = en_una_linea(nodo)
        if texto.strip():
            salida.append(margen + texto.strip())
        return
    salida.append(margen + apertura(nodo))
    for hijo in nodo["hijos"]:
        if isinstance(hijo, str) and not hijo.strip():
            continue  # espacio entre etiquetas: lo repone la sangría
        escribir(hijo, nivel + 1, salida)
    salida.append(f"{margen}</{nodo['tag']}>")


def formatear(html: str) -> str:
    arbol = Arbol()
    arbol.feed(html)
    arbol.close()
    salida: list[str] = []
    if arbol.doctype:
        salida.append(arbol.doctype)
    for nodo in arbol.raiz:
        if isinstance(nodo, str) and not nodo.strip():
            continue
        escribir(nodo, 0, salida)
    return "\n".join(salida) + "\n"


# Elementos de nivel en línea: entre dos de ellos, un espacio SÍ se pinta.
EN_LINEA = {"a", "b", "button", "code", "em", "i", "img", "input", "label",
            "small", "span", "strong", "sub", "sup"}


def huella(html: str):
    """
    Lo que no puede cambiar: la secuencia de etiquetas con sus atributos y los
    trozos de texto, en orden.

    Cuenta cada trozo por separado a propósito. Concatenarlo todo en una
    cadena y comparar palabras da un falso positivo en cuanto dos elementos
    pegados —`…divertidas</title><p>Gira…`— dejan de estarlo: el texto es el
    mismo y la comparación dice que no.
    """
    piezas: list = []

    class Cosecha(HTMLParser):
        def handle_starttag(self, tag, attrs):
            piezas.append(("etiqueta", tag, tuple(attrs)))

        handle_startendtag = handle_starttag

        def handle_endtag(self, tag):
            piezas.append(("cierre", tag))

        def handle_data(self, data):
            if data.strip():
                piezas.append(("texto", data))

    c = Cosecha(convert_charrefs=True)
    c.feed(html)
    c.close()
    return piezas


def espacios_que_se_verian(nodo, hallazgos: list) -> None:
    """
    Busca los sitios donde el formateo metería un espacio VISIBLE: dos
    elementos en línea que estaban pegados y pasan a tener un salto de línea
    entre medias. Dentro de un contenedor flex o grid da igual —el espacio en
    blanco suelto no es un ítem— pero en uno normal abre un hueco.

    No aborta: no puede saber desde aquí qué display tiene cada caja. Lo
    imprime para que se mire el CSS antes de dar el cambio por bueno.
    """
    if isinstance(nodo, str) or "comentario" in nodo:
        return
    if se_parte(nodo):
        anterior = None
        pegado = False
        for hijo in nodo["hijos"]:
            if isinstance(hijo, str):
                if not hijo.strip():
                    pegado = False
                continue
            if "comentario" in hijo:
                continue
            if anterior is not None and pegado:
                if anterior["tag"] in EN_LINEA and hijo["tag"] in EN_LINEA:
                    señas = dict(nodo["attrs"])
                    hallazgos.append(
                        f"<{nodo['tag']} class=\"{señas.get('class', '')}\">: "
                        f"{anterior['tag']} + {hijo['tag']}"
                    )
            anterior = hijo
            pegado = True
    for hijo in nodo["hijos"]:
        if isinstance(hijo, dict):
            espacios_que_se_verian(hijo, hallazgos)


def main() -> int:
    argumentos = sys.argv[1:]
    comprobar = "--comprobar" in argumentos
    rutas = [a for a in argumentos if not a.startswith("--")]
    if not rutas:
        print(__doc__.strip())
        return 2

    pendientes = 0
    for ruta in map(Path, rutas):
        original = ruta.read_text(encoding="utf-8")
        nuevo = formatear(original)

        # Red de seguridad: mismas etiquetas, mismos atributos, mismo texto y
        # en el mismo orden; y el resultado tiene que volver a formatearse
        # igual, o el fichero bailaría en cada pasada.
        if huella(original) != huella(nuevo):
            print(f"ABORTADO: {ruta} cambiaría de contenido", file=sys.stderr)
            return 1
        if formatear(nuevo) != nuevo:
            print(f"ABORTADO: {ruta} no es estable al reformatear", file=sys.stderr)
            return 1

        arbol = Arbol()
        arbol.feed(original)
        arbol.close()
        hallazgos: list[str] = []
        for nodo in arbol.raiz:
            if isinstance(nodo, dict):
                espacios_que_se_verian(nodo, hallazgos)
        if hallazgos:
            print(f"AVISO: {ruta} mete un salto entre elementos en línea pegados.")
            print("       Se ve como un espacio salvo que la caja sea flex o grid:")
            for h in dict.fromkeys(hallazgos):
                print(f"       - {h}")

        if comprobar:
            estado = "ya está formateado" if original == nuevo else "haría falta formatearlo"
            print(f"{ruta}: {estado}")
            if original != nuevo:
                pendientes += 1
        else:
            ruta.write_text(nuevo, encoding="utf-8")
            print(f"{ruta}: {original.count(chr(10)) + 1} -> {nuevo.count(chr(10))} líneas")
    return 1 if pendientes else 0


if __name__ == "__main__":
    raise SystemExit(main())
