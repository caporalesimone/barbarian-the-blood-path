import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width":1280,"height":1000})
        await pg.add_init_script(open('hook.js').read())
        await pg.goto("http://localhost:8081/"); await pg.wait_for_timeout(15000)
        r = await pg.evaluate("window.__ev")
        print("picco audio nella pagina:", round(r["peak"],3), "inizi di suono:", len(r["audio"]))
        await pg.screenshot(path="guac_vice.png"); await b.close()
asyncio.run(main())
