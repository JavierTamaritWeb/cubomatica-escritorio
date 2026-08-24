# Cubomática 4.0.0

App **de escritorio** del juego **Cubomática** (matemáticas de Educación Primaria).
Carga la web del juego (HTML + CSS + JS vanilla) en una ventana nativa con pywebview.
**La apariencia visual es identica a la del navegador.**

Ya no es una web ni una PWA: se instala y se abre como cualquier app del Mac,
funciona sin conexion y no abre ningun puerto en el equipo.

| | |
|---|---|
| Version de la app | **4.0.0** (`pyproject.toml` y `Cubomatica.spec`) |
| Version del juego | `CB.VERSION` dentro del bundle web (hoy 3.4.7) |
| Identificador | `es.javiertamarit.cubomatica` |

Son dos numeros distintos a proposito: esta app empaqueta el juego, pero el juego
se versiona en su propio proyecto. Un test comprueba que las dos declaraciones de
la version de la app no se desincronicen.

---

## 1. Instalar `uv` (una sola vez)

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Comprobar:
```bash
uv --version
```

Este proyecto exige **uv 0.12.0 o superior**.
Si tienes uno mas viejo, uv te avisa y no continua. Actualiza con:
```bash
uv self update
```

---

## 2. Instalar el proyecto

Desde la carpeta del proyecto:

```bash
uv sync
```

Esto hace 3 cosas solo:
1. Crea el entorno virtual en `.venv/`
2. Instala las librerias del `pyproject.toml`
3. Crea `uv.lock` con las versiones exactas

**No hace falta activar el entorno.** `uv` lo hace por ti.

---

## 3. Ejecutar

```bash
uv run cubomatica
```

O tambien:
```bash
uv run python -m cubomatica.main
```

Con DevTools (inspeccionar elemento):
```bash
CUBOMATICA_DEBUG=1 uv run cubomatica
```

---

## 4. Pasar los tests

```bash
uv run pytest
```

Los tests comprueban:
- La logica de `api.py`
- Que los metodos privados NO se exponen a JavaScript
- Que existen `index.html`, CSS, JS, imagenes y audio
- Que las rutas son relativas (si no, el .app se abre en blanco)
- Que `main.py` desactiva el modo privado (si no, se pierde el progreso)
- Que la ventana carga con `file://` (si no, sale un 404 al chocar de puertos)
- Que la version de `pyproject.toml` y la del `.spec` coinciden
- Que todas las librerias tienen version fija

Con informe de cobertura:
```bash
uv run pytest --cov=cubomatica --cov-report=term-missing
```

---

## Comandos utiles

| Que quiero | Comando |
|---|---|
| Anadir una libreria | `uv add nombre-libreria` |
| Quitar una libreria | `uv remove nombre-libreria` |
| Anadir libreria de desarrollo | `uv add --dev nombre-libreria` |
| Ver librerias instaladas | `uv pip list` |
| Actualizar el lock | `uv lock --upgrade` |
| Instalar exacto que el lock | `uv sync --frozen` |
| Pasar los tests | `uv run pytest` |
| Un solo test | `uv run pytest tests/test_api.py -v` |

---

## Estructura

```
cubomatica/
├── pyproject.toml          <- ficha del proyecto + librerias + version de uv
├── uv.lock                 <- versiones exactas (lo crea uv)
├── .python-version         <- version de Python fijada (3.11)
├── .gitignore
├── README.md
├── CLAUDE.md               <- guia para Claude Code
├── EMPAQUETAR-MAC.md
├── Cubomatica.spec         <- config del .app de Mac
├── build-mac.sh            <- construye dist/Cubomatica.app
├── make-icon.sh            <- regenera el icono desde assets/icon.svg
├── assets/
│   ├── icon.svg            <- dibujo del icono (igual que el favicon)
│   └── icon.icns           <- icono del .app (lo genera make-icon.sh)
├── tests/
│   ├── conftest.py         <- fixtures compartidas
│   ├── test_api.py         <- logica Python
│   └── test_web.py         <- archivos web + rutas + persistencia
└── src/
    └── cubomatica/
        ├── __init__.py
        ├── main.py         <- abre la ventana
        ├── api.py          <- puente JS <-> Python (listo para el futuro)
        └── web/            <- EL JUEGO, tal cual
            ├── index.html
            ├── manifest.webmanifest
            ├── css/        <- cubomatica.css + cubomatica.min.css
            ├── js/         <- cubomatica.js + cubomatica.min.js
            ├── img/        <- piezas (webp)
            └── audio/      <- musica (mp3, ~42 MB)
```

