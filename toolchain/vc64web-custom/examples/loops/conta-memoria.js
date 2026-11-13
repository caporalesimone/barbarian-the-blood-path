// Incrementa un byte in memoria a ogni passo e si ferma quando arriva a 5:  c64 runLoop "$(cat loops/conta-memoria.js)"
// (a ogni passo il ciclo fa avanzare di 'every' fotogrammi; lo stato 'state' persiste tra i passi ed è restituito)
if (i === 0) c64.poke(0xC000, 0);
const v = c64.peek(0xC000);
state.visto = (state.visto || []).concat(v);
if (v >= 5) return false;
c64.poke(0xC000, v + 1);
