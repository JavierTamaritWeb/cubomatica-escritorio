"""
Tests de la web.

Estos tests atrapan el error MAS COMUN de pywebview:
la ventana se abre en blanco porque falta un archivo
o porque una ruta es absoluta.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


class TestArchivosExisten:
    def test_carpeta_web_existe(self, web_dir):
        assert web_dir.is_dir()

    @pytest.mark.parametrize(
        "ruta",
        [
            "index.html",
            "manifest.webmanifest",
            "css/cubomatica.min.css",
            "js/cubomatica.min.js",
        ],
    )
    def test_archivo_existe(self, web_dir, ruta):
        assert (web_dir / ruta).is_file(), f"Falta {ruta}"

    def test_index_no_esta_vacio(self, web_dir):
        assert len((web_dir / "index.html").read_text()) > 100

    def test_hay_imagenes(self, web_dir):
        assert list((web_dir / "img").glob("*.webp")), "No hay imagenes webp"

    def test_hay_audio(self, web_dir):
        assert list((web_dir / "audio").glob("*.mp3")), "No hay ficheros de audio"


class TestRutasRelativas:
    """
    Una ruta absoluta como /css/style.css funciona en el navegador
    con servidor, pero ROMPE dentro del .app.
    """

    def _html(self, web_dir) -> str:
        return (web_dir / "index.html").read_text(encoding="utf-8")

    def test_css_no_usa_ruta_absoluta(self, web_dir):
        malas = re.findall(r'href="(/[^/][^"]*)"', self._html(web_dir))
        assert not malas, f"Rutas absolutas en CSS: {malas}"

    def test_js_no_usa_ruta_absoluta(self, web_dir):
        malas = re.findall(r'src="(/[^/][^"]*)"', self._html(web_dir))
        assert not malas, f"Rutas absolutas en JS: {malas}"

    def test_todos_los_archivos_enlazados_existen(self, web_dir):
        html = self._html(web_dir)
        enlaces = re.findall(r'(?:href|src)="([^"]+)"', html)

        locales = [
            e for e in enlaces
            if not e.startswith(("http://", "https://", "//", "#", "data:"))
        ]

        faltan = [e for e in locales if not (web_dir / e).exists()]
        assert not faltan, f"Enlazados pero no existen: {faltan}"


class TestPersistencia:
    """
    El juego guarda perfiles y progreso en localStorage.
    pywebview arranca por defecto en modo privado, que NO persiste:
    sin private_mode=False se pierde TODO el progreso al cerrar.
    """

    def _main(self) -> str:
        ruta = ROOT / "src" / "cubomatica" / "main.py"
        return ruta.read_text(encoding="utf-8")

    def test_private_mode_desactivado(self):
        assert "private_mode=False" in self._main(), (
            "main.py debe llamar a webview.start(private_mode=False) "
            "o el progreso del juego no se guarda"
        )

    def test_declara_storage_path(self):
        assert "storage_path" in self._main()


class TestUrlDeCarga:
    """
    La ventana DEBE cargar el juego con file://.

    Si se pasa la ruta suelta, pywebview levanta un servidor HTTP interno
    y, con private_mode=False, lo hace siempre en el puerto fijo 42001.
    Basta con que otra instancia (o una colgada) tenga ese puerto para que
    la app abra un "Error: 404 Not Found" en lugar del juego.
    """

    def _main(self) -> str:
        ruta = ROOT / "src" / "cubomatica" / "main.py"
        return ruta.read_text(encoding="utf-8")

    def test_usa_esquema_file(self):
        assert "as_uri()" in self._main(), (
            "main.py debe pasar url=INDEX.as_uri() (file://), no la ruta suelta"
        )

    def test_no_pasa_la_ruta_suelta(self):
        assert "url=str(INDEX)" not in self._main(), (
            "url=str(INDEX) hace que pywebview arranque su servidor HTTP "
            "en el puerto fijo 42001 y provoca el 404 al colisionar"
        )


class TestHtmlLegible:
    """
    index.html se mantiene formateado.

    Es el unico fichero del bundle sin gemelo sin minificar: si vuelve a una
    sola linea, deja de poder revisarse y nadie se entera hasta que hay que
    tocarlo. El formateo es idempotente, asi que basta con comprobar que
    volver a formatearlo no cambia nada.
    """

    def _formateador(self):
        import importlib.util

        ruta = ROOT / "herramientas" / "formatear-html.py"
        spec = importlib.util.spec_from_file_location("formatear_html", ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def test_no_esta_minificado(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        assert html.count("\n") > 100, "index.html ha vuelto a quedar en una sola linea"

    def test_esta_formateado(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        assert self._formateador().formatear(html) == html, (
            "index.html no esta formateado: pasa "
            "python3 herramientas/formatear-html.py src/cubomatica/web/index.html"
        )

    def test_formatear_no_cambia_el_documento(self, web_dir):
        modulo = self._formateador()
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        assert modulo.huella(modulo.formatear(html)) == modulo.huella(html)


class TestTipografia:
    """
    El juego se lee con OpenDyslexic y la fuente viaja DENTRO del bundle.

    Si falta un .otf no salta ningun error: el navegador se cae a Verdana y el
    juego sigue funcionando, solo que sin la tipografia que es media razon de
    ser de esta app. Por eso se comprueba aqui.

    La licencia (CC BY 3.0) obliga a atribuir, asi que el credito en pantalla
    tampoco puede desaparecer sin que nadie se entere.
    """

    CARAS = [
        "OpenDyslexic-Regular.otf",
        "OpenDyslexic-Bold.otf",
        "OpenDyslexic-Italic.otf",
        "OpenDyslexic-BoldItalic.otf",
    ]

    def _css(self, web_dir) -> str:
        return (web_dir / "css" / "cubomatica.min.css").read_text(encoding="utf-8")

    @pytest.mark.parametrize("cara", CARAS)
    def test_la_fuente_viaja_en_el_paquete(self, web_dir, cara):
        assert (web_dir / "fonts" / cara).is_file(), f"Falta fonts/{cara}"

    @pytest.mark.parametrize("cara", CARAS)
    def test_el_css_la_declara(self, web_dir, cara):
        assert f"../fonts/{cara}" in self._css(web_dir), f"El CSS no declara {cara}"

    def test_es_la_fuente_de_lectura(self, web_dir):
        assert '--fuente-lectura:"OpenDyslexic"' in self._css(web_dir)

    def test_la_ruta_de_la_fuente_es_relativa(self, web_dir):
        # Una ruta absoluta funciona sobre HTTP y bajo file:// no carga nada.
        css = self._css(web_dir)
        assert 'url("/fonts' not in css and "url('/fonts" not in css
        assert "url(http" not in css, "la fuente no puede venir de la red: la app es offline"

    def test_la_licencia_viaja_al_lado(self, web_dir):
        assert (web_dir / "fonts" / "LICENCIA-OpenDyslexic.txt").is_file()

    def test_los_creditos_atribuyen(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        assert "OpenDyslexic" in html, "CC BY 3.0 exige el credito en pantalla"


class TestPantallaCompleta:
    """
    La app abre a pantalla completa, como al pulsar el boton verde.

    Pedirselo a pywebview (fullscreen=True en create_window) NO vale: la orden
    sale antes de que la ventana este en pantalla y macOS la descarta sin
    avisar, asi que unas veces entra y otras se queda en 1280x800. Por eso
    main.py habla directamente con Cocoa y COMPRUEBA el resultado.
    """

    def _main(self) -> str:
        ruta = ROOT / "src" / "cubomatica" / "main.py"
        return ruta.read_text(encoding="utf-8")

    def test_pide_pantalla_completa_a_cocoa(self):
        assert "toggleFullScreen_" in self._main(), (
            "main.py debe entrar a pantalla completa con toggleFullScreen_"
        )

    def test_comprueba_que_ha_entrado(self):
        assert "MASCARA_PANTALLA_COMPLETA" in self._main(), (
            "hay que comprobar el styleMask de la ventana: pedirlo una sola "
            "vez y confiar es justo lo que fallaba de forma intermitente"
        )

    def test_no_se_lo_pide_a_pywebview(self):
        # Se busca la forma de ARGUMENTO (sangrado y con coma). Los dos nombres
        # aparecen tambien en los comentarios, explicando por que no se usan.
        texto = self._main()
        assert "\n        fullscreen=True," not in texto, (
            "fullscreen=True en create_window es el camino que falla"
        )
        assert "\n        maximized=True," not in texto, (
            "maximized=True solo redimensiona la ventana; no es pantalla completa"
        )


class TestPyprojectToml:
    def _toml(self) -> dict:
        import tomllib

        ruta = ROOT / "pyproject.toml"
        return tomllib.loads(ruta.read_text(encoding="utf-8"))

    def test_pyproject_es_valido(self):
        assert self._toml()["project"]["name"] == "cubomatica"

    def test_todas_las_versiones_estan_fijadas(self):
        """
        Sin '==' una libreria puede actualizarse sola
        y romper la app sin avisar.
        """
        deps = self._toml()["project"]["dependencies"]
        sueltas = [d for d in deps if "==" not in d]
        assert not sueltas, f"Sin version fija: {sueltas}"

    def test_pywebview_esta_declarado(self):
        deps = self._toml()["project"]["dependencies"]
        assert any(d.startswith("pywebview") for d in deps)


class TestVersion:
    """
    La version esta declarada en dos sitios y tienen que coincidir.

    Si el .spec se queda atras, el .app dice una version y el paquete otra,
    y no lo nota nadie hasta que hay que dar soporte a un usuario.
    """

    def _version_pyproject(self) -> str:
        import tomllib

        ruta = ROOT / "pyproject.toml"
        return tomllib.loads(ruta.read_text(encoding="utf-8"))["project"]["version"]

    def _version_spec(self) -> str:
        texto = (ROOT / "Cubomatica.spec").read_text(encoding="utf-8")
        encontrado = re.search(r'^VERSION\s*=\s*"([^"]+)"', texto, re.MULTILINE)
        assert encontrado, "No encuentro VERSION en Cubomatica.spec"
        return encontrado.group(1)

    def test_coinciden(self):
        assert self._version_pyproject() == self._version_spec(), (
            f"pyproject.toml dice {self._version_pyproject()} "
            f"y Cubomatica.spec dice {self._version_spec()}"
        )

    def test_formato_semantico(self):
        assert re.fullmatch(r"\d+\.\d+\.\d+", self._version_pyproject())


class TestVersionDeUv:
    """
    La version de la HERRAMIENTA uv tambien se controla.
    Si no, cada persona del equipo puede usar un uv distinto
    y generar un uv.lock incompatible.
    """

    def _toml(self) -> dict:
        import tomllib

        ruta = ROOT / "pyproject.toml"
        return tomllib.loads(ruta.read_text(encoding="utf-8"))

    def test_uv_tiene_version_minima_declarada(self):
        assert "required-version" in self._toml()["tool"]["uv"]

    def test_existe_python_version(self):
        ruta = ROOT / ".python-version"
        assert ruta.is_file(), "Falta .python-version"

    def test_python_version_coincide_con_pyproject(self):
        """
        Si .python-version dice 3.11 pero pyproject exige >=3.13,
        uv creara un entorno que no cumple. Fallo silencioso.
        """
        fijado = ROOT / ".python-version"
        version = fijado.read_text(encoding="utf-8").strip()
        requiere = self._toml()["project"]["requires-python"]

        minimo = requiere.replace(">=", "").strip()
        may_f, min_f = (int(x) for x in version.split(".")[:2])
        may_r, min_r = (int(x) for x in minimo.split(".")[:2])

        assert (may_f, min_f) >= (may_r, min_r), (
            f".python-version ({version}) es menor que requires-python ({requiere})"
        )
