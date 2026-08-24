# Registro de cambios

Todas las novedades reseñables de la app de escritorio. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
[semántico](https://semver.org/lang/es/).

Esta versión es la de **la app**, no la del juego: el juego lleva la suya propia
(`CB.VERSION`), que va por su cuenta y no la lee nadie desde Python.

---

## [4.11.0] — 2026-08-24

El juego deja de repetir preguntas por costumbre, y el banco de enunciados se
dobla. Juego 3.10.0.

### Corregido

- **Salir a medias y volver a entrar el mismo día daba las mismas preguntas en
  el mismo orden.** La semilla de cada expedición salía de `perfil + fecha +
  n.º de partidas`, y esa cuenta solo sube al terminar: dos arranques seguidos
  con la misma cuenta eran la misma partida, y el niño se las aprendía. Ahora
  la semilla es nueva en cada partida (`CB.util.semillaAleatoria`,
  `crypto.getRandomValues`). Los generadores siguen siendo puros y la semilla
  sigue viajando con la partida guardada.
- **Reanudar una expedición guardada cambiaba de preguntas si había cambiado el
  día.** `reanudarGuardada` volvía a llamar a `iniciar()`, que recalculaba la
  semilla con la fecha; ahora le pasa la que guardó (`semillaPartida`). El ítem
  que estaba en pantalla al guardar se regenera con otros números, como siempre
  —ya consta como servido—; el resto del guion es el mismo.
- **Un reto del jefe perdido y repetido el mismo día traía las mismas cuentas**,
  así que se podía ganar de memoria. También estrena semilla en cada combate.

### Añadido

- **Memoria de ítems entre partidas** (`2C-vistos.js`, `CB.vistos`). El juego
  guarda por veta los últimos 40 ítems servidos (`perfil.items`, un campo del
  esquema 1 que nadie escribía) y, al servir, pide al generador hasta 40
  candidatos y se queda con el primero que no haya salido ni en la sesión ni en
  esa memoria; si todos han salido, sirve el más antiguo. Con ello una veta de
  N ≤ 40 preguntas las recorre todas antes de repetir una: en la tabla del 2,
  medio de cada partida ya había salido en la anterior y ahora es el suelo
  matemático (una de seis); en «¿Con qué se mide?» y «Complementos a 10 y a
  100» la repetición entre partidas seguidas baja a cero. Nunca se bloquea y
  dentro de una sesión sigue sin repetirse nada. La poda del almacén recorta
  la memoria y la importación la sanea.
- **El banco de enunciados se dobla:** 80 nombres (40 F + 40 M) y 120 objetos
  contables para los problemas. Los objetos nuevos entran solos en la lista
  blanca, y un test genera 17.000 enunciados y los pasa por el validador de
  lectura fácil del juego: ninguno tropieza.
- **Las listas cerradas de siete vetas crecen:** «¿Con qué se mide?» 7 → 14
  casos, «La fracción y el decimal» 4 → 8 pares, «El denominador común» 8 → 16,
  «Los ejes de simetría» 4 → 8 figuras, «Caras, aristas y vértices» 3 → 6
  cuerpos, «Las figuras por sus lados» 5 → 7 polígonos y «Seguro o imposible»
  cuatro colores → seis a partir del segundo escalón. Los bancos acotados por
  las matemáticas o por lo que la interfaz sabe dibujar (la tabla del 2 tiene
  once preguntas; hay cuatro figuras planas dibujables) no se tocan.
- `herramientas/cargar-bundle.js` carga el juego en node sin navegador, y
  `herramientas/medir-banco.js` mide el banco real de cada veta (D1–D3) y la
  repetición entre partidas con y sin memoria.
- `TestBancoDePreguntas`: siete tests, dos de ellos cargan el bundle en node
  (la tabla del 2 sale entera antes de repetir; los 120 objetos pasan el
  validador). Total, 88.

---

## [4.10.1] — 2026-08-24

«Seguir cavando» del descanso vuelve a funcionar. Juego 3.9.1.

### Corregido

- **El botón «Seguir cavando» de la pantalla de descanso no hacía nada.**
  Dos elementos compartían el `id` `btn-seguir`: el del descanso, que lo tenía
  desde siempre, y el que estrenó la portada («Seguir cavando en el Bosque»).
  `getElementById` devuelve el **primero del documento** —el de la portada, que
  está `hidden`— así que el único botón visible se quedó sin manejador. No
  daba ningún error: ni en consola, ni en los tests.
- El mismo choque tenía una segunda consecuencia, más callada: el botón de la
  portada se quedaba con el `onclick` del descanso pegado encima del suyo, de
  modo que al pulsarlo arrancaba la expedición **y además** servía un ítem de
  más.
- Ahora son `btn-seguir-expedicion` (portada) y `btn-seguir` (descanso).

### Añadido

- `TestIdsUnicos`: falla si **cualquier** `id` se repite en `index.html`, no
  solo estos dos. Es la clase entera de fallo la que hay que cerrar (79 → 81).

### Notas

- Se revisaron los demás botones, uno a uno y con la app abierta: los 108 `id`
  son únicos, ningún `data-ir` apunta a una pantalla que no existe, ningún
  `getElementById` del JS busca un `id` que el HTML no tenga, y las cuatro
  acciones delegadas (`pista`, `pausa`, `sonido`, `salir-partida`) tienen quien
  las atienda. No apareció ningún otro botón mudo.

---

## [4.10.0] — 2026-08-24

La partida dice en qué curso se está. Juego 3.9.0.

### Añadido

- **El curso, a la cabeza de la franja de la partida**: «CURSO 3.º ▸ LA PRADERA
  DE LOS NÚMEROS ▸ EL HUECO DE LA SUMA». Hasta ahora la franja decía el mundo y
  la veta, y con el mismo nombre de veta repetido en varios cursos la única
  forma de saber en cuál se jugaba era salir al panel de personas adultas.
- Se pinta el curso del **minero**, no el de la veta: una expedición puede
  servir una veta de un curso anterior para repasar, y leerlo del nivel le
  diría al niño que ha bajado de curso a mitad de partida.

### Notas

- Va entero —«Curso 3.º»— porque un «3.º» suelto delante del nombre del mundo
  no dice de qué es; y, al revés que el nombre del mundo, no se esconde en
  pantallas estrechas: cabe, y es el dato que da sentido al resto.
- En oro claro, el mismo que ya usan los demás textos dorados sobre fondo
  oscuro, para distinguirse de un vistazo del nombre de la veta.
- Sin curso, `.rotulo-veta__curso:empty` se lleva también el «▸», para no dejar
  el separador huérfano.
- Un test nuevo (78 → 79), dentro de `TestEleccionDeCurso`.

### Mantenimiento

- **`.gitignore` reescrito**: cachés que faltaban (`.mypy_cache`, `coverage.xml`),
  la basura que deja macOS al copiar a un disco ajeno (`._*`), `.env` por si
  acaso, y una nota al pie de lo que **sí** viaja a git —`uv.lock`,
  `.python-version`, el `.spec` y el bundle entero— para que nadie lo añada
  aquí por descuido.

---

## [4.9.1] — 2026-08-24

Los diálogos nativos hablan español. Juego 3.8.0 (sin cambios).

### Corregido

- **Los paneles de guardar, abrir e imprimir salían en inglés** —«Save file»,
  «Cancel», «Printer»— en un Mac configurado en es-ES, dentro de una
  aplicación que por lo demás está entera en español. Son dos causas
  distintas y hacían falta las dos:
  - El **título** lo pone pywebview, cuyo diccionario por defecto está en
    inglés. `main.py` le pasa el suyo (`TEXTOS`).
  - Los **botones y el resto del panel** los pinta macOS, que elige idioma
    cruzando los del usuario con los que **declara el paquete**. No declaraba
    ninguno. `Cubomatica.spec` añade `CFBundleDevelopmentRegion` y
    `CFBundleLocalizations`.

### Notas

- Ejecutando desde el código (`uv run cubomatica`) los botones siguen en
  inglés: ahí el paquete del proceso es `Python.app`, no el `.app`. Es lo
  esperado, no una regresión.
- Dos tests nuevos (76 → 78), uno por cada mitad: quien arregle solo una se
  entera.

---

## [4.9.0] — 2026-08-24

El panel de personas adultas deja de mentir. Juego 3.8.0.

Tres de sus cuatro salidas al mundo no funcionaban dentro de la app, y ninguna
lo decía. Comprobado pulsando los botones de verdad con una sonda que abre la
aplicación y los acciona desde dentro, no leyendo el código.

### Corregido

- **Descargar CSV y Exportar copia `.json` se llevaban el juego por delante.**
  WKWebView no descarga un `<a download href="blob:…">`: **navega** a él. La
  ventana se iba del juego, pintaba el CSV como texto plano y, sin barra de
  direcciones ni botón de atrás, no había forma de volver: había que cerrar y
  reabrir la aplicación. Ahora se guarda con el diálogo nativo del sistema, a
  través de `Api.guardar_texto`.
- **El botón «Imprimir» del informe no imprimía.** `window.print()` no está
  implementado en WKWebView y no lanza excepción: no hacía absolutamente nada,
  que es la peor forma de fallar. `Api.imprimir` abre el panel de impresión de
  macOS sobre la ventana —y ese panel lleva «PDF ▸ Guardar como PDF», así que
  también sirve para guardar el informe. Se arreglan **los dos** sitios que
  conectaban el botón: el informe y la ficha de refuerzo.
- **«Restaurar copia (.json)» funcionaba por suerte.** El `<input type="file">`
  sí abre el selector nativo, pero solo si el clic nace de un gesto humano:
  WebKit exige activación del usuario y el juego lo disparaba desde JavaScript.
  Ahora se pide el fichero por el puente (`Api.abrir_texto`).
- **No se podía seleccionar ni copiar el texto del panel.** No era cosa del
  juego: pywebview trae `text_select` apagado e inyecta
  `body { user-select: none }` en cualquier página. Se enciende en `main.py` y
  es el CSS del juego el que decide dónde vale la pena.
- **Sin ningún minero, el panel no ofrecía restaurar una copia.** El botón
  vivía solo en la sección Datos de un perfil, así que desaparecía justo el día
  que hace falta: cuando no queda nada que enseñar.
- Una copia restaurada volvía al índice sin su curso, que la ficha de
  «¿Quién juega?» lee desde la 4.8.0.

### Añadido

- **El puente `api.py` deja de estar vacío**: `guardar_texto`, `abrir_texto` e
  `imprimir`. Los tres devuelven siempre un `dict` y nunca lanzan —quien llama
  es JavaScript, y una excepción ahí solo deja una promesa rechazada y un botón
  mudo—, y la ventana viaja en `_ventana`, privado, porque un objeto `Window`
  no es serializable como JSON y rompería el puente entero.
- El panel y el informe avisan de lo que ha pasado (`CB.adulto.decir`), en
  pantalla y para el lector de pantalla: dónde se ha guardado el fichero, o que
  no se ha guardado nada.
- Once tests nuevos (65 → 76), entre ellos que el puente se intenta **antes**
  que el blob: al revés, dentro de la app se pierde la página.

### Notas de diseño

- **El puente es opcional.** `CB.adulto.puente()` devuelve `null` en un
  navegador normal, donde el enlace `blob:` y `window.print()` sí funcionan y
  siguen siendo el camino. El juego no depende de correr dentro del `.app`.
- **La selección se enciende por pantalla, no en general.** En el juego sigue
  apagada: son bloques que se tocan, y arrastrar el dedo sobre un enunciado o
  sobre una respuesta lo pintaría de azul sin que el niño haya pedido nada. Se
  enciende en las pantallas que son documento —el panel y el informe— y en los
  créditos, que llevan los textos de licencia. Los botones de esas pantallas se
  quedan fuera.

---

## [4.8.2] — 2026-08-24

Deshacer lo empezado. Juego 3.7.2.

### Añadido

- **Quitar un minero desde «¿Quién juega?»**, sin pasar por el panel del
  adulto. Hasta ahora había que entrar con ese minero, abrir la llave y
  escribir BORRAR; probar el juego dejaba mineros de prueba imposibles de
  limpiar sin saberse ese camino.
- **«Dejarla y empezar otra»** en la portada, cuando hay una expedición a
  medias. No había forma de tirarla: JUGAR decía «Seguir jugando» y la única
  salida era esperar 24 h a que caducara. `CB.partida.descartarGuardada`
  vacía `partidaEnCurso` y guarda; el progreso aprendido no se toca, solo se
  pierden las gemas de esa expedición.
- La Ayuda cuenta las dos cosas, con lo que se pierde en cada caso.

### Notas de diseño

- **El borrado va detrás de un modo, no de un aspa en cada ficha.** Esta
  pantalla la ve el niño, y un aspa en la esquina se toca sin querer y se lleva
  por delante el progreso del hermano. Hay que entrar a propósito en «Quitar un
  minero» —que oculta «Nuevo minero» y pinta las fichas en brasa—, y aun dentro
  la ficha pregunta por su nombre, con su cara delante, antes de irse.
- El panel del adulto conserva su propio borrado, el que pide escribir BORRAR,
  para el perfil activo. Esto es lo mismo con la puerta a la altura del niño.
- Bloques `--peligro` en brasa con la estructura de bisel del primario: en la
  misma ficha donde antes ponía JUGAR, el color es lo primero que avisa de que
  este bloque no lleva a jugar. Negro sobre blanco en alto contraste, como el
  resto.

### Corregido

- Quitar el último minero dejaba la pantalla **sin «Nuevo minero»**: el modo
  quitar se apagaba después de decidir qué botones se ven, así que ese
  repintado los ocultaba los dos. Se apaga antes, y hay un test que compara el
  orden de las dos líneas.

---

## [4.8.1] — 2026-08-24

Una columna, pero ancha. Juego 3.7.1.

### Cambiado

- **Ayuda, Mis vetas, Mi álbum y «¿Quién juega?» dejan de leerse en una tira de
  640 px con media pantalla vacía al lado.** El modificador `contenido--ancho`
  declara `--ancho-contenido: 1040px`, `--ancho-panel: 100%` y
  `--ancho-lectura: 52ch` a partir de 1200 px, y 1240 px / 60ch a partir de
  1600 —que es la pantalla del iMac, donde 1040 seguía dejando 440 px muertos a
  cada lado—. El contenedor declara y el bloque consume, como el resto del CSS.
- Sigue **sin** columnas de periódico: Ayuda tiene 18 paneles y leerlas
  obligaría a bajar del todo y volver a subir. Eso vale para Créditos, que cabe
  en un scroll, y no para una pantalla larga.
- 60 caracteres es el techo de línea, no un número redondo: más allá el ojo
  pierde el principio del renglón siguiente, y eso a los siete años se paga.
  Un test lo comprueba.
- Ajustes y el Diccionario se probaron ensanchados y **se revirtieron**: una
  etiqueta con sus bloques, o un término con su definición de una línea, solo
  ganan hueco vacío, y el control acababa a media pantalla de su rótulo.

---

## [4.8.0] — 2026-08-24

Elegir curso dejaba de ser una decisión y pasaba a ser un descuido: la pregunta
que manda en todo el contenido del juego era el texto más pequeño de su
pantalla, y una vez contestada no volvía a verse nunca. Juego 3.7.0.

### Cambiado

- **Elegir curso es un paso, no una línea suelta.** «Nuevo minero» ya no deja la
  pantalla titulada «¿Quién juega?» con la pregunta de verdad debajo en letra
  menuda: la pregunta se lleva el titular, y bajo ella va la única frase que
  hacía falta —quién la contesta, qué decide y cómo se deshace—. Los seis
  cursos van en su fila y **«Volver» en la suya**: compartiéndola parecía un
  séptimo curso.
- **El curso se ve.** En la portada, arriba a la izquierda: «Juega Vagón Cargado
  · 2.º de Primaria», enfrente de la llave con la que un adulto lo cambia. Y en
  cada ficha de «¿Quién juega?», bajo el mote. Hasta ahora, colarse al crear el
  perfil solo se notaba porque las preguntas salían raras, y para entonces ya
  nadie lo relacionaba con aquella pantalla del primer día.
- **La pista de la portada nombra el curso**: «4 preguntas para ver por dónde
  empezar **en 2.º**». Sin él sonaba a que ahí se elegía el nivel, y no: la
  calibración solo mira por dónde empezar dentro del curso ya elegido.
- La Ayuda lo cuenta igual: dónde se ve el curso, quién lo cambia y que las
  cuatro preguntas no lo eligen.
- **Las fichas de «¿Quién juega?» enseñan al minero.** `CB.sprites.avatar`
  llevaba desde 3.0.0 dibujando los 16 mineros —casco, cara y ropa con la
  paleta del perfil— sin que lo llamara nadie: la ficha pintaba un cuadrado
  del color del casco y ya. Ahora sale el sprite a 84 px, y los dos mapas base
  tienen cara: las dos filas del rostro eran una banda maciza del color de los
  rasgos, que a ese tamaño se leía como un pasamontañas; ahora son dos ojos y
  una boca con piel alrededor. La ficha reserva dos renglones para el mote y
  pega JUGAR al fondo, así que el curso y el botón quedan a la misma altura en
  todas aunque un mote ocupe una línea y otro dos. Y lleva el marco de piedra
  de los demás bloques, blanco en alto contraste como ellos.

### Corregido

- `CB.sprites.aplicar` medía la caja con el tamaño de CELDA en su rama de
  box-shadow (`s.px` en vez de `s.ancho`), así que un sprite servido por esa
  vía se salía de un hueco de 8×8. Todavía no lo llamaba nadie.

- **La llave del panel adulto estaba en la esquina equivocada.** Se declara
  `position: absolute` arriba a la derecha, pero
  `.pantalla > *:not(.cielo)…` —la regla que levanta el contenido sobre el
  cielo— la pisaba con `position: relative`, y su propio `right: 16px` acababa
  moviéndola 16 px a la **izquierda** del borde izquierdo. Las dos esquinas de
  la portada quedan fuera de esa regla y llevan su `z-index` escrito.
- **Las fichas de «¿Quién juega?» se apilaban de una en una.** `.contenido`
  centra con `align-items`, así que la lista se encogía a 0 de ancho y cada
  ficha envolvía sola. Con un perfil no se veía; con dos, sí.
- El índice de perfiles guarda el curso, como ya guardaba mote y avatar, para
  no leer los ocho perfiles enteros solo para pintar la lista. Los perfiles
  anteriores lo rellenan solos la primera vez.

---

## [4.7.0] — 2026-08-24

La propuesta de UX/UI de `docs/propuesta-ux-ui.md`, implementada entera en el
juego (versión 3.6.0 del bundle). Nada toca los generadores ni las reglas: es
capa DOM, CSS e `index.html`.

### Cambiado

- **La respuesta se ve en el bloque que se tocó.** El elegido se hunde y se pone
  verde (o gris si falla), los demás se apagan a piedra y el foco va con él; el
  mensaje va grande junto a las opciones, en una caja que reserva su sitio para
  que nada salte. La gema ganada vuela desde el bloque hasta el contador del
  HUD y allí brota el «+N» (no hay vuelo con «sin movimiento»). El hueco del
  reloj se reserva al parar, así «Pregunta 3 de 20» no se mueve; los 20
  bloques de avance van en una fila; en escritorio los bloques de respuesta
  crecen (88–120 px por altura) y el enunciado con ellos.
- **El minero trabaja.** Cubi, Rocarr, Gluglú, Chispa y los jefes son sprites de
  `03-sprites` a ×8 (×12 en escritorio): Cubi pica el bloque al acertar y se
  rasca la cabeza al fallar; Rocarr asiente y sonríe al dar la pista.
- **Ni un emoji.** Llave, pista, pausa, altavoz, flecha, borrar, caras del
  «¿cómo te has sentido?», cromos y premios son sprites publicados como
  `--sprite-*`. `TestIconografia` vigila que no vuelvan.
- **Mis vetas es un frente de mina.** Las cerradas son piedra con candado y sin
  texto; el nombre solo se ve en la frontera (borde de oro) y al pasar o
  enfocar; las superadas llevan la gema incrustada; las de musgo, musgo.
- **Ajustes con selectores segmentados** (el bloque elegido, hundido) en vez de
  botones que ciclan, con **Alto contraste** y **Animaciones** (Sí / No / Como
  el aparato) por fin al alcance del niño, y una frase de muestra que crece con
  «Letra grande» al instante.
- **Mapa:** la textura del bioma es el fondo de toda la tarjeta; la bloqueada
  dice «Cava 3 vetas más en la Pradera» con la barra del mundo anterior; el modo
  es un selector de tres bloques; Mis vetas, Mi álbum y Diccionario son bloques
  con icono, y Ayuda y Salir van en segundo plano.
- **Álbum:** el cromo que falta enseña su silueta; la vitrina distingue
  diplomas (marco de madera y el curso en grande), guardianes (con su nombre y
  su criatura), récords y logros, y dice cómo se gana cada uno.
- **Portada:** «Cantera tranquila» dice «Sin reloj y sin vidas»; quien vuelve
  tiene «Seguir cavando en el Bosque» encima de JUGAR; el suelo anticipa los
  cuatro biomas.
- **La Ayuda del juego cuenta la interfaz nueva**: cómo se lee el frente de mina de «Mis
  vetas», que los cromos y los premios que faltan salen en sombra, los dos ajustes de
  accesibilidad, que los modos son bloques que se hunden (y que también están en el mapa) y
  que las flechas del teclado mueven de un bloque a otro.
- **Transición** de caída de bloque (150 ms, a saltos) al cambiar de pantalla,
  marcos de piedra texturizada en paneles, tarjetas y ajustes, y `:focus-visible`
  que conserva el bisel. Los botones con `aria-pressed`/`aria-checked` se ven
  hundidos.

### Corregido

- La presentación de cada formato decía «Toca el 5» sobre opciones donde no
  había ningún 5: ahora es una instrucción sobre el ítem real («Toca la
  respuesta buena»).
- El reloj analógico tapaba el 12 con la aguja y pegaba las cifras al borde:
  esfera de 168 px con las cifras en una banda exterior al anillo.
- La vitrina ocultaba la línea de «cómo se gana» de los premios pendientes, al
  revés de lo que decía su propio comentario.
- `CB.partida.hayPartidaGuardada` leía `iniciadaTs`, que nunca se escribía, y la
  partida guardada no caducaba a las 24 h.
- Chispa al girar abría una barra de scroll horizontal bajo el enunciado.
- El «+N» de las gemas brotaba hacia arriba desde el contador y se salía por el techo del HUD:
  ahora brota a su izquierda.

## [4.6.0] — 2026-08-24

Cuatro cambios de fondo: dos en el juego (versión 3.5.0 del bundle) y dos en el
proyecto.

### Corregido

- **La calibración inicial asignaba el nivel al revés.** Las cuatro preguntas
  fijan el theta de cada destreza, pero la línea que lo hacía comparaba la
  *posición* de la pregunta con el *número* de aciertos: fallar la primera y
  acertar la cuarta dejaba alta la destreza fallada y baja la acertada. Ahora se
  guarda el resultado de cada pregunta y cada destreza sube si acierta las
  suyas, baja si las falla y se queda en el theta inicial si acierta una y
  falla otra.

### Añadido

- **Las 48 pistas por error, por fin en pantalla.** Cada código de `CB.ERRORES`
  llevaba desde siempre una `pista` («Mira si al sumar las unidades pasas de
  diez») y el explicador que le corresponde (`reparacion`), y el diagnóstico se
  calculaba… y no se usaba para nada que viera el niño. Ahora, cuando el valor
  escrito coincide con un error conocido, el primer fallo enseña la pista de
  *ese* error en vez de la genérica de la destreza, y la tarjeta de reparación
  usa el explicador del error y pinta la pista encima de los tres pasos (y la
  lee en voz alta con ellos). Si no hay diagnóstico, todo sigue como antes.
- **Integración continua.** `.github/workflows/ci.yml` pasa `ruff`, `pytest`,
  la comprobación de formato de `index.html` y un `node --check` del bundle en
  cada push y cada pull request, y después construye `Cubomatica.app` en
  `macos-latest` y lo guarda como artefacto.

### Retirado

- **La puerta parental.** Pedía la n-ésima palabra de una frase que se enseñaba
  en pantalla: la abría cualquier niño que supiera leer, así que no protegía
  nada y solo estorbaba. La llave de la portada abre el panel directamente. Sin
  perfil elegido, el panel lo dice y ofrece solo «Salir». La Ayuda ya no
  promete «una cuenta de mayores».
- **Los gemelos minificados.** `index.html` cargaba `cubomatica.min.css` y
  `cubomatica.min.js`, y los ficheros legibles viajaban al lado sin que nada
  los ejecutara: cada cambio había que aplicarlo dos veces, a mano, sin
  minificador. Bajo `file://` la minificación no ahorra nada perceptible, así
  que ahora se cargan los legibles y los `.min` han desaparecido. Un test
  avisa si vuelven.
- **El módulo offline.** `45-offline.js` (service worker, caché de música)
  exigía `location.protocol !== 'file:'` y registraba un `sw.js` que no
  existía: dentro de la app no podía correr nunca. Se va con su sección «Sin
  conexión» del panel del adulto y con `manifest.webmanifest`.
- **Los ejemplos de plantilla de `api.py`.** `saludar`, `info_sistema` y
  `elegir_archivo` viajaban dentro del `.app` sin que el juego los llamara. La
  clase queda vacía a propósito, conectada como `js_api`, y `test_api.py`
  protege que nada se exponga a JavaScript por accidente.

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
