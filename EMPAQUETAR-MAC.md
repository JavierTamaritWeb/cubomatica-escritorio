# Empaquetar para macOS (.app)

---

## Paso 1 — Instalar PyInstaller

Ya viene declarado en el grupo `dev` del `pyproject.toml`. Basta con:

```bash
uv sync --all-extras
```

---

## Paso 2 — Construir

```bash
chmod +x build-mac.sh
./build-mac.sh
```

Resultado: **`dist/Cubomatica.app`**

Doble clic y funciona.

---

## Si prefieres a mano

```bash
uv run pyinstaller --noconfirm Cubomatica.spec
codesign --force --deep --sign - dist/Cubomatica.app
```

⚠️ **El `codesign` NO es opcional en Apple Silicon (M1/M2/M3/M4).**
Sin él, macOS mata la app al abrirla.

---

## Icono

**Ya esta hecho.** El icono vive en `assets/icon.icns` y el `.spec` lo detecta solo.

El dibujo es el cubo de tres caras (amarillo, verde y azul sobre fondo marron),
el **mismo** que el `<link rel="icon">` de `web/index.html`. La fuente esta en
`assets/icon.svg`.

### Regenerarlo

Si cambias `assets/icon.svg`, vuelve a construir el `.icns` con:

```bash
./make-icon.sh
./build-mac.sh    # para que la app coja el icono nuevo
```

Necesita ImageMagick (`brew install imagemagick`). El script rasteriza el SVG
y genera los 10 tamanos que pide macOS (de 16 a 1024 px).

### Si partes de un PNG en vez de un SVG

Con un PNG de 1024x1024 puedes hacerlo a mano, sin ImageMagick:

```bash
mkdir -p assets icon.iconset

sips -z 16 16     mi-logo.png --out icon.iconset/icon_16x16.png
sips -z 32 32     mi-logo.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     mi-logo.png --out icon.iconset/icon_32x32.png
sips -z 64 64     mi-logo.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   mi-logo.png --out icon.iconset/icon_128x128.png
sips -z 256 256   mi-logo.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   mi-logo.png --out icon.iconset/icon_256x256.png
sips -z 512 512   mi-logo.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   mi-logo.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 mi-logo.png --out icon.iconset/icon_512x512@2x.png

iconutil -c icns icon.iconset -o assets/icon.icns
rm -rf icon.iconset
```

### Si el Finder sigue enseñando el icono viejo

macOS cachea los iconos. Fuerza el refresco:

```bash
touch dist/Cubomatica.app
killall Finder Dock
```

---

## Modo debug (DevTools)

En Cubomática el debug **ya viene apagado por defecto**.
Se activa solo bajo demanda con una variable de entorno:

```bash
CUBOMATICA_DEBUG=1 uv run cubomatica
```

No hay que tocar nada antes de publicar.

---

## Universal (Intel + Apple Silicon)

En `Cubomatica.spec`, dentro de `EXE(...)`:

```python
target_arch="universal2",
```

⚠️ Solo funciona si **todas** tus librerías tienen build universal.
Si falla, déjalo en `None` (compila solo para tu Mac).

---

## Problemas típicos

| Síntoma | Causa | Solución |
|---|---|---|
| Ventana en blanco | La web no se copió | Revisa `datas=` en el `.spec` |
| "La app está dañada" | Falta firma | Ejecuta el `codesign` |
| Se cierra al instante | Error de Python | Ver comando de abajo |
| No encuentra `index.html` | Ruta absoluta en HTML | Usa rutas relativas |
| Se pierde el progreso al cerrar | `private_mode` activado | `main.py` debe llamar `webview.start(private_mode=False)` |

**Ver el error real** (abre la app desde terminal y muestra los mensajes):
```bash
./dist/Cubomatica.app/Contents/MacOS/Cubomatica
```

---

## Distribuir a otras personas

| Situación | Qué necesitas |
|---|---|
| Solo tú | Nada más. Ya está. |
| Amigos / equipo | Ellos: botón derecho → Abrir → Abrir (1ª vez) |
| Público general | Cuenta Apple Developer (99 €/año) + notarización |

---

## ⚠️ Importante

El `.app` **solo funciona en macOS**.
Para Windows hay que compilar **desde un Windows** — PyInstaller no hace cruzado.
El .app pesa unos 60–70 MB: la mayor parte es la música (`web/audio/`, ~42 MB).
