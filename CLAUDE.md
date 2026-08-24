# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

The **desktop packaging shell** for Cubomática, a Spanish primary-school maths game. A pywebview
window loads a local HTML/CSS/JS bundle, and PyInstaller turns it into `dist/Cubomatica.app`.
Desktop only — it is not a web build or a PWA, and it opens no port on the machine.

**Two version numbers, deliberately.** The app version (currently **4.10.0**) is declared in both
`pyproject.toml` and `Cubomatica.spec`, and `tests/test_web.py::TestVersion` fails if they drift
apart. The game has its own, `CB.VERSION` inside the web bundle (currently 3.9.0); it tracks the
game's content, moves on its own schedule, and nothing on the Python side reads it.

The Python here is deliberately thin (two short modules); nearly everything else is the game bundle.
Read the next section before touching anything under `src/cubomatica/web/` — those files load in a
way that punishes the obvious guess.

Everything user-facing is in Spanish: UI, docs, comments, test names. Match that when writing.

## Stay inside this repository

**Do not touch `~/Desktop/mathsgame`.** It is a separate project, and the owner has ruled it out of
scope: everything happens with the files in `~/Desktop/cubomatica`. This is a standing instruction,
not a default to weigh against convenience.

`src/cubomatica/web/` originally arrived as a byte-identical copy of `mathsgame/dist/` — build
output from a gulp/SCSS pipeline that lives over there. That history explains the shape of the files
but no longer says where to edit them. **Here, `src/cubomatica/web/` is the source.**

**`index.html` loads `css/cubomatica.css` and `js/cubomatica.js` directly — the legible files are
the ones that run.** Until 4.5.0 it loaded `.min` twins that had to be kept in step by hand, with no
minifier in the repository; under `file://` minification saves nothing perceptible, so the twins
were deleted in 4.6.0 and `tests/test_web.py::TestArchivosExisten::test_no_hay_gemelos_minificados`
fails if any `*.min.*` reappears under `web/`. Do not reintroduce them: one file, edited in place.

`index.html` was itself minified — one 21 KB line — and is now kept formatted by
`herramientas/formatear-html.py`. `tests/test_web.py::TestHtmlLegible` fails if it goes back to one
line.

**Reformatting HTML is not cosmetic: whitespace renders.** A newline plus indentation between two
inline-level elements is a real space, and where there was none it opens a gap that was not there.
So the tool never touches the inside of a text element (`p`, `h1`, `li`, `button`…), never splits
mixed content, and splits only containers whose children are all elements. It also prints every
place where it puts a break between two inline-level siblings that were glued together — check the
CSS for those boxes before believing the result. In a flex or grid container a whitespace-only node
is not an item and is ignored; in a normal block it is a space you will see. That check is why
`.contenido--doble .contenido__paneles` carries `line-height: 0` with the panels restoring it: the
panels are `inline-block`, so the newline between them would otherwise add a blank line.

`cubomatica.js` is a concatenation of 56 modules whose boundary comments (`/* 00-nucleo.js`,
`/* 07-musica.js` …) survive in the bundle — see the next section for the map. The CSS is BEM in
Spanish, and the game's accessibility rules are legal requirements rather than preferences: root
classes `letra-grande`, `alto-contraste` and `sin-movimiento` must keep working, and anything that
centres content while also scrolling needs the `safe` keyword (`justify-content: safe center`), or
whatever overflows above becomes unreachable — `scrollTop` cannot go negative.

**The game is set in OpenDyslexic, and the font ships inside the bundle** (`web/fonts/`, 256 KB,
four faces declared with relative `url("../fonts/…")`). Nothing looks it up in the system: the app
runs from `file://` on a stranger's Mac. It is **CC BY 3.0**, which obliges attribution — the credit
is on the Créditos screen and `fonts/LICENCIA-OpenDyslexic.txt` travels beside the files.
`tests/test_web.py::TestTipografia` guards all of that, because a missing `.otf` raises nothing at
all: WebKit silently falls back to Verdana and the game still runs.

Two spacing tokens were retuned with it. `--espaciado-letra` went to `0` and `--espaciado-palabra`
to `.06em`: the old `.05em`/`.16em` were right for Verdana, where extra tracking aids reading, but
OpenDyslexic already builds that in and the two stacked left words floating apart.

