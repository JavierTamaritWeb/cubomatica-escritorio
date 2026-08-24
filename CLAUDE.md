# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

The **desktop packaging shell** for Cubomática, a Spanish primary-school maths game. A pywebview
window loads a local HTML/CSS/JS bundle, and PyInstaller turns it into `dist/Cubomatica.app`.
Desktop only — it is not a web build or a PWA, and it opens no port on the machine.

**Two version numbers, deliberately.** The app version (currently **4.2.0**) is declared in both
`pyproject.toml` and `Cubomatica.spec`, and `tests/test_web.py::TestVersion` fails if they drift
apart. The game has its own, `CB.VERSION` inside the web bundle (currently 3.4.7); it tracks the
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

Three traps come with that, and each will waste an afternoon:

1. `index.html` loads **only** `css/cubomatica.min.css` and `js/cubomatica.min.js`. Editing
   `cubomatica.css` or `cubomatica.js` changes nothing at runtime.
2. …but the non-minified twins still ship, and they are what anyone reads to understand the code.
   **A change goes in both files**, hand-applied: the `.min` one is what runs, the plain one is what
   keeps it legible. Leaving them out of step is how the next reader gets misled.
3. There is no minifier, gulpfile or `package.json` in this repository, so nothing here can
   regenerate a `.min` file from its twin. Minified CSS is one line: use a targeted replacement, not
   a rewrite.

`cubomatica.js` is a concatenation of 56 modules whose boundary comments (`/* 00-nucleo.js`,
`/* 07-musica.js` …) survive in the bundle — see the next section for the map. The CSS is BEM in
Spanish, and the game's accessibility rules are legal requirements rather than preferences: root
classes `letra-grande`, `alto-contraste` and `sin-movimiento` must keep working, and anything that
centres content while also scrolling needs the `safe` keyword (`justify-content: safe center`), or
whatever overflows above becomes unreachable — `scrollTop` cannot go negative.

`src/cubomatica/web/` carries no licence text (`LICENSE`, `AVISO-LEGAL.txt`,
`LICENCIAS-TERCEROS.md` were never copied), so the shipped `.app` carries none either. Worth fixing
before distributing it. There is no `sw.js` either, which is why the game's service-worker
registration silently no-ops — harmless, since a service worker cannot run under `file://` anyway.

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
| `40-`–`45-` | features: parent panel, bosses, skill map, album, offline |
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
way back up. It stays in a single column on purpose.

## Commands

```bash
uv sync --all-extras                 # create .venv/ and install pinned deps
uv run cubomatica                    # run the app from source
CUBOMATICA_DEBUG=1 uv run cubomatica # …with WebKit DevTools enabled
uv run pytest                        # full suite (39 tests, fast)
uv run ruff check .                  # lint
./build-mac.sh                       # -> dist/Cubomatica.app, ad-hoc signed
./make-icon.sh                       # regenerate assets/icon.icns from assets/icon.svg
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
methods stay private). The game does not currently call it; it exists for future needs such as
printing or exporting progress. `tests/test_api.py` locks the public/private contract.

## Packaging

`Cubomatica.spec` bundles `src/cubomatica/web` to `cubomatica/web` inside the app, force-includes the
Cocoa/WebKit modules PyInstaller cannot detect, and excludes the Windows/GTK/Qt webview backends. It
picks up `assets/icon.icns` automatically when present.

The `.app` is ~68 MB, of which ~42 MB is the nine music tracks in `web/audio/` (Pixabay Content
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
- **`window.print()` does nothing** — WKWebView does not implement it, so the game's printable
  report button is inert in the desktop app. Routing it through `api.py` is the fix if it is needed.
- **Finder shows a stale icon** — icon cache, not a build failure: `touch dist/Cubomatica.app &&
  killall Finder Dock`.

## Provenance

This shell was built from the author's own **Pyzarra** template (`~/Desktop/pyzarra`), a
pywebview + uv starter. Its layout, its pinned-version discipline and the shape of the test suite
come from there, so changes that drift from that structure should be deliberate.
