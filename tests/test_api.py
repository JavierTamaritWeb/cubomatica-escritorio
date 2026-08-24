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


class TestPuenteJavaScript:
    def test_hoy_no_expone_nada(self, api):
        """
        El juego no llama al puente. Si esto falla es que alguien ha anadido
        un metodo publico: bien, pero que sea a proposito, con su test y
        con quien lo llame desde JS.
        """
        assert _metodos_publicos(api) == set()

    def test_lo_privado_no_se_expone(self, api):
        """Un metodo con guion bajo no debe contar como publico."""
        assert not any(n.startswith("_") for n in _metodos_publicos(api))

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