The game's own licence is `web/LICENCIA.txt` — **inside the bundle**, because whoever receives the
`.app` does not receive the repository; `LICENSE` at the root covers the repo. Both are © 2026
JavierTamaritWeb, all rights reserved, and both **carve out the third-party material**: reserving
every right without excepting OpenDyslexic (CC BY 3.0) and the Pixabay music would be claiming
rights over someone else's work. `TestLicencia` guards that carve-out, the on-screen copyright
(`CB.LEGAL.COPYRIGHT`, painted at the head of the Créditos «Aviso legal» panel) and the two files.

There is no service worker, no `manifest.webmanifest` and no offline module any more: `45-offline.js`
required `location.protocol !== 'file:'`, so under this shell it could never run, and it was removed
in 4.6.0 together with its «Sin conexión» section in the parent panel. The app is offline by
construction — it never touches the network.

**Icons are sprites, never emojis.** `03-sprites.js` rasterises every pixel map once at boot
(`CB.sprites.publicar()`, 1 px per cell) and publishes it as a custom property `--sprite-<id>`
on `:root` (plus `--sprite-<id>-silueta` for the eleven creatures), exactly as `02-texturas.js`
publishes `--tex-*`. The DOM consumes them through `<span class="icono-px" data-icono="…">`
(`CB.ui.icono`, or `{ icono: '…' }` in `CB.ui.boton`) and `.criatura[data-quien=…]`; the CSS
scales the box with `--px-icono` / `--px-criatura` and the global `image-rendering: pixelated`
keeps it crisp at integer multiples. `TestIconografia` fails if an emoji comes back into
`index.html`. New icons are 8×8 maps in `CB.sprites.MAPAS`; creatures stay 7×7 (ranacubo is 8
wide, hence `--celdas`).

Three more things from the 3.6.0 UX pass that are easy to undo by accident: the answer block the
child touched gets `data-elegida` in `CB.componentes.pedirConfirmacion` (the funnel of all seven
formats) and the container gets `data-resultado` from `CB.partida.marcarResultado`, and the CSS
sinks and colours it from those two attributes; the clock is parked between questions with
`.reloj--parado` (`visibility: hidden`) rather than `hidden`, so the HUD never reflows; and
`CB.pantallas.caer` gives the incoming screen its 150 ms «block drop» — entrance only, because
`[hidden]` is `display: none`. Any new animation goes in **both** `sin-movimiento` lists.

**Avatars are sprites too, and `CB.sprites.avatar` draws them** — all sixteen miners, helmet,
face and clothes recoloured from `CB.datos.AVATARES`. It existed from 3.0.0 and nothing called
it: the profile card painted a flat square of the helmet colour until 3.7.0. It forces
`imagen: true`, because 7×7 sits under `UMBRAL_BOXSHADOW` and `CB.sprites.aplicar`'s box-shadow
branch is the buggier path. The two base maps carry a real face — eyes on one row, mouth on the
next; a solid band of the feature colour read as a balaclava at 84 px.

**The course (1.º–6.º) is declared once and must stay visible.** `CB.perfiles.crear` borrows the
`#titulo-perfiles` h1 for its own question and `CB.perfiles.pintar` gives it back — if you add a
path out of that step, restore the title there too. `CB.almacen.guardarPerfil` stamps `curso` on
the index entry beside mote and avatar, so the card can show it without reading every profile;
`pintar` back-fills older entries once. The portada prints `CB.arranque.quienJuega` in its top-left
corner, facing the key that changes it. Four questions of calibration deduce the *trimester*, never
the course, and every wording around them has to keep saying so.

In game, the strip under the HUD says it too — «CURSO 3.º ▸ LA PRADERA DE LOS NÚMEROS ▸ EL HUECO DE
LA SUMA». `CB.ui.pintarVeta(nivel, mundo, curso)` takes the course as a third argument and
`servirItem` passes `CB.catalogo.cursoDe(CB.perfil)`: the **miner's** course, not `nivel.curso` —
an expedition can serve a veta from an earlier course to revise, and reading it off the level would
tell the child they had gone down a year mid-game. It is written out in full («Curso 3.º») because a
bare «3.º» in front of a world name says nothing, and unlike `.rotulo-veta__mundo` it is never
hidden on narrow screens; `.rotulo-veta__curso:empty` removes it, and its «▸», when there is no
course. `TestEleccionDeCurso` guards the three pieces.

