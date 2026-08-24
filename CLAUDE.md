# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

The **desktop packaging shell** for Cubomática, a Spanish primary-school maths game. A pywebview
window loads a local HTML/CSS/JS bundle, and PyInstaller turns it into `dist/Cubomatica.app`.
Desktop only — it is not a web build or a PWA, and it opens no port on the machine.

**Two version numbers, deliberately.** The app version (currently **4.0.0**) is declared in both
`pyproject.toml` and `Cubomatica.spec`, and `tests/test_web.py::TestVersion` fails if they drift
apart. The game has its own, `CB.VERSION` inside the web bundle (currently 3.4.7), which is set
upstream and must not be edited here.

The Python here is deliberately thin (two short modules). **The game itself is not developed in this
repository** — see the next section before touching anything under `src/cubomatica/web/`.

Everything user-facing is in Spanish: UI, docs, comments, test names. Match that when writing.

## `src/cubomatica/web/` is generated output — do not edit it

It is a byte-identical copy of `~/Desktop/mathsgame/dist/`. **`~/Desktop/mathsgame` is the real
game project**: a git repo with a gulp build, ESLint/Stylelint, SCSS under `src/scss/`, and 49
numbered JS modules under `src/js/` (`00-nucleo.js`, `01-almacen.js`, … `19a-gen-division.js`, …).

Two traps that waste a lot of time:

1. `index.html` loads **only** `css/cubomatica.min.css` and `js/cubomatica.min.js`. Editing
   `cubomatica.js` or `cubomatica.css` here changes nothing at runtime — they ship as dead weight.
2. `cubomatica.js` is itself a concatenation of the numbered source modules (the boundary comments
   `/* 00-nucleo.js`, `/* 07-musica.js` … survive in the bundle). There is no minifier, gulpfile or
   `package.json` in this repository, so nothing here can regenerate the `.min` files.

To change game behaviour: edit in `~/Desktop/mathsgame`, run `npm run build` there, then copy
`dist/` over `src/cubomatica/web/`. **Read `~/Desktop/mathsgame/CLAUDE.md`** — it documents the game
architecture, its enforced contracts and its accessibility constraints, which are legal requirements
rather than preferences.

The copy currently omits six files present in `mathsgame/dist/`: `sw.js`, `.huellas.json`, `LICENSE`,
`AVISO-LEGAL.txt`, `LEEME.txt` and `LICENCIAS-TERCEROS.md`. The missing `sw.js` is why the game's
service-worker registration silently no-ops; the missing licence files mean the shipped `.app`
carries no licence text, which is worth fixing before distributing it.

## Orienting inside the bundle (read-only — fix upstream)

You will sometimes need to *read* `cubomatica.js` to trace a bug before fixing it in `mathsgame`.
It is 18k lines but navigable: the 56 concatenated modules (49 from `src/js/`, 7 data tables from
`src/datos/`) each keep their header comment, so this prints the table of contents with line numbers:

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

The CSS is BEM in Spanish with design tokens on `:root`, zero comments, and accessibility handled by
root classes (`letra-grande`, `alto-contraste`, `sin-movimiento`) so a stored child preference beats
the OS setting. Breakpoints are mostly height-driven: the target is a school tablet in landscape.

## Commands

```bash
uv sync --all-extras                 # create .venv/ and install pinned deps
uv run cubomatica                    # run the app from source
CUBOMATICA_DEBUG=1 uv run cubomatica # …with WebKit DevTools enabled
uv run pytest                        # full suite (36 tests, fast)
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
