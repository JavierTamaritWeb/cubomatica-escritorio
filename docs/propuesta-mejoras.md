# Cubomática — propuesta de mejoras (24-08-2026)

Diagnóstico sobre la versión 4.5.0 del shell y 3.4.7 del juego. Nada está implementado:
es una lista para decidir. Las referencias `js:NNNN` son líneas de
`src/cubomatica/web/js/cubomatica.js`; las he verificado leyendo el código.

## Resumen en cinco líneas

1. **Las familias pueden perder el progreso**, y las dos salidas que lo evitan (copia de
   seguridad y CSV) casi seguro no funcionan en la app de escritorio.
2. **La calibración inicial asigna el nivel al revés** en muchos casos: un bug de una línea
   con efecto en toda la partida.
3. **La puerta parental la abre cualquier niño que sepa leer**: la frase se enseña en pantalla
   y solo hay que copiar una palabra.
4. Hay **~48 pistas pedagógicas escritas y nunca mostradas**: la mayor mejora didáctica ya está
   codificada, solo falta enchufarla.
5. El proyecto arrastra **deuda estructural evitable**: los gemelos `.min` editados a mano,
   `api.py` con ejemplos de plantilla, módulo offline muerto, sin CI.

---

## 1. Lo que puede dejar a un niño sin sus datos (prioridad máxima)

- **Exportar copia / CSV está roto en escritorio.** `CB.adulto.descargar` (js:16443) usa
  `<a download>` con un blob. `main.py` no activa `webview.settings['ALLOW_DOWNLOADS']`, y
  pywebview/Cocoa cancela las respuestas que no puede mostrar (`cocoa.py:253-278`); peor: para
  `text/*` puede *navegar* al CSV y sacar al usuario del juego. El `catch` solo atrapa
  excepciones síncronas, así que **el usuario no recibe ningún aviso**. `CB.LEGAL.LIMITACION`
  le pide «haz una copia cada trimestre» y ese camino no existe. Hay que verificarlo
  arrancando la app, pero la lectura del código apunta a inerte.
- **Imprimir informe y ficha de refuerzo** (js:16383, 16423): `window.print()` inerte, ya
  documentado en el README. La hoja `@media print` está bien hecha y es inalcanzable.
- **La solución de ambos es la misma**: usar por fin `api.py`. Métodos reales
  `guardar_fichero(nombre, texto)` (diálogo nativo de guardado), `imprimir()` (vía
  `NSPrintOperation` sobre la WKWebView o exportar a PDF) y quizá `abrir_carpeta_datos()`. En
  JS, detectar `window.pywebview` y preferirlo. De paso, borrar `saludar`/`info_sistema`/
  `elegir_archivo`, que son ejemplos de plantilla que viajan dentro del `.app`.
- **Copia de seguridad automática**: con el puente, volcar los perfiles a
  `~/Library/Application Support/Cubomatica/copia-AAAA-MM-DD.json` al cerrar o al terminar
  sesión, y ofrecer «Restaurar la última copia». Resuelve también que el `.app` y `uv run` no
  compartan datos.

## 2. Bugs de juego que verificaría y corregiría primero

