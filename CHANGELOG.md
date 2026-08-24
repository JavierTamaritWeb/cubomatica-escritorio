# Registro de cambios

Todas las novedades reseñables de la app de escritorio. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
[semántico](https://semver.org/lang/es/).

Esta versión es la de **la app**, no la del juego: el juego lleva la suya propia
(`CB.VERSION`), que va por su cuenta y no la lee nadie desde Python.

---

## [4.2.0] — 2026-08-24

### Añadido

- Tres tests (`TestPantallaCompleta`) que protegen la pantalla completa: el
  fallo era intermitente, así que sin ellos una regresión pasaría por buena en
  cuanto un arranque saliera bien.

### Cambiado

- **La ventana arranca a pantalla completa**, lo mismo que al pulsar el botón
  verde. Antes solo se maximizaba: se quedaba debajo de la barra de menús y
  seguía enseñando el marco.
- **El contenido de las pantallas se centra en vertical** en lugar de quedarse
  pegado arriba con media pantalla vacía debajo.
- **Los créditos usan dos columnas** a partir de 1200 px de ancho. Aprovechan
  el ancho de un monitor sin alargar la línea de texto, que sigue en una medida
  cómoda de leer.

### Corregido

- La pantalla completa entraba unas veces sí y otras no. `fullscreen=True` de
  pywebview manda la orden antes de que la ventana esté en pantalla y macOS la
  descarta sin dar ningún error. Ahora se comprueba el `styleMask` de la
  ventana nativa y se reintenta.

### Notas técnicas

Centrar y desbordar a la vez esconde lo que sobresale por arriba y no hay forma
de llegar a ello, porque `scrollTop` no puede ser negativo. Por eso el centrado
es `justify-content: safe center`: centra mientras quepa y se comporta como
`start` en cuanto no quepa.

Las columnas de los créditos son columnas de flujo y no una rejilla: en rejilla
las filas se alinean por el panel más alto y uno largo deja un agujero al lado
del corto. Los paneles van como bloques en línea, que WebKit no parte nunca; con
`break-inside: avoid` a secas dejaba una tira vacía al pie de la columna.

---

## [4.1.0] — 2026-08-24

### Añadido

- **Menú «Juego» en la barra de macOS**, con accesos a *¿Quién juega?*,
  *Ajustes*, *Ayuda* y *Créditos*. Cada entrada llama a `CB.pantallas.ir()`, el
  mismo router que usan los botones del juego, y se declaran en la lista
  `MENU_PANTALLAS` de `main.py`.
- **README con portada, insignias e índice**, con capturas reales de la app.
- **CHANGELOG.md**, este archivo.

### Cambiado

- **La ventana arranca maximizada.** El juego está pensado para apaisado y a
  pantalla completa, así que ya no hay que redimensionar antes de jugar.
  `width` y `height` pasan a ser el tamaño al que vuelve la ventana si se
  restaura.
- La documentación corrige la ortografía: el texto venía sin tildes.

### Notas técnicas

El menú está construido a mano con PyObjC porque `webview.start(menu=...)` no
funciona en macOS con pywebview 5.3.2, y falla en silencio por dos motivos: el
menú se monta antes de crear la ventana y `_clear_main_menu()` lo borra, y los
objetos que reciben el clic se pierden por recolección de basura porque Cocoa no
retiene el `target` de un `NSMenuItem`.

---

## [4.0.0] — 2026-08-24

Primera versión de Cubomática como aplicación de escritorio. Deja de ser una web
y una PWA: se abre como cualquier app del Mac, funciona sin conexión y no abre
ningún puerto en el equipo.

### Añadido

- Ventana nativa con **pywebview** que carga el juego, empaquetada con
  **PyInstaller** como `Cubomatica.app` y firmada en local (obligatorio en
  Apple Silicon).
- Entorno reproducible con **uv**: librerías fijadas con `==`, Python 3.11 y
  uv ≥ 0.12.0 exigidos desde `pyproject.toml`.
- Icono del `.app` generado desde `assets/icon.svg`, el mismo dibujo que el
  favicon del juego, con el script `make-icon.sh`.
- Puente JavaScript ↔ Python en `api.py`, listo aunque el juego aún no lo use.
- 36 tests que protegen las decisiones que romperían la app en silencio.

### Corregido

- **`Error: 404 Not Found` al arrancar.** Al pasar la ruta suelta, pywebview
  levantaba un servidor HTTP interno en el puerto fijo 42001; con otra instancia
  viva, la ventana mostraba un 404 en lugar del juego. Ahora se carga con
  `file://` y no se levanta servidor alguno.
- **Ventana en blanco en el `.app`.** Dentro del bundle la web cuelga de un
  enlace simbólico que WKWebView no seguía. La ruta se resuelve con
  `.resolve()`.
- **Se perdía el progreso al cerrar.** `private_mode=False` es lo único que hace
  persistir `localStorage`, donde el juego guarda perfiles y avance.

[4.2.0]: #420--2026-08-24
[4.1.0]: #410--2026-08-24
[4.0.0]: #400--2026-08-24
