# Cubomática — propuesta de UX/UI conservando la estética Minecraft (24-08-2026)

Diagnóstico sobre la versión 3.5.0 del juego (app 4.6.0), a partir de nueve pantallas
recorridas en el navegador: portada, mapa, partida con acierto, reparación, ajustes, Mis
vetas, álbum, perfiles y panel adulto.

**Implementado en 3.6.0 (app 4.7.0), el 24-08-2026**, con dos decisiones tomadas con el autor:
el modo de juego se queda en el mapa como selector de tres bloques (y en Ajustes), y los cromos
siguen saliendo al azar, con una línea honesta en el álbum en vez de ligarlos a mundos (eso
habría tocado las reglas). El resto, tal como se propone abajo.

**Lo que se mantiene sin discusión:** la tipografía OpenDyslexic, los biseles, las texturas
16×16, los biomas y la paleta tierra/crema. La estética está bien resuelta; lo que sigue es
lo que la haría *jugar* mejor, de más a menos impacto.

---

## 1. La partida: el momento de responder es el más flojo

Es donde el niño pasa el 90 % del tiempo y es la pantalla con menos «juego» en la respuesta.

- **El acierto no se ve en el bloque que tocó.** Al pulsar «8 en punto» el botón queda
  igual; el marco dorado de foco sigue en «9 y media» (que era incorrecta), y el mensaje
  «¡La cantera se llena de luz!» aparece en una cajita pálida abajo a la izquierda, lejos de
  donde miraba. Propuesta: el bloque pulsado **se hunde** (bisel invertido) y se vuelve
  verde-ok; los otros se apagan a piedra; el mensaje va grande junto a las opciones. Con el
  fallo, lo mismo en gris. Es CSS sobre clases que ya existen (`ok-fondo`, `mal-fondo`).
- **El «+1 por rapidez» flota encima de las opciones.** Debería salir de la gema del HUD
  (arriba a la derecha), que es donde se suma. Un «vuelo» de la gema desde el bloque al
  contador, respetando `sin-movimiento`.
- **El HUD se recoloca** cuando desaparece el reloj tras responder: «Pregunta 1 de 20»
  salta de sitio. Reservar el hueco del reloj aunque esté vacío.
- **La barra de avance enseña 10 bloques para 20 preguntas.** Un niño de 7 años cuenta
  bloques; que sean 20 (o que cada acierto rellene medio, visible).
- **El minero mide 16 px** en una ventana de 1280×800: un punto. Los sprites ya se generan a
  8 px en `03-sprites`; escalarlo ×4 con `image-rendering: pixelated` y darle trabajo: pica
  el bloque al acertar, se rasca la cabeza al fallar. Es el gancho emocional más barato que
  tiene el juego y ahora es invisible.
- **El 40 % de la pantalla es cielo vacío.** Las opciones están topadas a 64 px
  (`--lado-techo: 96px`); en escritorio pueden ser bloques de 96–120 px y el panel del
  enunciado puede crecer con ellos.
- **Bug de presentación:** la primera vez que sale un componente aparece el bocadillo
  «▶ Toca el 5» (`CB.componentes.PRESENTACION`, `cubomatica.js` ≈ línea 14096) mientras las
  opciones reales son «9 y media / 8 en punto…». No hay ningún 5. O se presenta con el
  contenido real («Toca la respuesta buena») o con un ítem de demostración de verdad.
- El reloj dibujado tiene el 12 tapado por la aguja y los números pegados al borde: un poco
  más de radio y las cifras fuera del anillo.

## 2. Iconografía: los emojis rompen el pixel art

🔑 en la llave, 🪨 Rocarr, 💡 pista, 🔊 sonido, ⏸ pausa, ✨ chispas: cada uno se pinta con la
fuente de emoji del sistema, suavizado y con otro estilo, encima de un juego de bloques. Es
lo que más delata «web» frente a «juego».

Un juego de **8–10 iconos pixelados** (llave, piedra, bombilla, altavoz, pausa, gema,
candado, cromo, pico), generado como los sprites actuales o como SVG con
`shape-rendering: crispEdges`, unifica todas las pantallas de golpe. Rocarr merece un sprite
con dos o tres caras (normal, asiente, pista).

## 3. Mis vetas: que parezca una mina, no una hoja de cálculo