**`.pantalla > *:not(.cielo):not(.cinta):not(.cartel)` sets `position: relative` to lift content
over the sky, and it outweighs a plain `.portada__llave { position: absolute }`.** That is how the
parent-panel key spent releases in the top-*left* corner, shoved there by its own `right: 16px`
resolving in relative mode. Both portada corners are excluded from that rule and carry their own
`z-index`; `TestEleccionDeCurso` fails if the exclusions go. Anything else absolutely positioned
directly under `.pantalla` needs the same treatment.

**Undoing is a first-class action, and it is gated by a mode, not by an X.** «¿Quién juega?»
carries `#btn-quitar-minero`: it flips `CB.perfiles.modoQuitar`, hides «Nuevo minero», paints the
cards in brasa and swaps each JUGAR for QUITAR; the card itself then asks, with the miner's face
still on it, before `CB.almacen.borrarPerfil` runs. A per-card X would be tapped by accident and
take a sibling's progress with it. `pintar()` clears the mode **before** it decides which buttons
show — clearing it after left the screen with no «Nuevo minero» once the last miner went.
`CB.adulto.confirmarBorrado` (type BORRAR) stays for the active profile. The portada's
`#btn-descartar` calls `CB.partida.descartarGuardada`, the only way out of a half-finished
expedition short of waiting for the 24 h expiry.

There is no parental gate either. The key on the title screen opens the parent panel directly: the
old gate (type the n-th word of a sentence shown on screen) was removed in 4.6.0 at the owner's
request. With no profile selected the panel says so and offers only «Salir».

## Orienting inside the bundle

`cubomatica.js` is 18k lines but navigable: the 56 concatenated modules each keep their header
comment, so this prints the table of contents with line numbers:

```bash
grep -nE '^/\* [0-9A-Za-z][-A-Za-z0-9]*\.js' src/cubomatica/web/js/cubomatica.js
```

The numbering encodes strict layering, and the layers are enforced rather than aspirational:

| Prefix | Layer |
|---|---|
| bare names | frozen content tables — curriculum, names, objects, glossary, messages |
| `00-`–`07-` | core: seeded RNG + event bus, `CB.almacen`, procedural textures/sprites, synthesized SFX, speech, a11y, music |
| `10-`–`19x-` | exercise generators, one per topic family |
| `17-`/`18-` | level catalogue and misconception-keyed distractors |
| `20-`–`2B-` | game-rule models: scoring, anti-guessing, lives, adaptive Elo, memory/forgetting, prerequisite DAG |
| `30-`–`32-` | the only modules allowed to touch the DOM |
| `40-`–`44-` | features: game loop, parent panel, bosses, skill map, album |
| `99-` | boot |

Generators are pure by contract — no DOM, and no `Math.random`: the RNG is always injected, so a
seed reproduces a question exactly. There is one global `CB`, no bundler, and one
`DOMContentLoaded` that calls `CB.arranque()`.

Three pieces of wiring explain most behaviour:

- **`CB.pantallas.ir(id)`** is the *only* function that shows or hides a screen across the 18
  `<section id="p-…" class="pantalla" hidden>` elements. A single delegated click listener maps
  `data-ir="<screenId>"` and the valueless `data-salir` attribute onto it, and it emits
  `pantalla` on `CB.bus` — which is how the music follows the screen.
- **`CB.almacen`** is the sole owner of the `cubomatica.*` localStorage keys; schema migrations are
  additive only, and a corrupted profile is salvaged rather than dropped.
- **`CB.catalogo`** declares levels as positional arrays and calls itself a contract. Adaptive
  difficulty tracks Elo **per skill slug** (26 of them), not per level.

The CSS is BEM in Spanish with design tokens on `:root`, and accessibility handled by root classes
(`letra-grande`, `alto-contraste`, `sin-movimiento`) so a stored child preference beats the OS
setting. Breakpoints were mostly height-driven — the original target was a school tablet in
landscape — and the desktop-width ones are newer.

