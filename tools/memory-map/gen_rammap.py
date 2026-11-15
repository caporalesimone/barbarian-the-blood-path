#!/usr/bin/env python3
"""Mappa della RAM del C64 per Barbarian: The Blood Path -> out/work/memory-map/mappa_ram.html
Indirizzi letti da out/work/game.lbl e out/work/lobby.lbl dove possibile (dopo ./build.sh); il resto e' descritto
qui a mano (zone di sistema, scenari d'uso). Uso: python3 tools/memory-map/gen_rammap.py [out.html]"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "work", "memory-map", "mappa_ram.html")


def labels(fn):
    d = {}
    for l in open(os.path.join(ROOT, "out", "work", fn)):
        m = re.match(r"\s*(\S+)\s*=\s*\$([0-9a-f]+)", l)
        if m:
            d[m.group(1)] = int(m.group(2), 16)
        m = re.match(r"\s*(\S+)\s*=\s*(\d+)\s*$", l)
        if m:
            d[m.group(1)] = int(m.group(2))
    return d


L = labels("game.lbl")
M = labels("lobby.lbl")
GFXD, GFXE = L["gfx_data"], L["gfx_end"]          # grafica fissa nel PRG (dato morto dopo copy_gfx)
GENI, GENIE = L["gen_img"], L["gen_img_end"]       # immagine del generatore nel PRG (copiata sotto l'I/O)
GENA = L["GEN_AT"]; GENE = GENA + (GENIE - GENI)   # generatore sotto l'I/O
FINAT = L["FIN_AT"]; FINE = FINAT + os.path.getsize(os.path.join(ROOT, "out", "work", "fmap.prg")) - 2
CODE2E = L["code2_end"]
MENUE = M["menu_end"]
ZXAT = int(re.search(r"GAME_ZX_AT\s*=\s*\$([0-9a-f]+)", open(os.path.join(ROOT, "out", "work", "pack.inc")).read()).group(1), 16)
MN = labels("menu.lbl")                            # (11/11) modulo MENU: zone 1-3 (src/menu.asm)
MZ = [(L["MR%d_AT" % k], MN["mz%d_top" % k], L["MR%d_END" % k]) for k in (1, 2, 3)]
LVLE, CHRE, RELE = L["LVLEND"], L["CHREND"], L["rel_end"]
_MT = open(os.path.join(ROOT, "out", "work", "music_tab.inc")).read()
SMAX = int(re.search(r"SND_SMAX\s*=\s*(\d+)", _MT).group(1)); FMAX = int(re.search(r"SND_FMAX\s*=\s*(\d+)", _MT).group(1))
TOWNE = 0xE000 + os.path.getsize(os.path.join(ROOT, "out", "work", "gfx0.prg")) - 2
DUNA, NMA, NMI = L["GFX_DUN_AT"], L["NM_AT"], L["GFX_INFO"]   # (15/11) tema del dungeon da $EC6D; blocco info dei mostri a NM_AT
ARE = labels("arena.lbl")["ar_end_"] if os.path.exists(os.path.join(ROOT, "out", "work", "arena.lbl")) else 0xCD66
LDE = None                                          # fine del corpo di START (indirizzo logico a $A000)
_SL = "start.lst"                       # (11/11) un solo START per i due dischi
for l in open(os.path.join(ROOT, "out", "work", _SL)):
    m = re.match(r"^\.[0-9a-f]{4}\s+([0-9a-f]{4})\s+body_end", l)
    if m:
        LDE = int(m.group(1), 16)
assert LDE, "body_end non trovato in out/" + _SL

# ------------------------------------------------------------------ categorie
CAT = {
    "sys":   ("Sistema (KERNAL, stack, vettori)", "--c-sys"),
    "io":    ("I/O e ROM", "--c-io"),
    "code":  ("Codice del gioco", "--c-code"),
    "data":  ("Dati / tabelle del gioco", "--c-data"),
    "vic":   ("Video: schermi, charset, sprite", "--c-vic"),
    "var":   ("Variabili del gioco", "--c-var"),
    "cache": ("Cache (grafica, stato piani)", "--c-cache"),
    "boot":  ("Solo all'avvio (START / titolo)", "--c-boot"),
    "free":  ("Libera (uso condizionato o non classificato)", "--c-free"),
    "freec": ("LIBERA per codice e dati, senza vincoli", "--c-freec"),
    "freeio": ("LIBERA per codice con I/O spento (o dati)", "--c-freeio"),
    "freed": ("LIBERA solo per dati", "--c-freed"),
}
FREE = ("free", "freec", "freeio", "freed")


def R(a, b, name, cat, desc="", ver="", multi=None):
    return dict(a=a, b=b, name=name, cat=cat, desc=desc, ver=ver, multi=multi)


V = "verificata in VICE"
S = "solo analisi statica"

# ------------------------------------------------------------------ mappa principale (64 KB)
MAIN = [
    ("Pagina zero e pagine di sistema", [
        R(0x0000, 0x0001, "Porta del 6510", "sys", "$00 direzione, $01 configurazione: $36 in gioco (BASIC off, I/O e KERNAL on); $35 / $34 per leggere la RAM sotto KERNAL / I/O"),
        R(0x0002, 0x003A, "Pagina zero del gioco", "var", "tmp0-7, ptr0-3, rnd, px/py, camera, schermo attivo (front), tx/ty, joystick, puntatori della UI", multi="zp"),
        R(0x003B, L["zp_end"] - 1, "Pagina zero del gioco: UI", "var", "(11/11) ui_cur, ui_n, ui_col, ui_ib, ui_sel, ui_lc (istruzioni piu' corte)", multi="zp"),
        R(L["zp_end"], 0x004F, "Libera", "free", "", S),
        R(0x0050, 0x0064, "ZX0 e caricamento del MENU", "var", "ZX_ZP $50-$5B (decompressore), ml_len/ml_src/ml_i $5C-$64 (ovl_town)"),
        R(0x0065, 0x008C, "Pagina zero del modulo MENU", "var", "Variabili della locanda $65-$81 e dei negozi $82-$8C (src/menu/inn.asm, shop.asm)"),
        R(0x008D, 0x008F, "Libera", "free", "", S),
        R(0x0090, 0x00FA, "Pagina zero del KERNAL", "sys", "ST ($90), seriale, nome file, tastiera: usata dalle routine di I/O del KERNAL"),
        R(0x00FB, 0x00FE, "Pagina zero libera", "free", "All'avvio la usano START e il loader (zp0/zp1); in gioco libera", S),
        R(0x00FF, 0x00FF, "Temporaneo del BASIC", "sys"),
        R(0x0100, 0x01FF, "Stack del 6510", "sys", "Il gioco lo azzera (txs) a ogni ritorno al menu"),
        R(0x0200, 0x0258, "Buffer di input del BASIC", "free", "Non usato dal gioco", S),
        R(0x0259, 0x0276, "Tabelle dei file aperti (KERNAL)", "sys", "LAT/FAT/SAT: 10 file al massimo; il gioco ne usa 2 (REL + comandi) o 1 (PRG / precaricamento)"),
        R(0x0277, 0x02A6, "Tastiera e variabili del KERNAL", "sys", "Buffer della tastiera, limiti di memoria, colori, RS-232"),
        R(0x02A7, 0x02B1, "Segnali START -> gioco", "var", "$02A7 LOBBY gia' a $C000, $02A8 villaggio in cache, $02A9-$02B0 liberi, $02B1 elenco eroi gia' letto. Non azzerati da game_start"),
        R(0x02B2, 0x02FF, "Pagina 2 libera", "free", "", S),
        R(0x0300, 0x0333, "Vettori di sistema", "sys", "IRQ $0314, BRK, NMI, vettori del KERNAL"),
        R(0x0334, 0x03FF, "Buffer del registratore", "free", "Libera (in build di debug: $03F0-$03F3 misure dei tempi)", S),
    ]),
    ("Programma GAME ($0400-$9D8F, caricato all'avvio da START; nessuno stub BASIC)", [
        R(0x0400, L["mod_db"] - 1, "main.asm: nucleo", "code", "GAME_ENTRY $0400 (lo schermo del BASIC: libero, il VIC usa il banco 2). Avvio, copy_gfx, main_loop, disegno della mappa, copie, RLE, IRQ di base"),
        R(L["mod_db"], L["mod_dungeon"] - 1, "db.asm: database", "data", "Oggetti, PG per livello, abilita', mostri, curve, bottino, negozi, nomi (generato da tools/build/gen_db.py)"),
        R(L["mod_dungeon"], L["mod_data"] - 1, "dungeon.asm: parte residente del generatore", "code", "tile_to_pix, clear_map, seed_level, gen_dungeon + gen_call (passa al codice sotto l'I/O), fin_doors, fin_chests. Il generatore vero e' a $%04X (spaccato 4)" % GENA),
        R(L["mod_data"], L["mod_game"] - 1, "data.asm: tabelle", "data", "Indirizzi delle righe di MAP e EXPL"),
        R(L["mod_game"], L["mod_combat"] - 1, "game.asm: logica di gioco", "code", "Mostri, bottino, bauli, azioni sui tile, abilita'"),
        R(L["mod_combat"], L["mod_levels"] - 1, "combat.asm: regole d20", "code", "Statistiche del PG e dei mostri, tiri d'attacco, danni, Rage/Frenzy, pozioni, esperienza"),
        R(L["mod_levels"], L["mod_ui"] - 1, "levels.asm: cambio piano", "code", "Villaggio, change_level, STASH, nuovo eroe, game_start"),
        R(L["mod_ui"], L["mod_hud"] - 1, "ui.asm: schermate", "code", "Inventario, negozi, baule, minimappa, menu RUN/STOP, leva e vittoria (piano 20)"),
        R(L["mod_hud"], L["mod_bar"] - 1, "hud.asm: IRQ raster e HUD", "code"),
        R(L["mod_bar"], L["mod_music"] - 1, "bar.asm: barra e etichette", "code"),
        R(L["mod_music"], L["mod_theme"] - 1, "music.asm + player SID (sid_player.inc) + effetti", "code", "I brani sono file SNDn su disco (docs/musica.md)"),
        R(L["mod_theme"], L["mod_rel"] - 1, "theme.asm: tema del piano, bit di visita", "code"),
        R(L["mod_rel"], L.get("mod_cheats", GFXD) - 1, "rel.asm: salvataggi REL", "code", "File SAVES, formato compatto del piano"),
        *([R(L["mod_cheats"], GFXD - 1, "cheats.asm: menu dei trucchi", "code", "Solo nella build di debug (CHEATS=1): voce cheats del menu RUN/STOP")]
          if "mod_cheats" in L else []),
        R(GFXD, 0x871F, "Margine per il codice", "free", "Fino a $8720 (righe HUD), garantito da .cerror. All'avvio qui c'e' la grafica fissa del PRG: vedi spaccato 1", multi="s1"),
        R(0x8720, 0x87E7, "Schermo HUD (righe 20-24)", "vic", "SCR_H=$8400: il VIC mostra solo le ultime 5 righe (split raster)", multi="s1"),
        R(0x87E8, 0x87F7, "Libera", "free", "", S, multi="s1"),
        R(0x87F8, 0x87FF, "Puntatori sprite (fascia HUD)", "vic", "", multi="s1"),
        R(0x8800, 0x89FF, "Sprite della barra, set A", "vic", "8 sprite (doppio buffer con $B000)", multi="s1"),
        R(0x8A00, 0x8A3F, "Sprite segnaposto minimappa", "vic", "", multi="s1"),
        R(0x8A40, 0x8A40 + SMAX - 1, "Brano del luogo (SND_LBUF)", "data", "Il brano del villaggio / piano, letto dal disco (grande quanto il brano piu' lungo, SND_SMAX)", multi="s1"),
        R(0x8A40 + SMAX, 0x8BFF, "Libera", "free", "Resto degli slot sprite 41-47", S, multi="s1"),
        R(0x8C00, 0x8E7F, "Sprite forti + boss finale", "vic", "640 B dal file del tema (10 sprite)", multi="s1"),
        R(0x8E80, 0x8E80 + FMAX - 1, "Motivetto di combattimento (SND_FBUF)", "data", "Grande quanto il motivetto piu' lungo (SND_FMAX)"),
        R(0x8E80 + FMAX, NMA - 1, "Libera", "free", "Resto degli slot sprite 58-63", S),
        R(NMA, 0x8FFF, "Colori e nomi dei mostri del capitolo (NM_AT)", "data", "(15/11) Blocco info del file del tema (%d B), copiato da gfx_install: 9 colori, 9 indirizzi, 9 nomi" % NMI),
        R(0x9000, 0x9BFF, "Variabili del gioco", "var", "Il VIC qui vede la ROM dei caratteri, non la RAM: solo variabili. Dettaglio nella sezione dedicata", multi="vars"),
        R(0x9C00, CODE2E - 1, "CODE2: disco", "code", "io_begin, load_gfx, menu_run, load_menu, ld_open, load_raw, save_level"),
        R(CODE2E, 0x9FFF, "Coda di CODE2", "free", "Riservata al codice residente", V),
    ]),
    ("Banco VIC 2: $A000-$BFFF (sotto la ROM del BASIC, esclusa)", [
        R(0xA000, 0xA2FF, "Sprite 0-11: eroe e fendenti", "vic", "", multi="s2"),
        R(0xA300, 0xA4FF, "Sprite 12-19: mostri del tema", "vic", "Dal file GFXn (nel tema 8 slot 12-13: stella e cerchio)", multi="s2"),
        R(0xA500, 0xA5FF, "Slot sprite 20-23", "free", "", S, multi="s2"),
        R(0xA600, 0xA6BF, "Sprite 24-26: HUD, segnaposto, anello", "vic", "", multi="s2"),
        R(0xA6C0, 0xA6FF, "Slot sprite 27", "free", "Riceve la coda della copia (byte senza uso)", S, multi="s2"),
        R(0xA700, MZ[2][1] - 1, "Modulo MENU, zona 3 (slot 28-31)", "code", "Negozi: riparazione, tetto dell'oro (11/11)", multi="s2"),
        R(MZ[2][1], 0xA7FF, "Libera (zona 3 del MENU)", "free", "", S, multi="s2"),
        R(0xA800, 0xAFFF, "Charset del gioco", "vic", "4 quarti da $200: tile del luogo (360 B villaggio / 216 B dungeon) + 152 B di caratteri fissi", multi="s2"),
        R(0xB000, 0xB3FF, "Sprite della barra, set B / nomi minimappa", "vic", "Vedi spaccato 2", multi="s2"),
        R(0xB400, 0xB7FF, "Schermo A (gioco) / schermo delle UI", "vic", "", multi="s2"),
        R(0xB800, 0xBBFF, "Font della UI", "vic", "Charset delle schermate (inventario, negozi, menu)", multi="s2"),
        R(0xBC00, 0xBFFF, "Schermo B (gioco)", "vic", "Doppio buffer con lo schermo A", multi="s2"),
    ]),
    ("$C000-$CFFF", [
        R(0xC000, 0xC8FF, "MAP: mappa 48x48", "data", "Nel menu iniziale: modulo LOBBY", multi="s3"),
        R(0xC900, 0xCFFF, "Libera in gioco", "free", "1792 B di RAM normale (arena: modulo a $C900): candidata per l'overlay della sala del trono", V, multi="s3"),
    ]),
    ("$D000-$DFFF: I/O (sotto: 4 KB di RAM)", [
        R(0xD000, 0xD3FF, "VIC-II", "io", "Registri (ripetuti)", multi="s4"),
        R(0xD400, 0xD7FF, "SID", "io", "", multi="s4"),
        R(0xD800, 0xDBFF, "RAM del colore (4 bit)", "io", "", multi="s4"),
        R(0xDC00, 0xDCFF, "CIA 1", "io", "Tastiera, joystick, timer", multi="s4"),
        R(0xDD00, 0xDDFF, "CIA 2", "io", "Banco VIC, bus seriale del 1541", multi="s4"),
        R(0xDE00, 0xDFFF, "I/O 1-2 (espansioni)", "io", "", multi="s4"),
    ]),
    ("$E000-$FFFF: ROM del KERNAL (sotto: 8 KB di RAM)", [
        R(0xE000, 0xFFF9, "ROM del KERNAL", "io", "La RAM sotto e' la cache del gioco: vedi spaccato 5", multi="s5"),
        R(0xFFFA, 0xFFFF, "Vettori NMI / RESET / IRQ", "sys", ""),
    ]),
]

# ------------------------------------------------------------------ spaccati: stesse celle, scenari diversi
SCEN = []


def spaccato(key, title, a, b, note, cols):
    SCEN.append(dict(key=key, title=title, a=a, b=b, note=note, cols=cols))


spaccato("s1", "Spaccato 1 - $%04X-$8FFF: grafica fissa del PRG / schermo HUD e sprite" % GFXD, GFXD, 0x8FFF,
         "Il PRG GAME arriva fino a $9D8F: la sua coda contiene la grafica fissa, che copy_gfx copia a destinazione come prima cosa. Dopo, quei byte sono dato morto e la zona diventa schermo HUD, sprite e margine per il codice.",
         [("Avvio (dopo il caricamento, prima di copy_gfx)", [
             R(GFXD, GFXD + 639, "Caratteri fissi (640 B)", "boot", "-> 4 quarti del charset $A800"),
             R(GFXD + 640, GFXD + 1599, "Sprite base (960 B)", "boot", "-> $A000-$A2FF e $A600"),
             R(GFXD + 1600, GFXE - 1, "Font della UI (1024 B)", "boot", "-> $B800"),
             R(GENI, GENIE - 1, "Generatore dei piani (%d B)" % (GENIE - GENI), "boot", "-> $%04X sotto l'I/O (gen_io.asm)" % GENA),
             R(GENIE, 0x8FFF, "Non ancora scritta", "free"),
         ]), ("In gioco (villaggio, dungeon, UI)", [
             R(GFXD, 0x871F, "Margine per il codice", "free", "Codice futuro: guardia .cerror a $8720"),
             R(0x8720, 0x87E7, "Righe HUD 20-24", "vic"),
             R(0x87E8, 0x87F7, "Libera", "free"),
             R(0x87F8, 0x87FF, "Puntatori sprite", "vic"),
             R(0x8800, 0x89FF, "Barra, set A", "vic"),
             R(0x8A00, 0x8A3F, "Segnaposto minimappa", "vic"),
             R(0x8A40, 0x8A40 + SMAX - 1, "Brano del luogo", "data"),
             R(0x8A40 + SMAX, 0x8BFF, "Libera", "free"),
             R(0x8C00, 0x8E7F, "Sprite forti + boss", "vic", "Dal tema corrente"),
             R(0x8E80, 0x8E80 + FMAX - 1, "Motivetto di combattimento", "data"),
             R(0x8E80 + FMAX, NMA - 1, "Libera", "free"),
             R(NMA, 0x8FFF, "Colori e nomi dei mostri (NM_AT)", "data", "Dal tema corrente"),
         ])])

spaccato("s2", "Spaccato 2 - $A000-$BFFF: banco VIC del gioco", 0xA000, 0xBFFF,
         "All'avvio START (avvio del gioco, caricato dal loader BARBARIAN) gira qui (RAM sotto la ROM del BASIC, esclusa). In gioco e' il banco VIC 2: tutto cio' che il VIC mostra deve stare in $8000-$BFFF (esclusa $9000-$9FFF, dove vede la ROM dei caratteri).",
         [("Avvio: START", [
             R(0xA000, LDE - 1, "Codice di START", "boot", ("Titolo, musica, PRESS SPACE, lettura dei file" if _SL == "start.lst" else "Build di debug: solo la lettura dei file (la release con il titolo e' piu' lunga)")),
             R(LDE, 0xAFFF, "Libera", "free"),
             R(0xB000, 0xB042, "CHRTMP: elenco eroi", "boot", "Stato + ultimo record di SAVES (elenco eroi)"),
             R(0xB043, 0xBFFF, "Libera", "free"),
         ]), ("Gioco: villaggio e dungeon", [
             R(0xA000, 0xA2FF, "Sprite eroe + fendenti", "vic"),
             R(0xA300, 0xA4FF, "Sprite mostri del tema", "vic"),
             R(0xA500, 0xA5FF, "Slot 20-23 liberi", "free"),
             R(0xA600, 0xA6BF, "Sprite 24-26", "vic"),
             R(0xA6C0, 0xA6FF, "Slot 27 libero", "free"),
             R(0xA700, 0xA7FF, "Modulo MENU, zona 3", "code", "Slot 28-31"),
             R(0xA800, 0xAFFF, "Charset del gioco", "vic", "Tile del luogo + caratteri fissi"),
             R(0xB000, 0xB1FF, "Barra, set B", "vic"),
             R(0xB200, 0xB3FF, "(nomi minimappa)", "free", "Usati solo dalla minimappa"),
             R(0xB400, 0xB7FF, "Schermo A", "vic"),
             R(0xB800, 0xBBFF, "Font della UI", "vic"),
             R(0xBC00, 0xBFFF, "Schermo B", "vic"),
         ]), ("Schermate UI (inventario, negozi, baule, menu)", [
             R(0xA000, 0xAFFF, "Sprite e charset del gioco (intatti)", "vic"),
             R(0xB000, 0xB3FF, "Barra (non visibile)", "vic"),
             R(0xB400, 0xB7FF, "Schermo della UI", "vic", "$D018=$DE: schermo $B400, charset $B800"),
             R(0xB800, 0xBBFF, "Font della UI", "vic"),
             R(0xBC00, 0xBFFF, "Schermo B", "vic", "Ridisegnato all'uscita"),
         ]), ("Minimappa del villaggio", [
             R(0xA000, 0xAFFF, "Sprite e charset del gioco", "vic"),
             R(0xB000, 0xB2FF, "Sprite con i nomi delle case", "vic", "Azzerati e scritti da mm_names"),
             R(0xB300, 0xB3FF, "-", "free"),
             R(0xB400, 0xB7FF, "Schermo della minimappa", "vic"),
             R(0xB800, 0xBBFF, "Font della UI", "vic"),
             R(0xBC00, 0xBFFF, "Schermo B", "vic"),
         ])])

spaccato("s3", "Spaccato 3 - $C000-$CFFF", 0xC000, 0xCFFF,
         "Stessi 4 KB, usi che non si sovrappongono mai nel tempo (la build arena e' un programma a parte, solo per i test).",
         [("Avvio: titolo", [
             R(0xC000, MENUE - 1, "Modulo LOBBY (caricato)", "code", "Prima: GAME compresso ZX0 a $%04X-$9FFF, decompresso sul posto in $0400 (tools/build/pack.py)" % ZXAT),
             R(MENUE, 0xCBFF, "Libera", "free"),
             R(0xCC00, 0xCFE7, "Schermo del titolo", "boot", "Colori 01/10 del bitmap multicolor (banco VIC 3)"),
             R(0xCFE8, 0xCFF7, "-", "free"),
             R(0xCFF8, 0xCFFF, "Puntatori sprite PRESS SPACE", "boot"),
         ]), ("Menu e creazione eroe", [
             R(0xC000, MENUE - 1, "Modulo LOBBY", "code", "Menu iniziale: elenco eroi, creazione, scheda (senza musica); quit the game = reset (nessun rientro dal BASIC dall'11/11)"),
             R(MENUE, 0xCFFF, "Libera", "free"),
         ]), ("Villaggio / dungeon", [
             R(0xC000, 0xC8FF, "MAP 48x48", "data", "Villaggio: scompattato dalla cache; dungeon: rigenerato dal seed"),
             R(0xC900, MZ[0][1] - 1, "Modulo MENU, zona 1", "code", "src/menu.asm (locanda, parte dei negozi): caricato entrando nel villaggio se manca (il LOBBY lo copre), poi resta"),
             R(MZ[0][1], 0xCFFF, "Libera (zona 1 del MENU)", "free", V),
         ]), ("Build arena (solo test, tools/vice/arena.py)", [
             R(0xC000, 0xC8FF, "MAP: stanza 44x44", "data"),
             R(0xC900, ARE - 1, "Modulo arena + bot", "code", "src/test/arena.asm"),
             R(ARE, 0xCEFF, "Libera", "free"),
             R(0xCF00, 0xCF35, "Parametri", "var", "Scritti da tools/vice/arena.py"),
             R(0xCF36, 0xCF3F, "-", "free"),
             R(0xCF40, 0xCF66, "Risultati", "var", "RES_LEN 39: con durabilita' e arma a fine serie"),
             R(0xCF67, 0xCF7F, "-", "free"),
             R(0xCF80, 0xCFFF, "Registro: 32 combattimenti", "var"),
         ]), ("Progetto (TODO): sala del trono", [
             R(0xC000, 0xC8FF, "MAP 48x48", "data"),
             R(0xC900, 0xCFFF, "Overlay sala del trono (idea)", "free", "Mai fatto: oggi $C900 ospita il modulo OVLT; un overlay del piano 20 lo sostituirebbe (TODO.md)"),
         ])])

spaccato("s4", "Spaccato 4 - $D000-$DFFF: RAM sotto l'I/O", 0xD000, 0xDFFF,
         "Il processore la legge solo con $01=$34 (I/O escluso) e interrupt spenti; il VIC non la vede in questo banco. Solo dati.",
         [("Avvio: caricamento", [
             R(0xD000, 0xDA52, "Villaggio (GFX0) in attesa", "boot", "$E000 e' occupato dal titolo"),
             R(0xDA53, 0xDCFF, "Libera", "free"),
             R(0xDD00, 0xDE7F, "Sprite P R E S A C", "boot", "Puntatori VIC ($DD00-$C000)/64"),
             R(0xDE80, 0xDFFF, "Libera", "free"),
         ]), ("Dopo SPAZIO, fino al primo menu", [
             R(0xD000, 0xD042, "CHRBUF: elenco eroi", "boot", "Il menu lo legge senza disco"),
             R(0xD043, GENA - 1, "Libera", "free"),
             R(GENA, GENE - 1, "Generatore dei piani", "code", "Copiato da copy_gfx all'avvio del gioco"),
             R(GENE, 0xDFFF, "Libera", "free"),
         ]), ("In gioco, nessun piano in sospeso", [
             R(0xD000, GENA - 1, "Libera (STASH quando serve)", "free"),
             R(GENA, GENE - 1, "Generatore dei piani", "code", "gen_io.asm (%d B)" % (GENE - GENA)),
             R(GENE, GENE + L["CH_LV"] * L["LV_SLOT"] - 1, "Piani del capitolo (slot)", "cache", "5 slot da 93 B (LVRAM, rel.asm): stato dei piani del capitolo, sul disco solo con save game o cambio di capitolo"),
             R(GENE + L["CH_LV"] * L["LV_SLOT"], 0xDFFF, "Libera (%d B)" % (0xE000 - GENE - L["CH_LV"] * L["LV_SLOT"]), "free"),
         ]), ("In gioco, piano lasciato per portale o morte", [
             R(0xD000, 0xD000 + (LVLE - 0x9800) - 1, "STASH: stato del piano", "cache", "Copia di LVLBLK (%d B)" % (LVLE - 0x9800)),
             R(0xD000 + (LVLE - 0x9800), 0xD2FF, "-", "free"),
             R(0xD300, 0xD47F, "STASHM: mostri in gioco", "cache", "Copia di MRT (384 B)"),
             R(GENA, GENE - 1, "Generatore dei piani", "code", "gen_io.asm, copiato all'avvio; gira con $01=$34 (gen_call)"),
             R(GENE, GENE + L["CH_LV"] * L["LV_SLOT"] - 1, "Piani del capitolo (slot)", "cache", "5 slot da 93 B (LVRAM, rel.asm): stato dei piani del capitolo, sul disco solo con save game o cambio di capitolo"),
             R(GENE + L["CH_LV"] * L["LV_SLOT"], 0xDFFF, "Libera (%d B)" % (0xE000 - GENE - L["CH_LV"] * L["LV_SLOT"]), "free", S),
         ])])

spaccato("s5", "Spaccato 5 - $E000-$FFFF: RAM sotto il KERNAL", 0xE000, 0xFFFF,
         "Lettura con $01=$35 e interrupt spenti (o con il codice che la copia). Il VIC la vede solo nel banco 3 (titolo).",
         [("Avvio: titolo", [
             R(0xE000, 0xFF3F, "Bitmap del titolo", "boot", "320x200 multicolor, mostrata riga per riga"),
             R(0xFF40, 0xFFF9, "-", "free"),
             R(0xFFFA, 0xFFFF, "Vettori in RAM", "sys", "NMI di START"),
         ]), ("Villaggio", [
             R(0xE000, 0xE59F, "Tile del villaggio", "cache", "4 x 360 B"),
             R(0xE5A0, TOWNE - 1, "Mappa del villaggio (RLE)", "cache"),
             R(TOWNE, 0xECFF, "Libera", "free"),
             R(0xED00, 0xF4DF, "Coda del tema dell'ultimo dungeon", "cache", "Dato morto (gia' installato); la testa (blocco info, da $%04X) l'ha coperta il villaggio" % DUNA),
             R(MZ[1][0], MZ[1][1] - 1, "Modulo MENU, zona 2", "code", "Locanda (scelta dell'equipaggiamento) e negozi, eseguiti con $01=$35. Dall'11/11 il precaricamento del tema scrive direttamente nella cache del tema ($ED00)"),
             R(MZ[1][1], FINAT - 1, "Libera (zona 2 del MENU)", "free"),
             R(FINAT, FINE - 1, "Mappa della sala del trono (FMAP, RLE)", "cache", "Letta una volta (fin_load), poi scompattata in MAP a ogni ingresso nel piano 20"),
             R(FINE, 0xFFF9, "Libera", "free"),
             R(0xFFFA, 0xFFFF, "Vettori", "sys"),
         ]), ("Dungeon (piani 1-9)", [
             R(0xE000, 0xE59F, "Tile del villaggio", "cache", "Dato morto: il villaggio si rilegge a ogni ingresso (11/11)"),
             R(0xE5A0, TOWNE - 1, "Mappa del villaggio (RLE)", "cache"),
             R(TOWNE, DUNA - 1, "Libera", "free"),
             R(DUNA, DUNA + 863, "Tema: tile (4 x 216)", "cache", "(15/11) Il file comincia GFX_INFO byte prima di $ED00, nella coda del villaggio (che si rilegge a ogni ingresso)"),
             R(DUNA + 864, DUNA + 1375, "Tema: mostri base", "cache"),
             R(DUNA + 1376, DUNA + 2015, "Tema: forti + boss", "cache"),
             R(DUNA + 2016, 0xF4DF, "Tema: blocco info (colori e nomi)", "cache", "Copiato a NM_AT da gfx_install"),
             R(MZ[1][0], MZ[1][1] - 1, "Modulo MENU, zona 2", "code", "Resta dal villaggio (il precaricamento del tema del piano successivo scrive nella cache del tema, $ED00)"),
             R(MZ[1][1], FINAT - 1, "Libera (zona 2 del MENU)", "free"),
             R(FINAT, FINE - 1, "Mappa della sala del trono (FMAP, RLE)", "cache", "Se gia' letta"),
             R(FINE, 0xFFF9, "Libera", "free"),
             R(0xFFFA, 0xFFFF, "Vettori", "sys"),
         ]), ("Piano 20 (sala del trono)", [
             R(0xE000, TOWNE - 1, "Villaggio (tile + mappa)", "cache"),
             R(TOWNE, DUNA - 1, "Libera", "free"),
             R(DUNA, 0xF4DF, "Tema 8", "cache", "Pentacolo e leva negli slot dei tile; mostri del capitolo 4"),
             R(MZ[1][0], MZ[1][1] - 1, "Modulo MENU, zona 2", "code", "Resta dal villaggio"),
             R(MZ[1][1], FINAT - 1, "Libera (zona 2 del MENU)", "free"),
             R(FINAT, FINE - 1, "Mappa della sala del trono (FMAP, RLE)", "cache", "Letta al primo ingresso nel piano"),
             R(FINE, 0xFFF9, "Libera", "free"),
             R(0xFFFA, 0xFFFF, "Vettori", "sys"),
         ])])

# ------------------------------------------------------------------ variabili $9000-$9BFF
VARS = [
    R(0x9000, 0x90F0, "Generatore e stato del piano", "var", "cur_level, stanze rx/ry/rw/rh/rcx..."),
    R(0x90F1, 0x90FF, "Libera", "free", "", S),
    R(0x9100, 0x91A7, "Variabili di gioco", "var", "bottino e bauli, mostri in elaborazione, aree d'attacco, effetti, suoni, generatore, disco"),
    R(0x91A8, 0x91FB, "Barra ed etichette", "var"),
    R(0x91FC, 0x91FF, "Libera", "free", "", S),
    R(0x9200, 0x922F, "solidtab", "var", "tile solidi del luogo (copia di solid_dun, o dei tile solidi del villaggio dal file TWNc)"),
    R(0x9230, 0x923F, "Libera", "free", "", S),
    R(0x9240, 0x9317, "Percorsi dei mostri e drop", "var", "Coda BFS, tile dei mostri vivi, oggetti in attesa"),
    R(0x9318, L["cb_end"] - 1, "Combattimento (combat.asm)", "var", "vita massima 16 bit, FOR/DES/COS, ATT, CA, dadi, ricariche delle abilita', timer Rage/Frenzy/pozioni, statistiche dei mostri del piano (ft_*)"),
    R(L["cb_end"], 0x939F, "Libera", "free", "", S),
    R(0x93A0, L["mus_end"] - 1, "Musica: richieste, buffer, brani gia' letti", "var"),
    R(L["mus_end"], 0x93AF, "Libera", "free", "", S),
    R(0x93B0, L["tp_end"] - 1, "set_tile, mostri che si muovono, scorrimento", "var", "tp_*, sel_*, sp_* (08/11 sera: da $95D4, per fare posto al baule di casa nel blocco dell'eroe)"),
    R(L["tp_end"], 0x93DF, "Libera", "free", "", S),
    R(0x93E0, L["nav_end"] - 1, "Menu, ordinamento, casa", "var", "ui_nav (ui_cur, ui_n, ui_lc, tb_*), colore delle cornici (ui_bc), sort4 (s4_*), casa (hg_x, hg_k, ovl2_ok)"),
    R(L["nav_end"], 0x93FF, "Libera", "free", "", S),
    R(0x9400, 0x9415, "Negozio", "var"),
    R(0x9416, 0x941F, "Libera", "free", "", S),
    R(0x9420, 0x942A, "Movimento", "var"),
    R(0x942B, 0x943F, "Libera", "free", "", S),
    R(0x9440, 0x944F, "Riquadri della UI", "var"),
    R(0x9450, 0x945F, "Disco", "var", "cmdbuf, cur_slot, ovl_cur"),
    R(0x9460, L["st_col"], "Stato della UI", "var", "cursore, oggetto in transito, durabilita' mostrata, baule di casa"),
    R(L["st_col"] + 1, 0x947F, "Libera", "free", "", S),
    R(0x9480, 0x94F6, "Elenco eroi", "var", "slot_valid, nomi (passo 16)"),
    R(0x94F7, 0x94FF, "Libera", "free", "", S),
    R(0x9500, CHRE - 1, "CHRBLK: eroe e baule di casa (salvato)", "var", "Dettaglio sotto"),
    R(CHRE, L["mfar"] - 1, "Libera", "free", "", S),
    R(L["mfar"], L["mfar_end"] - 1, "Mostri lontani (mfar)", "var"),
    R(0x9600, 0x977F, "Mostri in gioco", "var", "Posizione fine, vita, ricarica, stordimento... 12 x 32"),
    R(0x9780, 0x97E7, "HUD e IRQ", "var"),
    R(0x97E8, 0x97FF, "Libera", "free", "", S),
    R(0x9800, LVLE - 1, "LVLBLK: stato del piano", "var", "Dettaglio sotto (%d B)" % (LVLE - 0x9800)),
    R(LVLE, 0x9A5F, "Libera", "free", "", S),
    R(0x9A60, 0x9A9F, "sort4: ordine e appoggio", "var", "S4_ORD, S4_BUF (32 B ciascuno): solo durante l'ordinamento di zaino e baule di casa"),
    R(0x9AA0, 0x9AFF, "Libera", "free", "", S),
    R(0x9B00, RELE - 1, "Variabili REL", "var", "Record corrente, file aperto, elenco eroi (hdrbuf)"),
    R(RELE, L["SP_VARS"] - 1, "Libera", "free", "", S),
    R(L["SP_VARS"], L["SP_VARS"] + L["SP_VSIZE"] - 1, "Player SID (sid_player.inc)", "var", "Strumenti del brano, stato delle 3 voci, posizione salvata (ripresa dopo il combattimento)"),
    R(L["SP_VARS"] + L["SP_VSIZE"], 0x9BFF, "Libera", "free", "", V),
]
LVL = [("lb_lvl, lb_cnt, boss, nome boss, baule del boss", 6), ("mtype: tipo dei 32 mostri", 32), ("malive", 32), ("mix, miy: casella", 64),
       ("cx_x, cx_y, ch_t: 15 bauli", 45),
       ("ch_i, ch_b: contenuto bauli (15 x 4 x 2)", 120), ("EXPL: mappa esplorata (1 bit per tile)", 288)]
CHR = [("versione, seed, luogo, livello, XP, oro, vita", 12), ("piani visitati, ritorno col portale", 9),
       ("cintura (4), abilita', uccisioni, boss, leva, piano massimo", 10), ("nome (12)", 12),
       ("posizione", 4), ("zaino (8) + equipaggiamento (4)", 12), ("seed testuale, versione generatore", 7),
       ("bonus zaino ed equip. (8+4), chiavi", 13), ("durabilita' attuale (8+4)", 12), ("durabilita' massima (8+4)", 12),
       ("partita e minuti, morti, oro nel baule di casa", 7),
       ("baule di casa: id, bonus, durabilita', massimo (4 x 24, dall'08/11 sera)", 96)]

# ------------------------------------------------------------------ HTML
def h(x):
    return html.escape(str(x))


def fmt(a):
    return "$%04X" % a


def size(r):
    return r["b"] - r["a"] + 1


def bsz(n):
    return "%d B" % n if n < 1024 else ("%.1f KB" % (n / 1024)).replace(".0 KB", " KB")


def cell_h(n):
    return max(30, min(170, int(9 * n ** 0.42)))


def cell(r, extra=""):
    n = size(r)
    lab, var = CAT[r["cat"]]
    badge = ""
    if r["ver"]:
        badge = '<span class="badge %s">%s</span>' % ("ok" if r["ver"] == V else "st", h(r["ver"]))
    if r.get("multi") and r["multi"].startswith("s"):
        badge += '<a class="badge mu" href="#%s">multiuso: spaccato %s</a>' % (r["multi"], r["multi"][1:])
    if r.get("multi") == "vars":
        badge += '<a class="badge mu" href="#vars">dettaglio</a>'
    return ('<div class="cell" style="--h:%dpx;--c:var(%s)" title="%s-%s  %s">'
            '<div class="adr">%s<br><span>%s</span></div>'
            '<div class="body"><div class="nm">%s <em>%s</em></div><div class="ds">%s</div>%s</div></div>'
            % (cell_h(n), var, fmt(r["a"]), fmt(r["b"]), h(r["name"]), fmt(r["a"]), fmt(r["b"]), h(r["name"]), bsz(n),
               h(r["desc"]), badge))


def column(rows, a, b, px):
    out = []
    for r in rows:
        top = (r["a"] - a) / (b - a + 1) * px
        hh = size(r) / (b - a + 1) * px
        lab, var = CAT[r["cat"]]
        small = hh < 30
        tiny = hh < 15
        txt = "" if tiny else ('<b>%s</b> <i>%s-%s · %s</i>%s' % (h(r["name"]), fmt(r["a"]), fmt(r["b"]), bsz(size(r)),
                                                                  "" if small or not r["desc"] else "<br>" + h(r["desc"])))
        out.append('<div class="sc %s" style="top:%.1fpx;height:%.1fpx;--c:var(%s)" title="%s-%s  %s (%s)%s">%s</div>'
                   % ("sm" if small else "", top, max(hh, 2), var, fmt(r["a"]), fmt(r["b"]), h(r["name"]), bsz(size(r)),
                      (" - " + h(r["desc"])) if r["desc"] else "", txt))
    return "".join(out)


def check(rows, a, b, what):
    p = a
    for r in rows:
        assert r["a"] == p, "%s: buco o sovrapposizione a %s (%s)" % (what, fmt(p), r["name"])
        p = r["b"] + 1
    assert p == b + 1, "%s: fine %s invece di %s" % (what, fmt(p), fmt(b + 1))


# ------------------------------------------------------------------ memoria libera utilizzabile
# (a, b, tipo, zona, come si usa). tipo: freec = RAM normale, codice e dati senza vincoli; freeio = codice solo se gira
# con $01=$34 e interrupt spenti (niente VIC/SID/CIA/colori/KERNAL/disco), oppure dati; freed = solo dati
ZONES = [
    (GFXD, 0x871F, "freec", "Margine del programma principale", "Codice e dati del gioco: basta aggiungere sorgenti a main.asm. La build ferma (.cerror) se si supera $8720 (righe HUD)."),
    (CODE2E, 0x9FFF, "freec", "Coda di CODE2", "Piccolo codice residente (disco, caricamenti), nello stesso blocco di CODE2."),
    (0x0200, 0x0258, "freec", "Pagina 2: buffer del BASIC", "RAM normale ma piccola e sparsa: routine brevissime o dati."),
    (0x02B2, 0x02FF, "freec", "Pagina 2 libera", "Come sopra."),
    (0x0334, 0x03FF, "freec", "Pagina 3: buffer del registratore", "Come sopra (le build di debug usano $03F0-$03F3)."),
    (GENE + L["CH_LV"] * L["LV_SLOT"], 0xDFFF, "freeio", "RAM sotto l'I/O dopo il generatore e gli slot dei piani", "Codice che non tocca VIC, SID, CIA, colori, KERNAL, disco e gira con $01=$34 e interrupt spenti (come gen_io.asm, chiamato da gen_call); oppure dati."),
    (TOWNE, DUNA - 1, "freed", "Coda libera della cache del villaggio", "Dati (cache di grafica o tabelle): si leggono con $01=$35 e interrupt spenti (dal 15/11 fino all'inizio del tema del dungeon, GFX_DUN_AT)."),
    (0xF4E0, 0xF4FF, "freed", "Cache sotto il KERNAL: pezzo piccolo", "Dati."),
    (FINE, 0xFFF9, "freed", "Fondo della cache sotto il KERNAL", "Dati (dopo FMAP)."),
    (0x87E8, 0x87F7, "freed", "Tra schermo HUD e puntatori sprite", "Dati (nel banco VIC, fuori da sprite e schermi)."),
    (0x8A40 + SMAX, 0x8BFF, "freed", "Coda degli slot sprite 41-47", "Dati: slot senza sprite."),
    (0x8E80 + FMAX, NMA - 1, "freed", "Coda degli slot sprite 58-63", "Dati: slot senza sprite (fino al blocco info dei mostri, NM_AT)."),
    (0xA500, 0xA5FF, "freed", "Slot sprite 20-23", "Dati: slot senza sprite."),
    (0xA6C0, 0xA6FF, "freed", "Slot sprite 27", "Dati: slot senza sprite (riceve la coda della copia, byte senza uso)."),
    (L["zp_end"], 0x004F, "freed", "Pagina zero libera", "Variabili veloci (indirizzamento breve)."),
    (0x008D, 0x008F, "freed", "Pagina zero libera", "Variabili veloci (3 B)."),
    (0x00FB, 0x00FE, "freed", "Pagina zero libera", "Variabili veloci (4 B)."),
]


def zone_of(r):
    for z in ZONES:
        if z[0] <= r["a"] and r["b"] <= z[1]:
            return z
    return None


for _, g in MAIN:
    for r in g:
        z = zone_of(r) if r["cat"] == "free" else None
        if z:
            r["cat"] = z[2]
for _s in SCEN:
    for _t, rows in _s["cols"]:
        for r in rows:
            z = zone_of(r) if r["cat"] == "free" else None
            if z:
                r["cat"] = z[2]
for r in VARS:
    if r["cat"] == "free":
        r["cat"] = "freed"

flat = [r for _, g in MAIN for r in g]
check(flat, 0, 0xFFFF, "mappa principale")
check(VARS, 0x9000, 0x9BFF, "variabili")
for s in SCEN:
    for t, rows in s["cols"]:
        check(rows, s["a"], s["b"], s["title"] + " / " + t)

free_n = {}
for r in flat:
    if r["cat"] in FREE:
        free_n[r["ver"] or S] = free_n.get(r["ver"] or S, 0) + size(r)
vfree = sum(size(r) for r in VARS if r["cat"] in FREE)

P = []
P.append("""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mappa della RAM</title><style>
:root{--bg:#f6f5f1;--fg:#1d1d1b;--mut:#6b6a64;--line:#d9d6cc;--card:#fff;
--c-sys:#8e6cc9;--c-io:#8a8a86;--c-code:#d4622a;--c-data:#d9a23a;--c-vic:#3b7fc4;--c-var:#2f9e8f;--c-cache:#c2477e;--c-boot:#7a9a3a;--c-free:#cfe6c0;--c-freec:#1fae4b;--c-freeio:#4fc3c0;--c-freed:#e6d34a}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--fg:#e9e7e1;--mut:#9b998f;--line:#34352f;--card:#202124;--c-free:#3c5a35;--c-io:#5d5d5a;--c-freec:#2fbf5b;--c-freeio:#3aa6a3;--c-freed:#b8a62e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 80px}h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:42px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:14px;margin:22px 0 6px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}p{margin:6px 0;max-width:80ch}.mut{color:var(--mut)}
code,.adr,i{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:14px 0}.legend span{display:inline-flex;align-items:center;gap:6px;font-size:13px}
.legend b{width:14px;height:14px;border-radius:3px;background:var(--c);display:inline-block;border:1px solid rgba(0,0,0,.15)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin:14px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}.stat b{display:block;font-size:20px}.stat span{color:var(--mut);font-size:12px}
.map{border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--card)}
.cell{display:flex;min-height:var(--h);border-top:1px solid var(--line)}.cell:first-child{border-top:0}
.cell .adr{flex:0 0 92px;padding:6px 8px;font-size:12px;border-right:6px solid var(--c);color:var(--fg)}.cell .adr span{color:var(--mut)}
.cell .body{padding:6px 10px;flex:1;min-width:0;background:linear-gradient(90deg,color-mix(in srgb,var(--c) 14%,transparent),transparent 60%)}
.nm{font-weight:600}.nm em{font-weight:400;color:var(--mut);font-style:normal;font-size:12px;margin-left:6px}.ds{color:var(--mut);font-size:12.5px}
.badge{display:inline-block;margin:3px 6px 0 0;font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);color:var(--mut);text-decoration:none}
.badge.ok{border-color:#3e8e41;color:#3e8e41}.badge.mu{border-color:var(--c-cache);color:var(--c-cache)}
.grp{padding:8px 10px;background:var(--bg);font-weight:600;font-size:12.5px;border-top:1px solid var(--line);letter-spacing:.02em}
.split{display:grid;gap:10px;margin-top:10px;overflow-x:auto;padding-bottom:4px}
.scol h4{margin:0 0 6px;font-size:12.5px;min-height:34px}.stack{position:relative;border:1px solid var(--line);border-radius:6px;background:var(--card);overflow:hidden}
.sc{position:absolute;left:0;right:0;border-top:1px solid var(--line);border-left:6px solid var(--c);padding:3px 6px;font-size:12px;overflow:hidden;
background:color-mix(in srgb,var(--c) 16%,var(--card))}.sc i{color:var(--mut);font-style:normal;font-size:11px}.sc.sm{padding:1px 6px;white-space:nowrap;text-overflow:ellipsis}
.ruler{position:relative;font:11px ui-monospace,Menlo,monospace;color:var(--mut)}.ruler div{position:absolute;right:4px;transform:translateY(-6px)}
table{border-collapse:collapse;width:100%;max-width:720px;margin-top:8px}table.free{max-width:none}.chip{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;border:1px solid rgba(0,0,0,.2)}\n.fbar{position:relative;height:34px;margin:14px 0 26px;background:repeating-linear-gradient(90deg,var(--line) 0,var(--line) 1px,transparent 1px,transparent 6.25%);border:1px solid var(--line);border-radius:6px;background-color:var(--card)}.fbar div{position:absolute;top:2px;bottom:2px;border-radius:2px;min-width:2px}.fbar span{position:absolute;top:36px;font:10px ui-monospace,Menlo,monospace;color:var(--mut)}.l0{left:0}.l1{left:25%}.l2{left:50%}.l3{left:75%}.l4{right:0}td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;font-size:13px}td.n{text-align:right;font-family:ui-monospace,Menlo,monospace;white-space:nowrap}
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px}@media (max-width:760px){.two{grid-template-columns:1fr}.cell .adr{flex-basis:78px}}
</style></head><body><main>""")
P.append("<h1>Barbarian: The Blood Path · mappa della RAM</h1>")
P.append('<p class="mut">Commodore 64, 64 KB. Situazione: build v%s, generata da <code>tools/memory-map/gen_rammap.py</code> sulle etichette di <code>out/work/game.lbl</code> e <code>out/work/lobby.lbl</code>. '
         'Altezza delle celle non lineare (cresce con la dimensione, cosi\' anche le zone piccole restano leggibili); negli spaccati invece l\'altezza e\' proporzionale ai byte.</p>'
         % h(open(os.path.join(ROOT, "out", "work", "version.inc")).read().split('"')[1]))
P.append('<div class="legend">' + "".join('<span><b style="--c:var(%s)"></b>%s</span>' % (v, h(l)) for l, v in CAT.values()) + "</div>")
P.append('<div class="legend"><span><span class="badge ok">%s</span> riempita con un valore noto e rimasta intatta dopo cambi di piano, portali e salvataggi (non sono passati negozi, morte, boss)</span>'
         '<span><span class="badge st">%s</span> nessun riferimento nel codice, non provata in esecuzione</span></div>' % (V, S))
P.append('<div class="stats"><div class="stat"><b>%s</b><span>libera verificata in VICE (mappa principale)</span></div>'
         '<div class="stat"><b>%s</b><span>libera da analisi statica</span></div><div class="stat"><b>%s</b><span>buchi tra le variabili $9000-$9BFF</span></div>'
         '<div class="stat"><b>%s</b><span>libera sotto I/O e KERNAL in gioco (spaccati 4 e 5)</span></div></div>'
         % (bsz(free_n.get(V, 0)), bsz(free_n.get(S, 0)), bsz(vfree), bsz((0xDFFF - 0xD000 + 1 - (LVLE - 0x9800)) + (0xECFF - TOWNE + 1) + (0xFFF9 - 0xFCE0 + 1) - (GENE - GENA) - (FINE - FINAT))))

KIND = {"freec": "codice e dati", "freeio": "codice con I/O spento, o dati", "freed": "solo dati"}
tot = {k: sum(z[1] - z[0] + 1 for z in ZONES if z[2] == k) for k in KIND}
P.append('<h2>0. Memoria libera utilizzabile</h2>'
         '<p>Quanta RAM resta e <b>per cosa</b> si puo\' usare. Il tipo conta: nel C64 il codice non puo\' stare ovunque.</p>')
P.append('<div class="stats">'
         '<div class="stat" style="border-left:6px solid var(--c-freec)"><b>%s</b><span>libera per <strong>codice e dati</strong> senza vincoli (programma principale e CODE2: %s; pagine 2-3: %s, pezzi piccoli)</span></div>'
         '<div class="stat" style="border-left:6px solid var(--c-freeio)"><b>%s</b><span>libera per <strong>codice con I/O spento</strong> (sotto l\'I/O) o dati</span></div>'
         '<div class="stat" style="border-left:6px solid var(--c-freed)"><b>%s</b><span>libera <strong>solo per dati</strong> (cache sotto il KERNAL, slot sprite, pagina zero)</span></div></div>'
         % (bsz(tot["freec"]), bsz(sum(z[1] - z[0] + 1 for z in ZONES[:2])), bsz(sum(z[1] - z[0] + 1 for z in ZONES[2:5])), bsz(tot["freeio"]), bsz(tot["freed"])))
bar = []
for a, b, k, nm, use in ZONES:
    bar.append('<div title="%s-%s %s (%s)" style="left:%.3f%%;width:%.3f%%;background:var(--c-%s)"></div>' % (fmt(a), fmt(b), h(nm), bsz(b - a + 1), a / 65536 * 100, max((b - a + 1) / 65536 * 100, 0.25), k))
P.append('<div class="fbar" aria-label="RAM 0000-FFFF con le zone libere evidenziate">%s<span class="l0">$0000</span><span class="l1">$4000</span><span class="l2">$8000</span><span class="l3">$C000</span><span class="l4">$FFFF</span></div>' % "".join(bar))
P.append('<table class="free"><tr><th>Tipo</th><th>Indirizzi</th><th style="text-align:right">Byte</th><th>Zona</th><th>Come si usa</th></tr>')
for a, b, k, nm, use in sorted(ZONES, key=lambda z: ({"freec": 0, "freeio": 1, "freed": 2}[z[2]], -(z[1] - z[0]))):
    P.append('<tr><td><span class="chip" style="background:var(--c-%s)"></span>%s</td><td class="n">%s-%s</td><td class="n">%d</td><td>%s</td><td>%s</td></tr>'
             % (k, h(KIND[k]), fmt(a), fmt(b), b - a + 1, h(nm), h(use)))
P.append("</table>")
vg = sum(size(r) for r in VARS if r["cat"] in FREE)
P.append('<p class="mut">Non contati: %s di buchi tra le variabili <code>$9000-$9BFF</code> (solo dati, sparsi: sezione 3), la zona del precaricamento <code>$F500-$FCDF</code> '
         '(2016 B, occupata nei dungeon, libera solo nel piano 20), <code>$B200-$B3FF</code> (512 B, nomi della minimappa) e lo STASH <code>$D000-$D47F</code> '
         '(occupato solo con un piano lasciato per portale o morte). Le zone sotto I/O e KERNAL vanno scritte e lette con <code>$01=$34</code> / <code>$35</code> e interrupt spenti.</p>' % bsz(vg))

P.append("<h2>1. Mappa completa (in gioco)</h2><p>Dove una zona cambia uso nel tempo e' segnata <span class='badge mu'>multiuso</span>: il link porta allo spaccato.</p><div class='map'>")
for g, rows in MAIN:
    P.append('<div class="grp">%s</div>' % h(g))
    P.extend(cell(r) for r in rows)
P.append("</div>")

P.append("<h2>2. Spaccati delle zone multiuso</h2><p>Ogni colonna e' lo stesso intervallo di indirizzi in una situazione diversa; le situazioni non si sovrappongono mai nel tempo. Le celle troppo sottili per il testo mostrano i dettagli passandoci sopra col mouse.</p>")
for s in SCEN:
    px = 760
    P.append('<h3 id="%s">%s</h3><p>%s</p>' % (s["key"], h(s["title"]), h(s["note"])))
    n = len(s["cols"])
    P.append('<div class="split" style="grid-template-columns:64px repeat(%d,minmax(190px,1fr))">' % n)
    span = s["b"] - s["a"] + 1
    step = 0x100 if span <= 0x1000 else 0x400
    if span < 0x0800:
        step = 0x80
    ticks = "".join('<div style="top:%.1fpx">%s</div>' % ((t - s["a"]) / span * px, fmt(t))
                    for t in range((s["a"] + step - 1) // step * step, s["b"] + 1, step))
    P.append('<div class="scol"><h4>&nbsp;</h4><div class="ruler" style="height:%dpx">%s</div></div>' % (px, ticks))
    for t, rows in s["cols"]:
        P.append('<div class="scol"><h4>%s</h4><div class="stack" style="height:%dpx">%s</div></div>' % (h(t), px, column(rows, s["a"], s["b"], px)))
    P.append("</div>")

P.append('<h2 id="vars">3. Variabili $9000-$9BFF</h2><p>Il VIC nel banco 2 vede qui la ROM dei caratteri, quindi la zona va bene solo per dati della CPU. '
         'Azzerate da <code>game_start</code>. Dimensioni dei blocchi dalle dichiarazioni nel sorgente: l\'ultima variabile di ogni blocco e\' stimata dalla sua dichiarazione.</p>')
P.append("<div class='map'>" + "".join(cell(r) for r in VARS) + "</div>")


def table(title, rows, total):
    t = '<div><h3>%s</h3><table><tr><th>Contenuto</th><th style="text-align:right">Byte</th></tr>' % h(title)
    t += "".join("<tr><td>%s</td><td class='n'>%d</td></tr>" % (h(a), b) for a, b in rows)
    t += "<tr><th>Totale</th><th style='text-align:right'>%d</th></tr></table></div>" % total
    return t


P.append('<div class="two">' + table("LVLBLK $9800-%s: stato del piano" % fmt(LVLE - 1), LVL, LVLE - 0x9800)
         + table("CHRBLK $9500-%s: eroe (record del file SAVES)" % fmt(CHRE - 1), CHR, CHRE - 0x9500) + "</div>")
P.append('<p class="mut">LVLBLK nel villaggio e\' vuoto (azzerato); nel dungeon si rigenera dal seed e si sovrappone lo stato salvato in forma compatta (79-90 B su disco, un record). '
         'Con un portale o alla morte viene copiato in STASH ($D000, spaccato 4).</p>')

P.append("<h2>4. Note</h2><ul>"
         "<li>Configurazione in gioco: <code>$01=$36</code>: ROM del BASIC esclusa (sotto c'e' il banco VIC 2), I/O e KERNAL presenti (il disco usa il KERNAL).</li>"
         "<li>Banco VIC 2 ($8000-$BFFF): schermi, charset e sprite devono stare tutti qui. $9000-$9FFF il VIC la vede come ROM dei caratteri, per questo ci sono variabili e codice.</li>"
         "<li>RAM sotto I/O e KERNAL: solo dati, letti con interrupt spenti; per eseguire codice da li' bisognerebbe escludere il KERNAL ($01=$35) per tutto il tempo.</li>"
         "<li>Correzione trovata preparando questa mappa (05/11): <code>clear_lvlblk</code> azzerava 4 pagine fino a $9BFF, cancellando le variabili REL a $9B00; ora 3 pagine.</li>"
         "<li>Limiti: le zone 'analisi statica' non hanno riferimenti diretti nel codice, ma una scrittura tramite puntatore non si vede da li'.</li></ul>")
P.append("</main></body></html>")
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
open(OUT, "w").write("\n".join(P))
print("scritto", OUT)
