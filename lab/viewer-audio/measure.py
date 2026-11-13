# Uso: python3 measure.py URL CONTAINER N [click_selector]   -> ritardi di video e audio rispetto all'evento sul server
import asyncio, subprocess, sys, json, statistics, threading
from playwright.async_api import async_playwright
URL, CT, N = sys.argv[1], sys.argv[2], int(sys.argv[3]); CLICK = sys.argv[4] if len(sys.argv) > 4 else None
HOOK = open('hook.js').read()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 1280, "height": 1000})
        await pg.add_init_script(HOOK)
        await pg.goto(URL); await pg.wait_for_timeout(6000)
        if CLICK:
            for f in pg.frames:
                try:
                    if CLICK.startswith("js:"): await f.evaluate(CLICK[3:])
                    else: await f.click(CLICK, timeout=3000)
                    print("click", CLICK); break
                except Exception as e: pass
            await pg.wait_for_timeout(2000)
        out = await asyncio.to_thread(subprocess.run, ["docker", "exec"] + (["-u", "abc"] if CT == "kasm" else []) + [CT, "sh", "/opt/proto/event.sh", str(N)], capture_output=True, text=True)
        await pg.wait_for_timeout(2500)
        ev = [int(l.split()[1]) for l in out.stdout.splitlines() if l.startswith("EVENT")]
        vids, auds, peak = [], [], 0
        for f in pg.frames:
            try: r = await f.evaluate("window.__ev || null")
            except Exception: r = None
            if r: vids += r["video"]; auds += r["audio"]; peak = max(peak, r["peak"])
        await pg.screenshot(path="shot_%s.png" % CT)
        await b.close()
    def lat(xs):
        d = []
        for t in ev:
            c = [x - t for x in xs if 0 <= x - t < 3000]
            d.append(min(c) if c else None)
        return d
    dv, da = lat(sorted(vids)), lat(sorted(auds))
    print("eventi", len(ev), "video rilevati", len(vids), "audio rilevati", len(auds), "picco audio %.3f" % peak)
    print("video ms:", dv); print("audio ms:", da)
    for name, d in (("video", dv), ("audio", da)):
        x = [v for v in d if v is not None]
        if x: print("%s: mediana %d ms, min %d, max %d (%d/%d)" % (name, statistics.median(x), min(x), max(x), len(x), len(d)))
    av = [a - v for a, v in zip(da, dv) if a is not None and v is not None]
    if av: print("audio - video: mediana %d ms, min %d, max %d" % (statistics.median(av), min(av), max(av)))
asyncio.run(main())