**Width is negotiated through custom properties, never by styling a block from its container.** The
container declares, the block consumes: `.pantalla--mapa` declares `--ancho-contenido: 1040px`,
`.contenido--doble` declares `--ancho-contenido`, `--ancho-panel` and `--ancho-lectura`, and
`.contenido` / `.panel-bloque` / `.texto` each read the property with a fallback. Follow that shape
rather than adding `.pantalla--x .algo { … }` rules.

`.contenido--doble` (Créditos) puts its panels in two flow columns above 1200px. Two things there
were found the hard way and should not be "simplified": the panels are `display: inline-block`,
because with `break-inside: avoid` alone WebKit still left an empty fragment — a dark strip with
the panel's shadow and no content — at the foot of a column; and the columns live on a
`.contenido__paneles` wrapper rather than on `.contenido`, because `column-span: all` on the title
and the exit button fragments the multicol and scrambles the panel order.

Flow columns are right for a screen that fits in about one scroll. They are wrong for a long one:
Ayuda has 18 panels, and newspaper columns would mean reading to the bottom and scrolling all the
way back up. It stays in a single column on purpose — but a **wide** one. `.contenido--ancho`
(3.7.1) declares `--ancho-contenido: 1040px / --ancho-panel: 100% / --ancho-lectura: 52ch` at
1200px and 1240px / 60ch at 1600px, and Ayuda, Mis vetas, Mi álbum and «¿Quién juega?» consume it.
60 characters is the ceiling: past that the eye loses the start of the next line, which costs a
seven-year-old more than it costs you. Ajustes and the Diccionario were tried and reverted — a
label with its blocks, or a term with its one-line definition, only gains empty space.

**The players are seven years old, and that decides wording as much as layout.** The in-game HUD
labels (`.indicador__rotulo`) say what a thing is *for*, never what the fiction calls it: the
helmet lights are labelled **Vidas**, not «Luces», because «Luces» only makes sense once you have
read the Ayuda screen. For the same reason the clock counts plain seconds rather than `1:19`, and
the progress reads «Pregunta 3 de 20» rather than «3/20» — minutes:seconds and fractions are both
notations that 2.º de Primaria has not been taught. Label size is
`calc(var(--tam-texto-min) * .8)` rather than a fixed px so the stored «Letra grande» preference
scales it too. Apply the same test to any text you add.

**The fiction stays, but it has to be bridged.** The helmet lights run through the sprites, the
SFX and the game rules, so they were not renamed. What was added is the bridge: the Ayuda panel
is «Tus vidas: las luces del casco» and opens with «Arriba, donde pone VIDAS, tienes tres luces
en el casco», and `CB.a11y.textoLuces` announces «Vidas: 3 luces encendidas de 3» so a screen
reader says what the label shows. Where «luz» appeared *before* that panel it now says «vida».
If you add fiction vocabulary to a label, add the bridge in the same change.

The labels are set in caps at the owner's request. All-caps costs a new reader the word shape, so
size is doing the legibility work instead, and they carry `letter-spacing: .06em` — the game's
global `.05em` is tuned for lower case and reads tight in caps. Keep both if you touch the rule.

## Commands

```bash
uv sync --all-extras                 # create .venv/ and install pinned deps
uv run cubomatica                    # run the app from source
CUBOMATICA_DEBUG=1 uv run cubomatica # …with WebKit DevTools enabled
uv run pytest                        # full suite (79 tests, fast)
uv run ruff check .                  # lint
./build-mac.sh                       # -> dist/Cubomatica.app, ad-hoc signed
./make-icon.sh                       # regenerate assets/icon.icns from assets/icon.svg

# keep index.html readable (--comprobar only reports, writes nothing)
python3 herramientas/formatear-html.py src/cubomatica/web/index.html
```

Run one test or one class:

```bash
uv run pytest tests/test_api.py -v
uv run pytest tests/test_web.py::TestPersistencia -v
```

`uv` pins Python 3.11 via `.python-version` (the system Python is 3.13), and `[tool.uv]
required-version = ">=0.12.0"` rejects older uv. Every dependency is pinned with `==` on purpose;
`tests/test_web.py::TestPyprojectToml` fails the build if a `==` goes missing.

`build-mac.sh` ends with `codesign --force --deep --sign -`. That ad-hoc signature is **not
optional** on Apple Silicon — macOS kills an unsigned bundle on launch.

## Python side

