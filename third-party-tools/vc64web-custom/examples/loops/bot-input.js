// Bot per la prova di determinismo (API 24): usa TUTTI i tipi di input (joystick tenuto, joystick con durata,
// tasto tenuto, tasto con durata) e occupa la CPU dell'host per 0-13 ms a passo, per provocare i ritardi del browser.
// Il bersaglio (shell/11-determinismo.sh) e' un programma a $C000 che legge $DC00 senza sosta e ne fa un istogramma a $C100,
// piu' il buffer di tastiera del KERNAL: un input perso o spostato di un fotogramma cambia la RAM e quindi l'hash.
const t = performance.now(), d = (i * 7919) % 14;
while (performance.now() - t < d) {}
const D = ['up', 'down', 'left', 'right', 'fire'], st = {};
D.forEach((x, k) => st[x] = ((i >> k) & 1) === 1 && !(x === 'down' && (i & 1)));
c64.joy(2, st);
if (i % 7 === 0) c64.keyDown('a');
if (i % 7 === 3) c64.keyUp('a');
if (i % 11 === 0) c64.type('s', { frames: 5 });
if (i % 13 === 5) c64.joy(1, { fire: true }, 3);