| Dónde | Qué pasa |
|---|---|
| js:17513-17516 | **Calibración**: `d.theta = (i < a) ? 1080 : 920` donde `a` es *cuántos* aciertos, no *cuáles*. Fallar la 1.ª y acertar la 4.ª deja alta la destreza fallada y baja la acertada. Hay que guardar el vector de aciertos. |
| js:3552-3556 | **N6 pares/impares**: `base=99` y «par» → `100` → `clamp` → `99`, respuesta impar marcada como par. |
| js:4352-4366 | **S26 «mejor estimación»**: cuando la rebaja acumulada supera 250, el distractor `est−500` está más cerca del valor real que la respuesta «correcta». |
| js:3527 | **N11 salto 100**: `inicio` fijo en 400, serie siempre igual y se sale del techo 599. |
| js:5215-5216, 5128-5137 | Problemas con respuesta 0 («¿cuántos le quedan?» = 0) y enunciados donde aparece un personaje (Luis) que no se ha presentado. |
| js:4633 | En M4-M7 el `visual` matriz de hasta 10×10 **regala la respuesta contándola**; la tabla deja de ser un hecho memorizado. Limitar a tablas iniciales o a la reparación. |
| js:14571-14576 | `distractoresFijos` no deduplica ni comprueba contra la respuesta; N6 puede devolver menos de 3 opciones. |
| js:13339-13360 | `CB.pantallas.fallo()` salta por encima de `ir()`: el reloj (`setInterval` 100 ms) y los temporizadores de partida siguen vivos bajo la pantalla de error. |
| js:1495-1498 | `reportarError` relanza *cualquier* error capturado hasta `window.onerror`, de modo que un oyente roto del bus tumba la partida entera. Debería registrar, no escalar. |
| js:13434-13453 | `montar()` deja un `setTimeout` de 800 ms sin cancelar que roba el foco a una sección oculta y mantiene `bloqueado=true` (y entonces `conectarTeclado` hace `preventDefault` sobre todas las teclas, incluido el campo del adulto). |
| js:13205 | «**Hurry up!**» en inglés en pantalla para un niño de 7 años. |

## 3. Pedagogía: lo que más mejoraría la experiencia

- **Enchufar las pistas por error.** Cada uno de los 48 `CB.ERRORES` lleva `pista:` y
  `reparacion:` (p. ej. «Mira si al sumar las unidades pasas de diez»), el diagnóstico ya se
  calcula (js:14880), pero la tarjeta de reparación usa solo el explicador genérico por
  destreza (js:11250) y `notaAdulto` no lo pinta nadie. Es el retorno más alto por línea
  cambiada del proyecto.
- **Panel del niño sin «Alto contraste» ni «Sin movimiento»** (js:17798-17868): solo el adulto
  puede activarlos. Son requisitos legales, deberían estar donde está «Letra grande».
- **Voz**: `rate=0.85` fijo y elección de la primera voz `es*` que aparezca (js:2755,
  2711-2725); en macOS suele ser una voz mala. Priorizar `es-ES` de calidad y dar un control
  de velocidad.
- **Puerta parental** (js:15718-15756): 4 frases, la misma todo el día, y se pide «la cuarta
  palabra de esta frase: «…»» mostrando la frase. La Ayuda promete «una cuenta de mayores».
  Además `desbloqueado` no vuelve a `false` al salir y no hay límite de intentos. Sustituir
  por una operación real (p. ej. 47 × 6) y volver a bloquear al salir.
- **«Letra grande» solo escala 4 tokens** y hay 339 `px` literales en el CSS (parcialmente
  arreglado en 4.5.0, pero queda mucho).

## 4. Shell de escritorio (Python y empaquetado)

- **Registro en fichero.** Todo va a `stderr`, que en un `.app` no existe: cuando a una
  familia le falle algo no habrá rastro. `~/Library/Logs/Cubomatica/cubomatica.log` con
  rotación, y que `window.onerror` lo alimente vía `api.py`.
- **Distribución real.** La firma ad-hoc sirve en tu Mac; en otro, Gatekeeper mostrará «no se
  puede abrir porque no se puede verificar». Opciones: Developer ID + notarización
  (99 €/año) o, como mínimo, un DMG con instrucciones «clic derecho → Abrir» en el README.
  Y `target_arch="universal2"` para los Mac Intel que quedan en los colegios.
- **`argv_emulation=True`** en el spec: la app no abre ficheros y esa opción usa API Carbon
  obsoleta que retrasa el arranque y a veces lo impide. Ponerlo a `False`.
- **Peso**: 42 MB de los 69 son MP3 a **256 kbps**. A 128 kbps (o AAC `.m4a`, nativo en
  WKWebView) se queda en ~20 MB sin que un niño note nada.
- **Menú «Juego»** sin atajos (`keyEquivalent ""`): ⌘, para Ajustes, ⌘? para Ayuda; y entrar
  en Ajustes desde el menú no pausa la partida en curso. `ventana_nativa()` localiza la
  ventana por título: si algún día el juego cambia `document.title`, la pantalla completa
  deja de funcionar en silencio; mejor por `webview.windows[0].native` o por índice.