`main.py` is the whole runtime: `localizar_index()` finds `index.html`, then one window opens and
`webview.start()` runs. Three details are load-bearing, and each was a real bug:

- **The URL must be a `file://` URI** (`url=index.as_uri()`). Handed a bare path, pywebview treats
  it as local and starts an internal HTTP server — and with `private_mode=False` that server always
  binds the **fixed port 42001**. One leftover instance is enough to make the next launch render
  `Error: 404 Not Found` instead of the game. `file://` starts no server at all.
- **The path must be `.resolve()`d.** Inside the bundle the web folder is reached through a symlink
  (`Contents/Frameworks/cubomatica` → `../Resources/cubomatica`); WKWebView loads the unresolved
  path as a blank white window, with no error anywhere.
- **`private_mode=False`** is the only thing that makes `localStorage` persist — the game keeps
  every profile and all progress under the `cubomatica.*` prefix. **`storage_path` does nothing on
  macOS**: the Cocoa backend always uses `WKWebsiteDataStore.defaultDataStore()`, i.e.
  `~/Library/WebKit/<bundle id>/WebsiteData/`. It is kept only for Windows/Linux. A practical
  consequence: the `.app` (`es.javiertamarit.cubomatica`) and `uv run cubomatica`
  (`org.python.python`) keep **separate** saved games.

`tests/test_web.py::TestPersistencia` and `::TestUrlDeCarga` guard the first and third; do not
"simplify" them away.

**The window opens in real full screen** — what the green button does — because the game targets a
landscape tablet. `width`/`height` (1280×800) are therefore the size the window *returns* to when
someone leaves full screen, not the startup size.

`pantalla_completa()` does this itself, and neither `fullscreen=True` nor `maximized=True` is
passed to `create_window`. Both were tried:

- `maximized=True` only calls `maximize()`, which resizes the window to the screen. macOS keeps it
  below the menu bar and the title bar stays visible — it is Option-green, not green.
- `fullscreen=True` calls `toggleFullScreen_` before the window is on screen, and macOS drops the
  message with no error. It works perhaps two launches in three. **This is intermittent, so a
  single successful launch proves nothing** — the flakiness is what cost the time.

So `pantalla_completa()` waits for `shown`, then *checks* rather than asks: it reads the native
window's `styleMask` for `NSWindowStyleMaskFullScreen` and retries up to four times. Verified 9
launches out of 9. Everything touching AppKit goes through `AppHelper.callAfter` (UI thread only)
and the waiting happens on a worker thread. `tests/test_web.py::TestPantallaCompleta` guards it.

**The native "Juego" menu is hand-built with PyObjC on purpose.** `webview.start(menu=...)` is
broken on macOS in pywebview 5.3.2 in two independent ways, and both fail silently: `start()`
installs the menu before the window is created and window creation then calls `_clear_main_menu()`,
so it never appears; and even when it does, the objects receiving the click are garbage-collected
because Cocoa does not retain an `NSMenuItem`'s target, leaving a menu that opens and does nothing.
`instalar_menu()` therefore builds it after the `loaded` event and parks the targets in
`_REFERENCIAS_MENU`. Menu entries live in `MENU_PANTALLAS`; each runs `CB.pantallas.ir(...)`, the
game's own router. Every action must dispatch its JS on a separate thread — `evaluate_js` waits on
the UI thread, so calling it from a menu action freezes the app permanently.

`api.py` exposes a `js_api` bridge (public methods reach JS as `window.pywebview.api.*`, underscore
methods stay private). It was **empty on purpose** until 4.9.0 and now carries exactly three
methods — `guardar_texto`, `abrir_texto`, `imprimir` — because **the parent panel's four ways out
to the world do not work under WKWebView on their own**:

- `window.print()` is not implemented. It raises nothing and opens nothing: the button looked fine
  and printed nothing. `imprimir()` runs `printOperationWithPrintInfo:` on the native `WKWebView`
  as a sheet, and macOS's print panel includes «PDF ▸ Guardar como PDF», so it covers saving too.
- **`<a download href="blob:…">` is worse than useless: WKWebView does not download it, it
  NAVIGATES to it.** The window left the game, rendered the CSV as plain text, and with no address
  bar and no back button there was no way back — the app had to be relaunched. `guardar_texto()`
  puts up the native save panel instead.
