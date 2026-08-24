#!/usr/bin/env bash
#
# Genera assets/icon.icns a partir de assets/icon.svg
#
# El SVG es el mismo dibujo que el <link rel="icon"> de web/index.html,
# asi que el icono de la app y el del navegador son identicos.
#
# Uso:  ./make-icon.sh
#
set -euo pipefail

SVG="assets/icon.svg"
ICNS="assets/icon.icns"
SET="icon.iconset"

if ! command -v magick >/dev/null 2>&1; then
  echo "ERROR: falta ImageMagick.  Instalalo con:  brew install imagemagick" >&2
  exit 1
fi

echo "==> 1/3  Rasterizando $SVG"
rm -rf "$SET"
mkdir -p "$SET" assets

# Master grande: se rasteriza una vez y de ahi salen todos los tamanos.
# La densidad alta evita bordes dentados en el cubo y en las esquinas.
magick -background none -density 3200 "$SVG" -resize 2048x2048 "$SET/_master.png"

echo "==> 2/3  Creando los 10 tamanos que pide macOS"
# Formato:  "archivo pixeles"
while read -r nombre px; do
  magick "$SET/_master.png" -filter Lanczos -resize "${px}x${px}" "$SET/$nombre"
done <<'TAMANOS'
icon_16x16.png 16
icon_16x16@2x.png 32
icon_32x32.png 32
icon_32x32@2x.png 64
icon_128x128.png 128
icon_128x128@2x.png 256
icon_256x256.png 256
icon_256x256@2x.png 512
icon_512x512.png 512
icon_512x512@2x.png 1024
TAMANOS

rm "$SET/_master.png"

echo "==> 3/3  Empaquetando en .icns"
iconutil -c icns "$SET" -o "$ICNS"
rm -rf "$SET"

echo ""
echo "LISTO -> $ICNS"
echo ""
echo "El Cubomatica.spec lo detecta solo. Ahora reconstruye la app:"
echo "  ./build-mac.sh"
