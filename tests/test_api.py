"""
Tests del puente JavaScript <-> Python (api.py).

pywebview expone a JS todos los metodos publicos de la instancia que se pasa
como js_api. Estos tests protegen ese contrato: nada llega a JS por accidente
y, cuando se anada un metodo, tendra que ser serializable como JSON.
"""

import inspect


def _metodos_publicos(api) -> set[str]:
    return {
        n
        for n in dir(api)
        if not n.startswith("_") and callable(getattr(api, n))
    }


# Lo que el puente expone HOY, y nada mas. Cada nombre esta aqui porque hay
# JavaScript que lo llama; ver tests/test_web.py::TestSalidasDelPanelAdulto.
EXPUESTOS = {"guardar_texto", "abrir_texto", "imprimir"}


class TestPuenteJavaScript:
    def test_expone_exactamente_lo_previsto(self, api):
        """
        Si esto falla es que alguien ha anadido o quitado un metodo publico:
        bien, pero que sea a proposito, con su test y con quien lo llame
        desde JS. Hasta 4.8.2 el conjunto estaba VACIO.
        """
        assert _metodos_publicos(api) == EXPUESTOS

    def test_lo_privado_no_se_expone(self, api):
        """Un metodo con guion bajo no debe contar como publico."""
        assert not any(n.startswith("_") for n in _metodos_publicos(api))

    def test_la_ventana_no_llega_a_javascript(self, api):
        """
        El puente guarda la ventana de pywebview para los dialogos nativos y
        para imprimir. Tiene que viajar en un atributo privado: un objeto
        Window no es serializable como JSON y romperia el puente entero.
        """
        assert hasattr(api, "_ventana")
        assert "_asociar" not in _metodos_publicos(api)

    def test_todo_lo_publico_es_serializable(self, api):
        """
        pywebview envia argumentos y retornos como JSON. Un metodo publico
        cuya firma pida algo que no sea un tipo simple falla en silencio
        en el puente; se comprueba por las anotaciones.
        """
        simples = {str, int, float, bool, list, dict, type(None), inspect.Signature.empty}
        for nombre in _metodos_publicos(api):
            firma = inspect.signature(getattr(api, nombre))
            for parametro in firma.parameters.values():
                assert parametro.annotation in simples, f"{nombre}: {parametro}"
            assert firma.return_annotation in simples, nombre

    def test_no_revientan_sin_ventana(self, api):
        """
        Quien llama es JavaScript: una excepcion aqui solo deja una promesa
        rechazada y un boton mudo. Sin ventana asociada tienen que devolver
        su dict con el motivo.
        """
        r = api.guardar_texto("prueba.txt", "hola")
        assert r["ok"] is False and r["motivo"]
        r = api.abrir_texto(".json")
        assert r["ok"] is False and r["motivo"]
        r = api.imprimir()
        assert r["ok"] is False and r["motivo"]
