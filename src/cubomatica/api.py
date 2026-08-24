"""
Puente JavaScript -> Python.

Cada metodo PUBLICO de esta clase llega a JavaScript como

    await window.pywebview.api.<nombre>(...)

Reglas del puente:
- Los metodos que empiezan por "_" NO se exponen a JavaScript.
- Los argumentos y el retorno deben ser tipos simples (str, int, list, dict, bool):
  pywebview los serializa como JSON, y algo raro falla en silencio.
- Esperar en JS al evento "pywebviewready": window.pywebview.api no existe
  todavia cuando la pagina termina de cargar.

Hoy el juego es autocontenido y NO llama a nada de aqui: la clase esta vacia
a proposito. Hasta 4.5.0 llevaba tres metodos de ejemplo heredados de la
plantilla (saludar, info_sistema, elegir_archivo) que viajaban dentro del
.app sin que nadie los usara. Cuando haga falta disco o sistema (guardar la
copia de seguridad con un dialogo nativo, imprimir el informe...), el metodo
se anade aqui y tests/test_api.py protege el contrato publico/privado.
"""


class Api:
    pass
