# Playwright (con Chromium) — NON incluso

**Cos'è**: libreria Node che pilota Chromium. Il demone `headless/c64d.js` la usa solo internamente per aprire la pagina dell'emulatore. Non è incluso nel pacchetto: si installa con `npm i -g playwright && npx playwright install chromium` (nel Docker: `playwright@1.63.0`).

**Origine**: https://github.com/microsoft/playwright · https://playwright.dev
**Licenza**: Apache-2.0 (da conoscenza generale, non verificata qui). Chromium, scaricato da Playwright, ha le sue licenze (BSD e componenti di terze parti): https://chromium.googlesource.com/chromium/src/+/main/LICENSE
