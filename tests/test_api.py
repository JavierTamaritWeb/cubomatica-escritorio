"""
Tests de la logica Python (api.py).

Aqui va TODO lo que se pueda probar sin abrir una ventana.
"""

import pytest


class TestSaludar:
    def test_devuelve_el_nombre(self, api):
        assert api.saludar("Javi") == "Hola, Javi"

    def test_devuelve_texto(self, api):
        assert isinstance(api.saludar("X"), str)

    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("Ana", "Hola, Ana"),
            ("", "Hola, "),
            ("Mamen Ramos", "Hola, Mamen Ramos"),
            ("José Ñoño", "Hola, José Ñoño"),
        ],
    )
    def test_varios_nombres(self, api, entrada, esperado):
        assert api.saludar(entrada) == esperado


class TestInfoSistema:
    def test_devuelve_diccionario(self, api):
        assert isinstance(api.info_sistema(), dict)

    def test_tiene_las_claves_esperadas(self, api):
        datos = api.info_sistema()
        assert set(datos) == {"sistema", "version_python", "hora"}

    def test_ningun_valor_vacio(self, api):
        for clave, valor in api.info_sistema().items():
            assert valor, f"La clave '{clave}' vino vacia"

    def test_formato_de_hora(self, api):
        hora = api.info_sistema()["hora"]
        h, m, s = hora.split(":")
        assert 0 <= int(h) <= 23
        assert 0 <= int(m) <= 59
        assert 0 <= int(s) <= 59


class TestPuenteJavaScript:
    """
    pywebview solo expone a JS los metodos publicos.
    Estos tests protegen ese contrato.
    """

    def _metodos_publicos(self, api) -> set[str]:
        return {
            n
            for n in dir(api)
            if not n.startswith("_") and callable(getattr(api, n))
        }

    def test_metodos_esperados_estan_expuestos(self, api):
        publicos = self._metodos_publicos(api)
        assert {"saludar", "info_sistema", "elegir_archivo"} <= publicos

    def test_metodos_privados_no_se_exponen(self, api):
        assert "_ayuda_interna" not in self._metodos_publicos(api)

    def test_todo_lo_publico_es_serializable(self, api):
        """
        pywebview envia los datos a JS como JSON.
        Si un metodo devuelve algo raro, el puente falla en silencio.
        """
        import json

        json.dumps(api.saludar("test"))
        json.dumps(api.info_sistema())
