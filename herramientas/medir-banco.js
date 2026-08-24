/* Mide el banco de preguntas y cuánto se repite entre partidas.
 *
 *   node herramientas/medir-banco.js            # todas las vetas
 *   node herramientas/medir-banco.js S3 M4 B3   # solo esas
 *
 * Para cada veta cuenta cuántos ítems DISTINTOS produce el generador en 3000
 * tiradas por escalón de dificultad (D1, D2, D3): eso es el banco real, que
 * no siempre coincide con la cardinalidad declarada en el catálogo. Después
 * simula doce partidas seguidas con seis ítems de esa veta y mide qué parte
 * de cada partida ya había salido en la anterior, sin memoria (como hasta
 * 3.9.x) y con CB.vistos (desde 3.10.0). El suelo matemático no es cero: con
 * un banco de 10 y seis ítems por partida, dos de cada seis tienen que
 * repetirse.
 */
'use strict';

const { CB } = require('./cargar-bundle.js');

const TIRADAS = 3000, PARTIDAS = 12, POR_PARTIDA = 6;

function contexto() {
  return { techo: 999, ajustes: {}, bolsas: CB.gen.problemas.nuevoEstadoBolsas() };
}

function banco(nivel, D) {
  const vistos = new Set();
  for (let k = 0; k < TIRADAS; k++) {
    const it = nivel.generar(CB.util.mulberry32(k * 104729 + 7), D, contexto());
    if (it) vistos.add(it.expr);
  }
  return vistos.size;
}

function repeticion(nivel, conMemoria) {
  const perfil = { items: {} };
  let previa = new Set(), repetidos = 0, servidos = 0;
  for (let g = 0; g < PARTIDAS; g++) {
    const semilla = CB.util.hash32('partida' + g + nivel.id);
    const sesion = {}, actual = new Set();
    for (let i = 0; i < POR_PARTIDA; i++) {
      const generar = (k) => nivel.generar(
        CB.util.mulberry32(semilla + i * 7919 + k * 104729), 2, contexto());
      let item = null;
      if (conMemoria) {
        const el = CB.vistos.elegir(perfil, nivel.id, generar, (c) => !!sesion[c.expr]);
        if (el) { item = el.item; CB.vistos.anotar(perfil, nivel.id, el.clave); }
      } else {
        for (let k = 1; k <= 12 && !item; k++) {
          const c = generar(k);
          if (c && !sesion[c.expr]) item = c;
        }
      }
      if (!item) continue;
      sesion[item.expr] = true; actual.add(item.expr); servidos++;
      if (previa.has(item.expr)) repetidos++;
    }
    previa = actual;
  }
  return servidos ? Math.round(100 * repetidos / servidos) : 0;
}

const pedidos = process.argv.slice(2);
const ids = (CB.catalogo._ids || Object.keys(CB.catalogo._porId))
  .filter((id) => !pedidos.length || pedidos.indexOf(id) !== -1);

console.log('veta  declarado    D1    D2    D3   repite antes  repite ahora   nombre');
let sumaDeclarada = 0, sumaReal = 0;
ids.forEach((id) => {
  const n = CB.catalogo.get(id);
  const d = [1, 2, 3].map((D) => banco(n, D));
  sumaDeclarada += n.cardinalidad;
  sumaReal += Math.max.apply(null, d);
  console.log(
    id.padEnd(5) + String(n.cardinalidad).padStart(9) +
    d.map((x) => String(x).padStart(6)).join('') +
    String(repeticion(n, false) + '%').padStart(15) +
    String(repeticion(n, true) + '%').padStart(14) +
    '   ' + n.nombre);
});
console.log('\nvetas: ' + ids.length + '   banco declarado: ' + sumaDeclarada +
            '   banco real (máximo por veta en ' + TIRADAS + ' tiradas): ' + sumaReal);
