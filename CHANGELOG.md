# Registro de cambios

Todas las novedades reseñables de la app de escritorio. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
[semántico](https://semver.org/lang/es/).

Esta versión es la de **la app**, no la del juego: el juego lleva la suya propia
(`CB.VERSION`), que va por su cuenta y no la lee nadie desde Python.

---

## [4.3.0] — 2026-08-24

### Cambiado

- **El juego se lee con OpenDyslexic**, la tipografía pensada para que las
  letras no se confundan entre sí. Viaja dentro del paquete (256 KB, cuatro
  variantes), así que se ve igual en cualquier Mac aunque no la tenga
  instalada.
- **Los botones, los rótulos de la barra de estado y el nombre de la veta van
  en mayúsculas.**
- **La barra de estado de la partida se puede entender sin que nadie te la
  explique.** Tenía cuatro indicadores y ninguna palabra: tres cuadrados
  azules, veinte cuadraditos grises de 10 px, un número suelto y otro cuadrado
  azul. Ahora cada uno lleva su rótulo debajo: *Vidas*, *Pregunta 3 de 20*,
  *Segundos* y *Gemas*.
- **La gema deja de ser igual que una luz encendida.** Las dos eran un cuadrado
  de cristal con el mismo bisel y solo se distinguían por el tamaño. La gema
  pasa a rombo de oro.
- Los cuadraditos del avance pasan de 10 px a 16 px: se leían como una textura,
  no como una cuenta.

### Corregido

- El avance decía «0 de 20» con la primera pregunta delante. Contaba las
  hechas, no en cuál estabas.

### Añadido

- **`index.html` deja de estar minificado** y se puede revisar. Era el único
  fichero del bundle sin gemelo sin minificar: 21 KB en una sola línea.
- `herramientas/formatear-html.py`, que lo formatea sin cambiar lo que el
  navegador pinta, y tres tests que avisan si vuelve a quedar en una línea.
- El crédito a OpenDyslexic en la pantalla de Créditos y el texto de su
  licencia en `web/fonts/`, que la CC BY 3.0 obliga a acompañar.
- Doce tests (`TestTipografia`) que comprueban que las cuatro variantes viajan
  en el paquete, que el CSS las declara con ruta relativa y que el crédito
  sigue en pantalla.

### Notas técnicas

La fuente va dentro del paquete y no se busca en el sistema: la app se abre en
el Mac de otra persona, donde puede no estar instalada. Si faltara un `.otf` no
saltaría ningún error —WebKit se cae a Verdana y el juego sigue funcionando—,
así que lo comprueban los tests. Las rutas son relativas: una absoluta funciona
sobre HTTP y bajo `file://` no carga nada.

Con OpenDyslexic hubo que retocar dos variables. El juego separaba las letras
`.05em` y las palabras `.16em`, que está bien pensado para Verdana, donde
separar ayuda a leer; OpenDyslexic ya trae esa separación de fábrica y, sumadas,
dejaban las palabras flotando sueltas. Pasan a `0` y `.06em`.

Los rótulos dicen para qué sirve cada cosa, no cómo se llama en la ficción del
juego. «Luces» es el nombre de las luces del casco y hay que habérselo leído en
la Ayuda para saber que son las vidas; «Vidas» se entiende sin nada. Por lo
mismo el reloj sigue contando segundos en vez de pasar a `1:19`: la notación
minutos:segundos no se ha dado en 2.º de Primaria, donde el reloj se ve a la
hora y a la media. Y el avance dice «Pregunta 3 de 20» y no «3/20», que es una
fracción y tampoco se ha dado.

El tamaño del rótulo sale de `calc(var(--tam-texto-min) * .8)` en vez de los
12 px de los botones de la barra de abajo, así «Letra grande» también lo
agranda. Van en mayúsculas, con algo más de espaciado entre letras que el
general del juego, que está pensado para minúsculas.

En HTML el espacio en blanco se ve: entre dos elementos en línea, un salto de
línea con sangría es un espacio de verdad, y donde no había ninguno abre un
hueco. Por eso el formateador no toca el interior de los elementos de texto ni
reparte el contenido mixto, y solo parte los contenedores cuyos hijos son todos
elementos. Además avisa de cada sitio donde mete un salto entre dos elementos en
línea que estaban pegados, para mirar el CSS de esa caja: dentro de un flex el
espacio suelto no es un ítem y da igual, en una caja normal se ve.

De los catorce contenedores afectados, trece eran flex y el otro tenía un solo
hijo. El que sí importaba era `.contenido__paneles` de los créditos, cuyos
paneles son bloques en línea: ahora lleva `line-height: 0` y cada panel se lo
devuelve para su contenido, así que el salto entre ellos mide cero.

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

[4.3.0]: #430--2026-08-24
[4.2.0]: #420--2026-08-24
[4.1.0]: #410--2026-08-24
[4.0.0]: #400--2026-08-24