- `<input type="file">` does open the native picker (pywebview implements
  `runOpenPanelWithParameters`), but only from a real user gesture; the game clicks it from
  JavaScript, so it worked by luck. `abrir_texto()` has no gesture to depend on.

JS reaches all three through `CB.adulto.puente()`, which returns `null` in a plain browser — where
`window.print()` and the blob link work fine and stay the fallback path. `tests/test_api.py` pins
the exposed set exactly, and `tests/test_web.py::TestSalidasDelPanelAdulto` pins the JS side,
including that the bridge is tried **before** the blob.

**Everything the user reads is Spanish, including the dialogs the game does not paint.** Save,
open and print panels are drawn by macOS, which picks their language by intersecting the user's
preferred languages with the ones the *bundle declares* — and declaring none meant English panels
on a Mac set to es-ES. `Cubomatica.spec` therefore carries `CFBundleDevelopmentRegion: "es"` and
`CFBundleLocalizations: ["es"]` (4.9.1); check with
`NSBundle.bundleWithPath_(...).preferredLocalizations()`, which must answer `['es']`. The panel
*title* is separate and comes from pywebview, whose default dictionary is English too: `main.py`
passes its own `TEXTOS` as `localization=`. Both halves are needed — the dictionary alone leaves
the buttons in English, the plist alone leaves the title as «Save file» — and `TestIdioma` guards
each. Running from source (`uv run cubomatica`) keeps the English buttons, because the process
bundle is then Python.app; that is expected and not a regression.

Related: **`text_select=True` is passed to `create_window`** (4.9.0). pywebview defaults it to
False and then injects `body { user-select: none }` into any page, which left the parent panel —
legal notice, metrics, recommendations — impossible to select or copy. The switch is on and the
CSS decides where selection is worth having: off across the game (dragging over an answer block
would paint it blue), on in `.pantalla--documento` and `#p-creditos`, off again on their buttons.
`TestSeleccionDeTexto` guards both halves; turning the flag on without the CSS half is a
regression, not a fix.

`.github/workflows/ci.yml` runs lint, tests, the HTML format check and a `node --check` of the
bundle on every push and PR, then builds the `.app` on `macos-latest` and uploads it as an artifact.

## Packaging

`Cubomatica.spec` bundles `src/cubomatica/web` to `cubomatica/web` inside the app, force-includes the
Cocoa/WebKit modules PyInstaller cannot detect, and excludes the Windows/GTK/Qt webview backends. It
picks up `assets/icon.icns` automatically when present.

The `.app` is ~69 MB, of which ~42 MB is the nine music tracks in `web/audio/` (Pixabay Content
License, credited in `web/audio/CREDITOS.txt`). All nine tracks and all twelve `web/img/*.webp`
coin/banknote images are referenced by the game — none are dead files.

## Failure modes specific to this shell

- **`Error: 404 Not Found` on `http://127.0.0.1:42001/index.html`** — the URL regressed to a bare
  path, so pywebview started its HTTP server on the fixed port and something else already held it.
  Check for leftovers with `lsof -nP -iTCP:42001`.
- **Blank white window** — the path was not resolved through the bundle's symlink, or an asset path
  is absolute. Absolute paths like `/css/style.css` work over HTTP but break under `file://`.
  `tests/test_web.py::TestRutasRelativas` checks the HTML for both. Diagnose with
  `CUBOMATICA_DEBUG=1`, which prints the resolved index path and URL to stderr.
- **Progress disappears on restart** — `private_mode` regressed to its default.
- **A button in the parent panel does nothing, or the window leaves the game and shows raw text** —
  something regressed to the browser path. Print and downloads must go through `api.py`; see the
  bridge section above. The blob-link failure is the loud one: the app has no way back.
- **Text cannot be selected or copied** — `text_select=True` went missing from `create_window`, or
  the CSS rules that re-enable selection on the document screens did.
- **Finder shows a stale icon** — icon cache, not a build failure: `touch dist/Cubomatica.app &&
  killall Finder Dock`.

## Provenance

This shell was built from the author's own **Pyzarra** template (`~/Desktop/pyzarra`), a
pywebview + uv starter. Its layout, its pinned-version discipline and the shape of the test suite
come from there, so changes that drift from that structure should be deliberate.
