/* Carga el bundle del juego en node, sin navegador.
 *
 * Los módulos de la capa 30- tocan el DOM al arrancar (publican texturas y
 * sprites como custom properties), así que se les da un `document` de cartón
 * que acepta todo y no pinta nada. Sirve para llamar a los generadores, al
 * catálogo y a los modelos de reglas —que son puros— desde un script o desde
 * un test. NO sirve para probar la interfaz: para eso está la app.
 *
 *   const { CB } = require('./herramientas/cargar-bundle.js');
 *   CB.catalogo.get('S1').generar(CB.util.mulberry32(7), 2, {});
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const RUTA = path.join(__dirname, '..', 'src', 'cubomatica', 'web', 'js', 'cubomatica.js');

function elemento() {
  return {
    style: { setProperty() {} },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    setAttribute() {}, getAttribute() { return null; }, removeAttribute() {},
    appendChild() {}, addEventListener() {}, removeEventListener() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    getContext() { return null; },
    textContent: '', hidden: false
  };
}

const oyentes = {};
const ventana = global;
ventana.window = ventana;
ventana.addEventListener = function () {};
ventana.removeEventListener = function () {};
ventana.matchMedia = function () { return { matches: false, addEventListener() {}, addListener() {} }; };
ventana.requestAnimationFrame = function (f) { return setTimeout(f, 0); };
ventana.document = {
  documentElement: elemento(), body: elemento(),
  addEventListener(nombre, fn) { oyentes[nombre] = fn; },
  getElementById() { return null; },
  querySelector() { return null; }, querySelectorAll() { return []; },
  createElement() { return elemento(); }
};
ventana.localStorage = {
  _d: {},
  getItem(k) { return this._d[k] == null ? null : this._d[k]; },
  setItem(k, v) { this._d[k] = String(v); },
  removeItem(k) { delete this._d[k]; },
  key(i) { return Object.keys(this._d)[i]; },
  get length() { return Object.keys(this._d).length; }
};
/* node 22 ya trae navigator y crypto como getters: no se pisan. */
if (typeof ventana.navigator === 'undefined') {
  Object.defineProperty(ventana, 'navigator', {
    value: { userAgent: 'node', language: 'es' }, configurable: true
  });
}
ventana.location = { protocol: 'file:', href: 'file:///cubomatica/index.html' };
if (!ventana.performance) ventana.performance = { now: () => Date.now() };

vm.runInThisContext(fs.readFileSync(RUTA, 'utf8'), { filename: 'cubomatica.js' });

module.exports = { CB: ventana.CB, oyentes, RUTA };