---

## Como se carga el juego (y por que con `file://`)

`main.py` abre la ventana con `url=index.as_uri()`, es decir un `file://`.

Si se le pasa la ruta suelta (`/Users/.../index.html`), pywebview la considera
"local" y **levanta un servidor HTTP interno**. Con `private_mode=False` ese
servidor usa siempre el **puerto fijo 42001**, asi que basta con que quede otra
instancia viva para que la siguiente no pueda abrirlo y la ventana muestre
`Error: 404 Not Found` en lugar del juego.

Con `file://` no hay servidor, no hay puerto y no queda ningun socket a la
escucha en el equipo. La ruta se resuelve ademas con `.resolve()`: dentro del
`.app` la web cuelga de un enlace simbolico (`Contents/Frameworks` ->
`Contents/Resources`) y WKWebView no lo carga bien sin resolver.

---

## Donde se guarda el progreso

El juego guarda perfiles, progreso y ajustes en `localStorage`.
Lo unico que hace que persista es arrancar con **`private_mode=False`**: con el
modo privado, el backend Cocoa usa un almacen no persistente y se pierde TODO al
cerrar.

**`storage_path` no tiene efecto en macOS.** pywebview lo ignora aqui: usa
siempre `WKWebsiteDataStore.defaultDataStore()`, que guarda en

```
~/Library/WebKit/<identificador del bundle>/WebsiteData/
```

Se mantiene en el codigo porque en Windows y Linux si se respeta.

Consecuencia practica: el `.app` (`es.javiertamarit.cubomatica`) y el modo
desarrollo (`org.python.python`) **no comparten progreso**. Son dos almacenes
distintos. Es lo esperable: asi las pruebas no ensucian la partida real.

---

## Como conectar JavaScript con Python

El juego actual es autocontenido y no usa el puente, pero queda listo:

**En Python** (`api.py`) — creas un metodo:
```python
class Api:
    def saludar(self, nombre: str) -> str:
        return f"Hola, {nombre}"
```

**En JavaScript** — lo llamas:
```javascript
const texto = await window.pywebview.api.saludar("Javi");
```

**Regla clave:** espera siempre al evento `pywebviewready` antes de usar la API.

---

## Limitaciones conocidas (escritorio)

- **Imprimir el informe** (`window.print()`): WKWebView (macOS) no implementa
  `window.print()`. El boton «Imprimir» del informe no hace nada dentro de la app.
  Posible mejora futura: exponer la impresion via `api.py`.
- **Service worker** (`sw.js`): la web lo registra si el navegador lo soporta;
  dentro de la app (protocolo `file://`) no se activa. Es inofensivo:
  la app ya funciona 100 % sin conexion.

---

## Requisitos por sistema operativo

| Sistema | Motor web | Instalar algo |
|---|---|---|
| Windows | WebView2 (Edge) | Normalmente ya viene en Win 10/11 |
| macOS | WebKit | Nada, ya viene |
| Linux | GTK + WebKit2 | `sudo apt install python3-gi gir1.2-webkit2-4.1` |

---

## Empaquetar en .exe / .app

Ver **EMPAQUETAR-MAC.md** para el paso a paso completo de macOS:

```bash
./build-mac.sh        # -> dist/Cubomatica.app
```

En Windows (desde un Windows):
```bash
uv run pyinstaller --noconfirm --windowed --name "Cubomatica" ^
  --add-data "src/cubomatica/web;cubomatica/web" ^
  src/cubomatica/main.py
```

---

## Que versiones estan controladas

| Que | Donde | Valor |
|---|---|---|
| Librerias | `pyproject.toml` | `pywebview==5.3.2` |
| Versiones exactas de TODO | `uv.lock` | lo genera uv |
| Version de Python | `.python-version` | `3.11` |
| Version de la herramienta uv | `pyproject.toml` -> `[tool.uv]` | `>=0.12.0` |

Los 4 archivos deben subirse a git. Incluido `uv.lock`.
