// Ciclo di controllo per  c64 runLoop "$(cat loops/bot-joy.js)" '{"frames":300,"every":2}'
// Corpo di funzione con parametri (c64, i, state). return false = fine.
// Dentro runLoop joy(porta,stato,frames) preme e rilascia senza far avanzare il tempo (API 18).
c64.joy(2, { right: (i % 8) < 4, fire: (i % 2) === 0 }, 2);
state.passi = (state.passi || 0) + 1;
if (i >= 100) return false;