Treinta tarjetas grises, 26 con candado y el texto «aún cerrada» repetido 26 veces. Para un
lector de 2.º es un muro de texto. La metáfora que ya tiene el juego lo resuelve sola: **un
frente de mina**.

- Vetas cerradas: bloques de piedra con textura y sin texto.
- Vetas disponibles: bloques de mena con brillo y borde dorado (ya existe).
- Vetas superadas: bloques con la gema incrustada.
- El nombre, solo en las disponibles y al tocar/enfocar.

Menos lectura, más Minecraft, y el niño ve *dónde* cavar de un vistazo.

## 4. Mapa de mundos

- Las tarjetas bloqueadas dicen «Se abre al cavar más vetas del mundo anterior». Abstracto.
  Mejor concreto y contable: **«Cava 10 vetas más en la Pradera»** con la barra rellenándose.
- Usar la textura del bioma como **fondo de toda la tarjeta** (hierba, bosque, agua,
  piedra), no solo la tira superior; ahora los cuatro mundos son iguales salvo la franja.
- «MODO: NORMAL» es un botón que cicla y no lo parece; a Ajustes, o convertido en selector
  de tres bloques con el pulsado hundido.
- Cinco botones del mismo peso bajo las tarjetas (Mis vetas, Mi álbum, Diccionario, Ayuda,
  Salir). Jerarquía: Mis vetas y Álbum como bloques con icono; Ayuda y Salir en secundario.

## 5. Álbum y vitrina

Once «?» grises idénticos y veintitrés más. El niño no sabe qué persigue.

- **Silueta** del cromo (a lo Minecraft: el bloque en oscuro) y una línea de cómo se consigue
  («Gana 5 gemas en el Bosque»).
- Los premios, en marcos o cofres; el diploma de 1.º y el de 6.º no deberían parecer el
  mismo cuadrado gris.

## 6. Ajustes

- «Música: MEDIA» y «Modo: NORMAL» son botones que ciclan sin indicarlo. **Selectores
  segmentados** de bloques (Baja / Media / Alta) con el elegido hundido: es el patrón de los
  botones de Minecraft y no hay que adivinar.
- Faltan **Alto contraste** y **Sin movimiento** aquí (solo están en el panel del adulto);
  son requisitos, y este es el sitio.
- «Letra grande» debería verse al instante en la propia pantalla (previsualización en vivo).

## 7. Portada

- «Cantera tranquila» necesita su línea: «sin reloj y sin vidas». Un niño no sabe qué es.
- Para quien vuelve, un bloque **«Seguir cavando en El Bosque»** por encima de JUGAR: ahora
  JUGAR → mapa → tarjeta → cavar son tres toques para lo que hacía ayer.
- El suelo es solo hierba; una franja de biomas (hierba-bosque-agua-piedra) anticipa los
  cuatro mundos y da identidad.

## 8. Transiciones y textura de interfaz

- No hay transición entre pantallas (`hidden` on/off): un corte seco. Una **caída de
  bloque** de 150 ms (la pantalla nueva «cae» y asienta, con `steps()` como ya usan las
  animaciones) da sensación de juego; se anula con `sin-movimiento`.
- Los paneles crema son correctos para leer (mantener), pero sus **marcos** podrían ser de
  piedra texturizada como la GUI clásica de Minecraft: el juego ya genera esa textura y solo
  la usa en el suelo.
- Comprobar que todos los `.btn-bloque` tienen estado `:active` hundido (bisel invertido,
  2 px abajo): es el detalle que hace que un bloque «sea» un bloque.

---

## Orden que seguiría

1. **Respuesta en partida**: hundir bloque, color, mensaje junto a las opciones, HUD estable,
   20 bloques, presentación con contenido real. CSS y JS pequeños, efecto inmediato.
2. **Iconos pixelados** en sustitución de emojis + minero ×4 con animaciones.
3. **Mis vetas** como frente de mina.
4. **Ajustes** con selectores segmentados y los dos ajustes de accesibilidad.
5. **Mapa, álbum, portada y transiciones.**

Nada de esto toca la fuente ni las reglas del juego; todo es capa `30-`/`32-` (los módulos
que tocan el DOM) y CSS. El bloque 1, el de mayor rendimiento, cabe en una tarde.
