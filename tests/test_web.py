"""
Tests de la web.

Estos tests atrapan el error MAS COMUN de pywebview:
la ventana se abre en blanco porque falta un archivo
o porque una ruta es absoluta.
"""

import json
import re
import shutil
import subprocess
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
            "css/cubomatica.css",
            "js/cubomatica.js",
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

    def test_no_hay_gemelos_minificados(self, web_dir):
        """
        Hasta 4.5.0 index.html cargaba cubomatica.min.css y cubomatica.min.js,
        y los ficheros legibles viajaban al lado sin que nada los ejecutara:
        cada cambio habia que aplicarlo a mano en los dos. Bajo file:// la
        minificacion no ahorra nada perceptible, asi que se cargan los
        legibles y los .min desaparecen. Si alguien los vuelve a crear, este
        test lo dice antes de que nadie edite el fichero equivocado.
        """
        minificados = list(web_dir.rglob("*.min.*"))
        assert not minificados, f"Han vuelto los gemelos minificados: {minificados}"

    def test_index_carga_los_ficheros_legibles(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        assert 'href="css/cubomatica.css"' in html
        assert 'src="js/cubomatica.js"' in html
        assert ".min." not in html


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


class TestIdsUnicos:
    """
    Dos elementos con el mismo `id` no dan ningun error: `getElementById`
    devuelve el PRIMERO del documento y el segundo se queda mudo para siempre.

    Paso de verdad en 4.10.0. La portada estrenaba un boton «Seguir cavando en
    el Bosque» y lo llamo `btn-seguir`, que era el nombre del boton de la
    pantalla de descanso desde el principio. El de descanso -el unico que se
    veia- dejo de responder, y encima el de la portada se quedaba con su
    `onclick` pegado: al pulsarlo arrancaba la expedicion y ademas servia un
    item de mas.
    """

    def _ids(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        return re.findall(r'\sid="([^"]+)"', html)

    def test_ningun_id_se_repite(self, web_dir):
        repes = sorted(
            {i for i in self._ids(web_dir) if self._ids(web_dir).count(i) > 1}
        )
        assert not repes, "ids repetidos en index.html: " + ", ".join(repes)

    def test_los_dos_seguir_cavando_se_llaman_distinto(self, web_dir):
        """
        Son dos botones con el mismo rotulo y distinto trabajo: el de la
        portada retoma la expedicion de ayer, el del descanso vuelve al item.
        """
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        assert 'id="btn-seguir-expedicion"' in html
        assert 'id="btn-seguir"' in html
        # cada uno se busca por su nombre, y el del descanso desde la partida
        assert js.count("getElementById('btn-seguir-expedicion')") == 2
        assert js.count("getElementById('btn-seguir')") == 1


class TestIconografia:
    """Los iconos son sprites de 03-sprites, no emojis.

    Un emoji se pinta con la fuente del sistema, suavizado y con otro estilo,
    encima de un juego de bloques: es lo que más delata «web» frente a «juego».
    Desde 3.6.0 cada icono es un sprite publicado como --sprite-<nombre>.
    """

    EMOJI = re.compile(
        "[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u25C0\u23F8\u232B\u263A\u2639]"
    )

    def test_index_sin_emojis(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        hallados = sorted(set(self.EMOJI.findall(html)))
        assert hallados == [], f"emojis en index.html: {hallados}"

    def test_sprites_publicados(self, web_dir):
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        assert "CB.sprites.publicar = function" in js
        assert "CB.sprites.publicar();" in js
        assert "--sprite-llave" in css
        assert ".icono-px" in css


class TestBorrado:
    """Se puede deshacer lo empezado, sin pasar por el panel del adulto.

    Hasta 3.7.2 un minero solo se borraba entrando con el, abriendo la llave y
    escribiendo BORRAR, y la expedicion a medias no se podia dejar: JUGAR decia
    «Seguir jugando» hasta que caducaba a las 24 h.
    """

    def test_quitar_minero_existe_y_va_detras_de_un_modo(self, web_dir):
        """
        Esta pantalla la ve el nino: nada de un aspa en cada ficha, que se toca
        sin querer y se lleva por delante al hermano.
        """
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        assert 'id="btn-quitar-minero"' in html
        assert "CB.perfiles.modoQuitar" in js
        assert "CB.perfiles.preguntarQuitar" in js
        assert "CB.almacen.borrarPerfil(entrada.id)" in js

    def test_el_modo_quitar_no_sobrevive_a_crear_ni_a_vaciarse(self, web_dir):
        """
        Se apaga ANTES de pintar los botones: apagandolo despues, quitar el
        ultimo minero dejaba la pantalla sin «Nuevo minero».
        """
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        cuerpo = js[js.index("CB.perfiles.pintar = function"):]
        cuerpo = cuerpo[: cuerpo.index("CB.perfiles.PREGUNTA_CURSO")]
        apagado = cuerpo.index("if (!idx.length) CB.perfiles.modoQuitar = false;")
        pintado = cuerpo.index("btn.hidden = CB.perfiles.modoQuitar")
        assert apagado < pintado, "el modo se apaga despues de pintar los botones"

    def test_la_expedicion_a_medias_se_puede_dejar(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        assert 'id="btn-descartar"' in html
        assert "CB.partida.descartarGuardada = function" in js
        assert "perfil.partidaEnCurso = null" in js


class TestAnchoDeLectura:
    """Una columna, pero ancha.

    Ayuda son 18 paneles y las columnas de periodico obligarian a leer hasta
    abajo y volver a subir, asi que se queda en una columna. Eso no obliga a
    leerla en una tira de 640 px con media pantalla vacia al lado.
    """

    PANTALLAS_ANCHAS = ["p-perfiles", "p-cantera", "p-casa", "p-ayuda"]

    def test_el_modificador_declara_los_tres_anchos(self, web_dir):
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        assert ".contenido--ancho" in css
        assert "--ancho-contenido: 1040px" in css
        assert "--ancho-lectura: 52ch" in css
        # y el escalon de las pantallas de 1920
        assert "--ancho-contenido: 1240px" in css
        assert "--ancho-lectura: 60ch" in css

    def test_la_linea_no_pasa_de_60_caracteres(self, web_dir):
        """
        60 es el techo: mas alla el ojo pierde el principio del renglon
        siguiente, y quien lee tiene siete anos.
        """
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        anchos = [int(n) for n in re.findall(r"--ancho-lectura:\s*(\d+)ch", css)]
        assert anchos, "ha desaparecido --ancho-lectura"
        assert max(anchos) <= 60, f"linea demasiado larga: {max(anchos)}ch"

    def test_lo_consumen_las_pantallas_que_lo_ganan(self, web_dir):
        """
        Ajustes y el Diccionario se probaron y se revirtieron: una etiqueta con
        sus bloques, o un termino con su definicion de una linea, solo ganan
        hueco vacio.
        """
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        secciones = re.findall(
            r'<section id="(p-[a-z-]+)".*?</section>', html, re.S
        )
        assert secciones, "no se han encontrado las pantallas"
        cuerpos = dict(
            zip(secciones, re.findall(r'<section id="p-[a-z-]+".*?</section>', html, re.S))
        )
        for pid in self.PANTALLAS_ANCHAS:
            assert "contenido--ancho" in cuerpos[pid], f"{pid} ha perdido el ancho"
        for pid in ("p-ajustes", "p-glosario"):
            assert "contenido--ancho" not in cuerpos[pid], f"{pid} no lo quiere"


class TestEleccionDeCurso:
    """El curso manda en todo el contenido y se declara una sola vez.

    Hasta 3.7.0 la pregunta iba debajo de un h1 que seguia diciendo «¿Quien
    juega?», en letra mas pequena que el titulo, y despues de contestarla el
    curso no volvia a aparecer en ninguna pantalla: colarse al crear el perfil
    solo se notaba porque las preguntas salian raras.
    """

    def test_el_paso_de_crear_se_lleva_el_titular(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        assert 'id="titulo-perfiles"' in html
        assert "CB.perfiles.PREGUNTA_CURSO" in js
        assert "h1.textContent = CB.perfiles.PREGUNTA_CURSO" in js
        # y vuelve a su sitio al pintar la lista
        assert "h1.textContent = CB.perfiles.TITULO" in js

    def test_la_portada_dice_quien_juega_y_en_que_curso(self, web_dir):
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        assert 'id="portada-quien"' in html
        assert "CB.arranque.quienJuega = function" in js
        assert "de Primaria" in js

    def test_la_partida_dice_en_que_curso_se_esta(self, web_dir):
        """
        La franja de la partida decia el mundo y la veta, pero no el curso:
        con el mismo nombre de veta en varios cursos, la unica forma de saber
        en cual jugaba el nino era salir al panel de personas adultas.

        Se pinta el curso del MINERO, no el de la veta: una expedicion puede
        servir una veta de un curso anterior para repasar.
        """
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        assert 'id="hud-veta-curso"' in html
        assert "CB.ui.pintarVeta = function (nivel, mundo, curso)" in js
        assert "CB.ui.pintarVeta(nivel, e.mundo, CB.catalogo.cursoDe(CB.perfil))" in js
        # Sin curso no debe quedarse el separador «▸» huerfano.
        assert ".rotulo-veta__curso:empty" in css

    def test_la_ficha_del_minero_pinta_el_sprite(self, web_dir):
        """
        CB.sprites.avatar dibuja los 16 mineros desde 3.0.0 y no lo llamaba
        nadie: la ficha pintaba un cuadrado del color del casco.
        """
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        assert "CB.sprites.aplicar(av, 'avatar'" in js
        assert ".tarjeta-perfil__mote" in css
        assert ".tarjeta-perfil__jugar" in css

    def test_las_esquinas_de_la_portada_conservan_su_absolute(self, web_dir):
        """
        `.pantalla > *:not(.cielo)...` levanta el contenido sobre el cielo con
        `position: relative`, y pisaba el `absolute` de las dos esquinas: la
        llave acababa arriba a la IZQUIERDA, movida por su propio `right`.
        """
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        regla = [
            linea
            for linea in css.splitlines()
            if linea.startswith(".pantalla > *:not(.cielo)")
        ]
        assert regla, "ha desaparecido la regla de capas de .pantalla"
        assert ":not(.portada__llave)" in regla[0]
        assert ":not(.portada__quien)" in regla[0]


class TestAjustesAccesibilidad:
    """Alto contraste y animaciones son requisitos, y Ajustes es su sitio."""

    def test_ajustes_del_nino_exponen_contraste_y_movimiento(self, web_dir):
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        inicio = js.index("CB.ajustesNino = function")
        cuerpo = js[inicio : js.index("/* Créditos */", inicio)]
        assert "altoContraste" in cuerpo
        assert "reduceMotion" in cuerpo
        assert "CB.ui.selector(" in cuerpo


class TestSeleccionDeTexto:
    """
    Se puede copiar el texto del panel de personas adultas.

    pywebview trae `text_select` APAGADO y, cuando lo esta, inyecta
    `body { -webkit-user-select: none }` en cualquier pagina. Eso dejaba el
    panel -aviso legal, metricas, recomendaciones- imposible de seleccionar,
    sin que hubiera una sola linea del juego pidiendolo.
    """

    def test_main_enciende_la_seleccion(self):
        main = (ROOT / "src" / "cubomatica" / "main.py").read_text(encoding="utf-8")
        assert "\n        text_select=True," in main, (
            "sin text_select=True pywebview apaga la seleccion en toda la pagina"
        )

    def test_el_juego_decide_donde_vale(self, web_dir):
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        # Apagada por defecto: son bloques que se tocan, no un documento.
        assert re.search(r":root \{[^}]*user-select: none", css, re.S), (
            "encender text_select sin apagarla en el juego pinta de azul los "
            "bloques al arrastrar el dedo"
        )
        # Y encendida donde el texto es para leer y copiar.
        assert ".pantalla--documento *" in css
        assert "#p-creditos *" in css

    def test_los_botones_de_esas_pantallas_siguen_fuera(self, web_dir):
        css = (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")
        assert ".pantalla--documento button" in css, (
            "seleccionar el rotulo de un boton al pulsarlo es ruido"
        )


class TestIdioma:
    """
    Todo lo que ve el usuario esta en espanol, incluidos los dialogos que NO
    pinta el juego.

    Los de guardar, abrir e imprimir los pinta macOS, y elige idioma cruzando
    los del usuario con los que DECLARA el paquete. Sin declarar ninguno, el
    panel de guardar salia en ingles ("Save file", "Cancel") en un Mac
    configurado en es-ES. El titulo lo pone ademas pywebview, cuyo diccionario
    por defecto tambien esta en ingles.
    """

    def test_el_paquete_declara_el_espanol(self):
        spec = (ROOT / "Cubomatica.spec").read_text(encoding="utf-8")
        assert '"CFBundleLocalizations": ["es"]' in spec, (
            "sin esto macOS pinta los dialogos nativos en ingles"
        )
        assert '"CFBundleDevelopmentRegion": "es"' in spec

    def test_los_rotulos_de_pywebview_van_traducidos(self):
        main = (ROOT / "src" / "cubomatica" / "main.py").read_text(encoding="utf-8")
        assert '"localization": TEXTOS,' in main, (
            "pywebview usa su diccionario en ingles si no se le pasa otro"
        )
        assert '"global.saveFile": "Guardar fichero"' in main
        assert '"global.cancel": "Cancelar"' in main


class TestSalidasDelPanelAdulto:
    """
    Las cuatro salidas al mundo del panel adulto (informe, CSV, copia .json y
    restaurar) funcionan DENTRO de la aplicacion, no solo en un navegador.

    Bajo WKWebView, `window.print()` no hace nada -y no lanza excepcion- y la
    descarga por `<a download href="blob:...">` es peor que inutil: no
    descarga, NAVEGA al blob. La ventana se iba del juego, pintaba el CSV como
    texto plano, y sin barra de direcciones ni boton de atras no habia forma de
    volver. Comprobado pulsando los botones de verdad dentro de la app.
    """

    def _js(self, web_dir) -> str:
        return (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")

    def test_imprimir_pasa_por_el_puente(self, web_dir):
        js = self._js(web_dir)
        assert "CB.adulto.imprimir = function" in js
        assert "b.onclick = CB.adulto.imprimir;" in js, (
            "el boton Imprimir no puede llamar directo a window.print(): "
            "WKWebView no lo implementa y el boton se queda mudo"
        )
        assert js.count("b.onclick = CB.adulto.imprimir;") == 2, (
            "hay DOS sitios que conectan el boton: el informe y la ficha de "
            "refuerzo; si solo se arregla uno, el otro sigue mudo"
        )

    def test_guardar_pasa_por_el_dialogo_nativo(self, web_dir):
        js = self._js(web_dir)
        inicio = js.index("CB.adulto.descargar = function")
        cuerpo = js[inicio : js.index("CB.adulto.confirmarBorrado", inicio)]
        assert "api.guardar_texto(" in cuerpo, (
            "dentro de la app hay que guardar con el dialogo nativo"
        )
        assert cuerpo.index("api.guardar_texto(") < cuerpo.index("a.download"), (
            "el blob es el CAMINO DE RESPALDO para el navegador; si va "
            "primero, dentro de la app se lleva la pagina por delante"
        )

    def test_el_puente_es_opcional(self, web_dir):
        js = self._js(web_dir)
        assert "CB.adulto.puente = function" in js
        assert "window.pywebview && window.pywebview.api" in js, (
            "en un navegador normal no hay puente y el juego debe seguir"
        )

    def test_restaurar_no_depende_del_gesto_humano(self, web_dir):
        js = self._js(web_dir)
        inicio = js.index("CB.adulto.restaurar = function")
        cuerpo = js[inicio : js.index("CB.adulto.confirmarBorrado", inicio)]
        assert "api.abrir_texto(" in cuerpo, (
            "el <input type=file> solo abre el selector si el clic nace de un "
            "gesto humano, y aqui lo dispara JavaScript"
        )
        assert cuerpo.index("api.abrir_texto(") < cuerpo.index("input.click()"), (
            "el input es el camino de respaldo del navegador"
        )
        assert "CB.adulto.aplicarCopia" in cuerpo, (
            "los dos caminos deben compartir la validacion"
        )

    def test_sin_perfil_todavia_se_puede_restaurar(self, web_dir):
        """
        La copia de seguridad sirve sobre todo cuando NO queda nada. El boton
        vivia solo en la seccion Datos de un perfil, asi que desaparecia justo
        el dia que hacia falta: con el indice vacio, el panel ofrecia «Salir»
        y nada mas.
        """
        js = self._js(web_dir)
        inicio = js.index("CB.adulto.pintar = function")
        cuerpo = js[inicio : js.index("CB.adulto.metrica = function", inicio)]
        sin_perfil = cuerpo[: cuerpo.index("const m = CB.adulto.metricas(perfil);")]
        assert "CB.adulto.restaurar" in sin_perfil, (
            "sin minero elegido tiene que poder restaurarse una copia"
        )
        assert "adulto-aviso-datos" in sin_perfil, (
            "y con su hueco de aviso, o el resultado no se ve"
        )

    def test_la_copia_restaurada_recuerda_el_curso(self, web_dir):
        js = self._js(web_dir)
        assert "curso: p.curso" in js, (
            "desde 4.8.0 la ficha de «¿Quién juega?» lee el curso del indice"
        )


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
        return (web_dir / "css" / "cubomatica.css").read_text(encoding="utf-8")

    @pytest.mark.parametrize("cara", CARAS)
    def test_la_fuente_viaja_en_el_paquete(self, web_dir, cara):
        assert (web_dir / "fonts" / cara).is_file(), f"Falta fonts/{cara}"

    @pytest.mark.parametrize("cara", CARAS)
    def test_el_css_la_declara(self, web_dir, cara):
        assert f"../fonts/{cara}" in self._css(web_dir), f"El CSS no declara {cara}"

    def test_es_la_fuente_de_lectura(self, web_dir):
        # Con espacios y comillas simples o dobles: la hoja es la legible.
        patron = r"--fuente-lectura:\s*['\"]OpenDyslexic['\"]"
        assert re.search(patron, self._css(web_dir)), "OpenDyslexic no es la fuente de lectura"

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


class TestLicencia:
    """
    El juego se distribuye, asi que tiene que decir de quien es y que se puede
    hacer con el.

    El aviso viaja DENTRO de web/, no solo en la raiz del repositorio: quien
    recibe el .app no recibe el repositorio. Y el credito de la tipografia no
    es una cortesia, es lo que exige su CC BY 3.0.
    """

    AUTOR = "JavierTamaritWeb"

    def test_el_juego_lleva_su_licencia(self, web_dir):
        assert (web_dir / "LICENCIA.txt").is_file(), (
            "web/LICENCIA.txt viaja dentro del .app; sin el, lo que se "
            "distribuye no dice de quien es"
        )

    def test_el_repositorio_lleva_su_licencia(self):
        assert (ROOT / "LICENSE").is_file()

    @pytest.mark.parametrize("ruta", ["LICENSE", "src/cubomatica/web/LICENCIA.txt"])
    def test_declara_el_copyright(self, ruta):
        texto = (ROOT / ruta).read_text(encoding="utf-8")
        assert self.AUTOR in texto, f"{ruta} no declara el copyright"

    @pytest.mark.parametrize("ruta", ["LICENSE", "src/cubomatica/web/LICENCIA.txt"])
    def test_excluye_el_material_de_terceros(self, ruta):
        """
        Reservarse todos los derechos SIN excluir la fuente y la musica seria
        reclamar derechos sobre obra ajena.
        """
        texto = (ROOT / ruta).read_text(encoding="utf-8")
        assert "OpenDyslexic" in texto and "Pixabay" in texto, (
            f"{ruta} no deja fuera el material de terceros"
        )

    def test_el_juego_ensena_el_copyright(self, web_dir):
        """En pantalla, no solo en un .txt que nadie abre."""
        js = (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")
        assert self.AUTOR in js, "el copyright no aparece en los creditos del juego"
        assert "CB.LEGAL.COPYRIGHT" in js, "el panel de aviso legal no lo pinta"


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


class TestBancoDePreguntas:
    """El juego no repite preguntas por costumbre (3.10.0).

    Hasta 3.9.x la semilla de cada expedición salía de perfil + fecha + n.º de
    partidas: salir a medias y volver a entrar el mismo día daba el mismo guion
    y las mismas preguntas, y nada recordaba entre partidas qué ítems se habían
    servido. Ahora la semilla es nueva en cada partida (y viaja con la partida
    guardada para poder reanudarla), y `2C-vistos.js` guarda por veta los
    últimos ítems servidos para preferir lo que el niño no ha visto. De paso,
    el banco de enunciados se dobla: 80 nombres y 120 objetos.
    """

    @pytest.fixture
    def js(self, web_dir):
        return (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")

    @staticmethod
    def _cuerpo(js, nombre):
        """El texto de `nombre = function` hasta la siguiente definición CB.*."""
        ini = js.index(f"{nombre} = function")
        fin = js.find("\nCB.", ini + 1)
        return js[ini:fin]

    @staticmethod
    def _node(tmp_path, script):
        node = shutil.which("node")
        if not node:
            pytest.skip("hace falta node para cargar el bundle sin navegador")
        fichero = tmp_path / "sonda.js"
        fichero.write_text(script, encoding="utf-8")
        salida = subprocess.run([node, str(fichero)], capture_output=True, text=True, timeout=180)
        assert salida.returncode == 0, salida.stderr
        return json.loads(salida.stdout.strip().splitlines()[-1])

    CARGADOR = "const { CB } = require(" + json.dumps(str(ROOT / "herramientas" / "cargar-bundle.js")) + ");\n"

    def test_la_semilla_de_la_partida_no_sale_de_la_fecha(self, js):
        assert "CB.util.semillaAleatoria = function" in js
        iniciar = self._cuerpo(js, "CB.partida.iniciar")
        assert "CB.util.semillaAleatoria()" in iniciar
        assert "hoyISO" not in iniciar, "la semilla volvería a repetirse dentro del mismo día"

    def test_reanudar_conserva_la_semilla_guardada(self, js):
        reanudar = self._cuerpo(js, "CB.partida.reanudarGuardada")
        assert "semilla: p.semillaPartida" in reanudar

    def test_el_combate_del_jefe_tampoco_se_repite(self, js):
        jefes = js[js.index("/* 42-jefes.js"):js.index("/* 43-mapa-destrezas.js")]
        assert "rng: CB.util.mulberry32(CB.util.semillaAleatoria())" in jefes

    def test_hay_memoria_de_items_entre_partidas(self, js):
        assert "/* 2C-vistos.js" in js
        servir = self._cuerpo(js, "CB.partida.servirItem")
        assert "CB.vistos.elegir(perfil, nivelId" in servir
        assert "CB.vistos.anotar(perfil, nivelId" in servir
        podar = self._cuerpo(js, "CB.almacen.podar")
        assert "CB.vistos.podar(perfil, factor)" in podar

    def test_el_banco_de_enunciados_se_ha_doblado(self, js):
        def lista(nombre):
            ini = js.index(f"CB.datos.{nombre} = [")
            return re.findall(r"'([^']+)'", js[ini:js.index("];", ini)])

        assert len(lista("NOMBRES_F")) >= 40
        assert len(lista("NOMBRES_M")) >= 40
        objetos = js[js.index("CB.datos.OBJETOS = ["):]
        objetos = objetos[:objetos.index("];")]
        assert objetos.count("{ sing:") >= 120

    def test_recorre_el_banco_entero_antes_de_repetir(self, tmp_path):
        """La tabla del 2 tiene once preguntas: las once salen antes de que
        vuelva ninguna, y la que vuelve es la más antigua."""
        datos = self._node(tmp_path, self.CARGADOR + """
const n = CB.catalogo.get('M4');
const perfil = { items: {} }, servidos = [];
for (let i = 0; i < 22; i++) {
  const el = CB.vistos.elegir(perfil, 'M4',
    (k) => n.generar(CB.util.mulberry32(i * 7919 + k * 104729 + 1), 2, { techo: 999, ajustes: {} }),
    () => false);
  servidos.push(el.item.expr);
  CB.vistos.anotar(perfil, 'M4', el.clave);
}
console.log(JSON.stringify({
  primeraVuelta: new Set(servidos.slice(0, 11)).size,
  segundaVuelta: new Set(servidos.slice(11)).size,
  vuelveElMasAntiguo: servidos[11] === servidos[0],
  guardado: perfil.items.M4.length
}));
""")
        assert datos["primeraVuelta"] == 11
        assert datos["segundaVuelta"] == 11
        assert datos["vuelveElMasAntiguo"] is True
        assert datos["guardado"] == 11

    def test_los_enunciados_nuevos_pasan_el_validador(self, tmp_path):
        """Los 120 objetos aparecen en los problemas y ninguno tropieza con el
        validador de lectura fácil del juego (lista blanca, ancho, tildes)."""
        datos = self._node(tmp_path, self.CARGADOR + """
const ids = (CB.catalogo._ids || Object.keys(CB.catalogo._porId)).filter((id) => id[0] === 'P');
let total = 0, rechazados = 0;
const vistos = {};
ids.forEach((id) => {
  const n = CB.catalogo.get(id), bolsas = CB.gen.problemas.nuevoEstadoBolsas();
  for (let k = 0; k < 400; k++) {
    const it = n.generar(CB.util.mulberry32(k * 7919 + 13), 1 + (k % 3), { bolsas, techo: 999, ajustes: {} });
    if (!it) continue;
    total++;
    if (!CB.gen.problemas.validar(it).ok) rechazados++;
    (it.frases || []).forEach((f) => CB.datos.OBJETOS.forEach((o) => {
      if (f.indexOf(' ' + o.plur) !== -1) vistos[o.sing] = true;
    }));
  }
});
console.log(JSON.stringify({ total, rechazados, objetos: Object.keys(vistos).length,
                             deLaTabla: CB.datos.OBJETOS.length }));
""")
        assert datos["total"] > 1000
        assert datos["rechazados"] == 0
        assert datos["objetos"] == datos["deLaTabla"] == 120


class TestPistas:
    """Cada veta tiene su pista de método (3.11.0).

    Hasta 3.10.x el botón de pista enseñaba una de las dos frases de la
    DESTREZA: para el mínimo común múltiplo decía «Fíjate bien en cuántas
    cifras tiene el número», y seis destrezas ni eso («Léelo otra vez con
    calma»). `pistas.js` lleva una pista por VETA que cuenta el método con los
    números de la pregunta y sin dar la respuesta; `CB.reparacion.pista` la
    rellena y es lo que enseñan el botón y Rocarr al primer fallo.
    """

    @pytest.fixture
    def js(self, web_dir):
        return (web_dir / "js" / "cubomatica.js").read_text(encoding="utf-8")

    def test_el_boton_y_el_primer_fallo_usan_la_pista_de_la_veta(self, js):
        assert "/* pistas.js" in js and "CB.datos.PISTAS_VETA = {" in js
        boton = TestBancoDePreguntas._cuerpo(js, "CB.partida.accionPista")
        assert "CB.reparacion.pista(e.itemActual)" in boton
        assert "Léelo otra vez con calma" not in boton
        fallo = js[js.index("Escalón 1: pista de Rocarr"):]
        fallo = fallo[:fallo.index("CB.ui.mensaje(")]
        assert "CB.reparacion.pista(item)" in fallo

    def test_el_mcm_y_el_mcd_explican_el_metodo(self, js):
        tabla = js[js.index("CB.datos.PISTAS_VETA = {"):]
        tabla = tabla[:tabla.index("\n};")]
        assert "tablas de multiplicar de los dos números" in tabla   # N42
        assert "dividen a los dos sin dejar resto" in tabla           # N43
        assert "iénsalo" not in tabla and "con calma" not in tabla

    def test_todas_las_vetas_tienen_pista_y_ninguna_da_la_respuesta(self, tmp_path):
        """Cada veta, con 200 semillas y los tres escalones: la pista existe,
        todos los huecos se rellenan y ningún hueco se rellena con la
        respuesta (un número que ya está en el enunciado no cuenta)."""
        datos = TestBancoDePreguntas._node(tmp_path, TestBancoDePreguntas.CARGADOR + """
const ids = CB.catalogo._ids || Object.keys(CB.catalogo._porId);
const sinPista = [], huecos = [], chivatas = [];
ids.forEach((id) => {
  const n = CB.catalogo.get(id), plantilla = CB.datos.PISTAS_VETA[id];
  if (!plantilla) { sinPista.push(id); return; }
  for (let k = 0; k < 200; k++) {
    const it = n.generar(CB.util.mulberry32(k * 7919 + 5), 1 + (k % 3),
                         { techo: 999, ajustes: {}, bolsas: CB.gen.problemas.nuevoEstadoBolsas() });
    if (!it) continue;
    const p = CB.reparacion.pistaDeVeta(it);
    if (p === null) { huecos.push(id); break; }
    if (typeof it.respuesta !== 'number') continue;
    const r = String(it.respuesta).replace('.', ',').replace(/[.*+?^${}()|[\]\\-]/g, '\\$&');
    const re = new RegExp('(^|[^0-9,])' + r + '(?![0-9,])');
    const enunciado = it.frases ? it.frases.join(' ') : String(it.consigna || '');
    if (re.test(p) && !re.test(plantilla) && !re.test(enunciado)) { chivatas.push(id); break; }
  }
});
console.log(JSON.stringify({ vetas: ids.length, sinPista, huecos, chivatas }));
""")
        assert datos["vetas"] == 308
        assert datos["sinPista"] == []
        assert datos["huecos"] == []
        assert datos["chivatas"] == []

    def test_ninguna_destreza_se_queda_sin_pista_de_animo(self, tmp_path):
        datos = TestBancoDePreguntas._node(tmp_path, TestBancoDePreguntas.CARGADOR + """
const ids = CB.catalogo._ids || Object.keys(CB.catalogo._porId);
const sin = {};
ids.forEach((id) => { const d = CB.catalogo.get(id).destreza; if (!CB.datos.MENSAJES.PISTAS[d]) sin[d] = 1; });
console.log(JSON.stringify(Object.keys(sin)));
""")
        assert datos == []
