# Registro de cambios

Todas las novedades reseñables de la app de escritorio. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
[semántico](https://semver.org/lang/es/).

Esta versión es la de **la app**, no la del juego: el juego lleva la suya propia
(`CB.VERSION`), que va por su cuenta y no la lee nadie desde Python.

---

## [4.5.0] — 2026-08-24

Una auditoría a fondo de todo el proyecto: el shell de Python, el empaquetado,
los documentos y —sobre todo— el bundle del juego, con los 308 niveles
fuzzeados (unos 277 000 ítems generados) y una comparación mecánica de los
gemelos `.min` con sus copias legibles. La base salió muy sana: ni un
`Math.random` en los generadores, ni fugas de temporizadores, ni claves de
`localStorage` fuera de `CB.almacen`, gemelos sin derivas. Lo que sí había son
los veintidós errores de abajo, y están todos corregidos.

### Corregido

**Lo que un niño veía:**

- **La tarjeta de reparación de dinero pintaba los billetes como monedas y sin
  fotografía.** Construía las piezas a mano, sin el `data-valor` con el que el
  CSS carga la imagen, y con la clase de moneda aunque llegara un billete de
  50 €. Ahora usa `CB.ui.pieza`, el mismo ayudante que el resto del juego.
- **Los Créditos decían «Cero ficheros de imagen»** con doce webp de monedas y
  billetes en el bundle. Ahora dicen la verdad.
- En pantallas de menos de 480 px de ancho, la barra de avance enseñaba **a la
  vez** los bloquecitos y el contador de texto que debía sustituirlos: un
  `display` suelto y una caja sin condición anulaban el modo compacto.

**Accesibilidad:**

- Con **«Alto contraste»**, los tres resaltes dorados (la línea activa del
  enunciado, la columna CDU activa y la cara de ánimo elegida) quedaban en
  blanco sobre oro claro: 1,9:1, ilegible justo en el modo que promete lo
  contrario. Llevan ahora color explícito.
- El **«+N por rapidez»** flotaba en oro oscuro sobre el cielo (menos de 2:1 de
  contraste; sobre el césped, casi invisible). Va ahora en placa oscura.
- Los **cromos bloqueados** del álbum estaban a 3,4:1. Ahora en negro.
- **«Letra grande» no escalaba seis textos** que iban en píxeles fijos: los
  rótulos Pista, Pausa y Sonido, el nombre de la veta, los cromos, el
  distintivo de ampliación y la marca del glosario. Todos atados ahora a
  `--tam-texto-min`, conservando su tamaño de siempre.
- El botón de sonido decía **«Sonido» en pantalla y «Silenciar» al lector de
  pantalla**. Ahora dicen lo mismo.

**Reglas que no hacían lo que decían:**

- La adaptación del visor de respuesta a ventanas bajas estaba escrita *antes*
  del bloque base y, a igual especificidad, nunca ganaba la cascada. Movida
  detrás, con `min()` para seguir respetando «Letra grande».
- El aviso **«Gira el dispositivo»** saltaba también en apaisado —pidiendo
  girar un aparato ya girado— y tapaba la adaptación apaisada de la rejilla de
  respuestas, que no llegaba a verse nunca. Ahora solo sale en vertical.
- El par `image-rendering` estaba en orden inverso y el pixelado no ganaba.
- `.cinta--posa` no existe en ningún sitio del juego: regla borrada.

**Dentro del código:**

- Cada pulsación de **«Restaurar copia»** dejaba un `<input>` oculto más, con
  su oyente vivo, dentro del panel. Era la única fuga de oyentes del bundle.
- El tiempo agotado protegía `itemActual` en una línea y lo usaba sin guarda
  nueve líneas después.
- Un mensaje de diagnóstico decía «13 slugs» habiendo 26; ahora se calcula.
- Una llamada pasaba un argumento a una función sin parámetros.

**Proyecto y textos:**

- El `.spec` y el pie del README decían «© 2026 Javier Tamarit» donde el resto
  del proyecto dice **JavierTamaritWeb**.
- `audio/CREDITOS.txt` —que viaja dentro del `.app`— remitía a `docs/musica.md`
  y a `js/07-musica.js`, dos rutas que no existen para quien recibe la
  aplicación. Ahora remite al id de Pixabay de su propia tabla y al módulo real.
- Cuatro palabras sin tilde en `EMPAQUETAR-MAC.md`, y tres comentarios del CSS
  que describían valores ya retirados.

### Notas técnicas

Ninguna corrección cambia el tamaño ni el aspecto de nada en el modo normal:
los textos atados a `--tam-texto-min` conservan sus píxeles de siempre
(20 px × 0,6 = los mismos 12 px) y solo crecen cuando el ajuste lo pide. Cada
cambio de CSS y de JS está aplicado a mano dos veces, en el `.min` que corre y
en el gemelo legible, y la sincronía se comprobó mecánicamente: selectores
normalizados en el CSS, literales de cadena en el JS.

Quedan a la vista, sin tocar a propósito: el formato `'signo'` y su
`selectorSigno` son código inalcanzable (~30 líneas que ningún generador
produce); `CB.pantallas.ir` no corta la locución al cambiar de pantalla (se
acota sola y cortarla podría segar avisos legítimos); y el HTML dice «para 2.º
de Primaria» mientras la Ayuda habla de varios cursos, que es una decisión de
contenido, no de código.

---

## [4.4.0] — 2026-08-24

### Añadido

- **El juego dice de quién es y qué se puede hacer con él.** `LICENSE` en la
  raíz y `web/LICENCIA.txt` dentro del bundle, con el copyright de
  **JavierTamaritWeb** y todos los derechos reservados. Se puede usar en casa y
  en el aula en cuantos equipos haga falta; copiarlo, modificarlo o reutilizar
  su código necesita permiso.
- El copyright también en pantalla, encabezando el «Aviso legal» de los
  Créditos: un `.txt` dentro del paquete no lo abre nadie.
- Ocho tests (`TestLicencia`) que lo protegen, incluido que la reserva de
  derechos siga dejando fuera el material de terceros.

### Cambiado

- **La Ayuda y la barra de estado ya hablan el mismo idioma.** El panel se
  llama «Tus vidas: las luces del casco» y empieza por «Arriba, donde pone
  VIDAS, tienes tres luces en el casco», que es lo que enlaza el rótulo con la
  ficción. Donde «luz» salía antes de esa explicación ahora dice «vida».
- Quien oye el juego oye lo mismo que se ve: el estado de las luces se anuncia
  como «Vidas: 3 luces encendidas de 3».

### Notas técnicas

Reservarse todos los derechos sin excluir la tipografía y la música sería
reclamar derechos sobre obra ajena, así que ambos textos dejan fuera
OpenDyslexic (CC BY 3.0) y las pistas de Pixabay, y remiten a sus licencias,
que siguen viajando al lado de los ficheros. Hay un test para eso: es el tipo
de frase que se pierde en una reescritura sin que nadie lo note.

La ficción de las luces del casco no se ha tocado: está en los sonidos, en los
sprites y en la lógica del juego, y funciona. Lo que faltaba era el puente
entre la palabra que el niño lee en la barra y la que lee en la Ayuda.

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

[4.5.0]: #450--2026-08-24
[4.4.0]: #440--2026-08-24
[4.3.0]: #430--2026-08-24
[4.2.0]: #420--2026-08-24
[4.1.0]: #410--2026-08-24
[4.0.0]: #400--2026-08-24