- **Instancia única**: dos `.app` abiertos escriben en el mismo `localStorage`; un guardado en
  dos fases con `.tmp` puede corromperse. Un lock en Application Support lo evita.
- **Dependencias**: todo pinned a versiones de hace un año (pywebview 5.3.2 → 6.2.1,
  PyInstaller 6.10 → 6.22, ruff 0.6 → 0.16). Merece una pasada deliberada, comprobando sobre
  todo si pywebview 6 arregla el `menu=` roto que obligó al menú a mano.

## 5. Estructura, calidad y proceso

- **Eliminar los gemelos `.min`.** Bajo `file://` local, minificar 1,1 MB de JS no ahorra nada
  perceptible, y el mantenimiento a mano es la trampa documentada en `CLAUDE.md`. Que
  `index.html` cargue `cubomatica.js` y `cubomatica.css` directamente y borrar los `.min` (o,
  si se quieren, generarlos en `build-mac.sh` con un minificador pinneado). Una decisión, y
  desaparece toda una clase de errores.
- **Ir más allá: partir el bundle de nuevo en sus 56 módulos** (`web/js/00-nucleo.js`…) con
  56 `<script>` o una concatenación en el build. Los límites ya existen como comentarios; el
  diff por commit pasaría a ser legible.
- **Tests del juego, no solo del envoltorio.** Los 62 tests son estáticos sobre ficheros. Los
  generadores son puros con RNG inyectado: se pueden cargar en Node (`node --test`, sin
  `package.json` ni dependencias, definiendo `window`/`document` vacíos) y fuzzear los 308
  niveles como invariantes permanentes: respuesta dentro de rango, distractores ≠ respuesta y
  sin duplicados, siempre 4 opciones, ningún enunciado con `undefined`/`NaN`, ninguna
  respuesta 0 donde no proceda. La auditoría 4.5.0 lo hizo una vez a mano; debería correr en
  cada commit y habría cazado N6, S26 y N11.
- **CI**: un GitHub Actions con `uv run pytest`, `ruff`, `formatear-html.py --comprobar` y el
  build del `.app` en `macos-latest`. Hoy nada lo ejecuta salvo tú.
- **Versión en un solo sitio**: el spec puede leerla de `pyproject.toml` con `tomllib`, y el
  test de coincidencia se vuelve innecesario. `CB.VERSION` que aparezca también en Créditos
  junto a la de la app.
- **Código muerto que viaja en el `.app`**: `45-offline.js` entero (exige
  `protocol !== 'file:'` y registra un `sw.js` que no existe), su interfaz en el panel del
  adulto (descargar música, olvidar caché), `manifest.webmanifest`, `theme-color`,
  `avisarSinDisco`. Quitarlo evita explicar a un adulto botones que no hacen nada.
- **Rendimiento menor pero gratuito**: `ls()` escribe/borra una clave en `localStorage` en
  cada *lectura* (js:1596); `sanear()` es O(n²) con `indexOf` y corre por pregunta
  (js:1609); `.tmp` huérfano si falla el segundo `setItem` (js:1659); `CB.musica` mantiene
  un `setInterval` de 10 Hz y oyentes globales `pointerdown`/`keydown` que nunca se retiran;
  `@font-face` con `font-display: block` sin `preload` (texto invisible en el primer
  arranque).
- **CSP** en `index.html`: `default-src 'self' data: blob:; script-src 'self'`. Cuesta una
  línea y cubre la única entrada externa que hay (la importación de JSON).
- **CSV** sin escapado ni BOM, y `flags` puede llevar `;` (js:16428).

## Orden que seguiría

1. Puente `api.py` real: guardar fichero, imprimir, log; copia automática.
   *(desbloquea todo lo de datos)*
2. Calibración, N6, S26, N11, `fallo()`, `reportarError`. *(bugs verificados, pequeños)*
3. Pistas por error en la reparación + puerta parental seria + ajustes de accesibilidad en el
   panel del niño.
4. Quitar `.min` y módulo offline; tests de generadores en Node; CI.
5. Distribución: `argv_emulation=False`, universal2, audio a 128 kbps, DMG o notarización.
