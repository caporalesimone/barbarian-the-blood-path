// misura: istante (Date.now) in cui il rosso compare su un canvas e in cui il tono supera la soglia nell'audio della pagina
(() => {
  if (window.__ev) return;
  window.__ev = { video: [], audio: [], peak: 0 };
  const origConnect = AudioNode.prototype.connect, an = new Map();
  AudioNode.prototype.connect = function (dest, ...rest) {
    if (dest instanceof AudioDestinationNode) {
      let a = an.get(dest.context);
      if (!a) {
        a = dest.context.createAnalyser(); a.fftSize = 256; origConnect.call(a, dest); an.set(dest.context, a);
        const buf = new Float32Array(a.fftSize); let on = false, quiet = 0;
        setInterval(() => {
          a.getFloatTimeDomainData(buf); let m = 0; for (const v of buf) m = Math.max(m, Math.abs(v));
          __ev.peak = Math.max(__ev.peak, m);
          if (!on && m > 0.02) { on = true; quiet = 0; __ev.audio.push(Date.now()); }
          else if (on) { quiet = m < 0.005 ? quiet + 1 : 0; if (quiet > 50) on = false; }
        }, 2);
      }
      return origConnect.call(this, a, ...rest);
    }
    return origConnect.call(this, dest, ...rest);
  };
  let von = false;
  const tick = () => {
    const cs = [...document.querySelectorAll('canvas')].sort((a, b) => b.width * b.height - a.width * a.height);
    for (const c of cs) {
      if (c.width < 300 || c.height < 300) continue;
      let ctx; try { ctx = c.getContext('2d', { willReadFrequently: true }); } catch (e) { continue; }
      if (!ctx) continue;
      const p = ctx.getImageData(10, 10, 1, 1).data;            // angolo in alto a sinistra: fondo dello schermo X
      const red = p[0] > 180 && p[1] < 60 && p[2] < 60;
      if (red && !von) { von = true; __ev.video.push(Date.now()); }
      if (!red && von && p[0] < 60) von = false;
      break;
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();
