# Flussi del codice

Copyright © 2026 - Simone Caporale

Come **gira** il codice (stato dell'11/11, v1.223): sequenze, stati e flussi di ogni parte del gioco, con i nomi delle
routine come stanno nei sorgenti. La struttura statica (programmi, moduli, memoria, regole) è in
[Architettura](architettura.md); le regole di gioco nelle pagine dedicate ([Combattimento](combattimento.md),
[Mostri](mostri.md), [Bottino](bottino.md), [Oggetti](oggetti.md)).

Indice: [1 Avvio](#1-avvio-dal-disco-al-gioco) · [2 Partita](#2-inizio-di-una-partita-game_start-e-lobby) ·
[3 Ciclo](#3-ciclo-principale-un-fotogramma) · [4 Interrupt](#4-interrupt-raster) · [5 Input](#5-input-e-tasti) ·
[6 Cambio di luogo](#6-cambio-di-luogo) · [7 Generazione](#7-generazione-di-un-piano) ·
[8 Precaricamento (tolto)](#8-precaricamento-del-tema-tolto) · [9 Disco](#9-lettura-dal-disco) · [10 Salvataggi](#10-salvataggi) ·
[11 Combattimento](#11-attacco-del-pg) · [12 Mostri](#12-mostri-ia-a-ogni-fotogramma) ·
[13 Morte e portale](#13-morte-portale-scale) · [14 Schermate](#14-schermate-motore-dei-menu) ·
[15 Menu del villaggio](#15-menu-del-villaggio-modulo-menu) · [16 Musica](#16-musica-ed-effetti) ·
[17 Sala del trono](#17-sala-del-trono-e-vittoria)

## 1. Avvio: dal disco al gioco

Sorgenti: `src/barbarian.asm`, `src/common/tramp.inc`, `src/common/boot.asm`, `src/game.asm` (`start`). Dettagli in
[Avvio e storia](intro.md).

```mermaid
sequenceDiagram
    autonumber
    participant U as Utente
    participant B as BARBARIAN ($0801)
    participant T as trampoline ($0334)
    participant S as START ($0801 / $A000)
    participant D as 1541
    participant G as GAME ($0400)
    U->>B: LOAD"BARBARIAN",8 + RUN
    alt senza POKE
        B->>U: menu: legend / manual / walk the blood path
        U->>B: walk the blood path
    else POKE 1020,1 prima del RUN (sviluppo)
        Note over B: nessun menu
    end
    B->>T: copia il trampoline, nome "start"
    T->>D: IOINIT, RESTOR, LOAD "START"
    T->>S: jmp $080D
    Note over S: POKE 1021 -> gm_poke, krill_install (KERNAL), residente -> $0200
    S->>D: loadraw GAME compresso (ZX0) a GAME_ZX_AT
    Note over S: zx0_unpack sul posto in $0400 (attesa e musica)
    S->>D: loadraw LOBBY -> $C000 (LDFLAGS $8E = 1)
    S->>D: loadraw hl: elenco eroi -> CHRTMP, poi in RAM sotto l'I/O (CHRPRE $8F = 1)
    S->>G: sei, jmp $0400 (GAME_ENTRY)
    Note over G: start: copy_gfx (coda del PRG -> $8000-$9FFF,<br/>generatore -> $D080), CIA spente, irq_init,<br/>NMI su nmi_stub, banco VIC 2, init_vic
    G->>G: game_start
```

## 2. Inizio di una partita: `game_start` e LOBBY

Sorgenti: `src/game/levels.asm` (`game_start`), `src/game/disk.asm` (`menu_run`, `load_menu`), `src/lobby.asm`.

```mermaid
flowchart TD
    GS["game_start: azzera $9000-$9BFF"] --> MR["menu_run"]
    MR --> LF{"LDFLAGS ($8E):<br/>LOBBY gia' a $C000?"}
    LF -->|"si' (prima volta)"| LJ["jmp LOBBY_AT"]
    LF -->|no| LM["load_menu: file lobby -> $C000<br/>ovl_cur = 0 (MENU non piu' valido)"] --> LJ
    LJ --> LB["LOBBY: elenco eroi, scheda,<br/>nuovo barbaro (nome, seed)"]
    LB -->|"A = 1 nuovo"| NC["new_character<br/>cur_level = 0"]
    LB -->|"A = 0 continua"| CG["c_game + 1 (ripopola i piani)<br/>cur_level = c_loc"]
    LB -->|"back to main menu"| BM["BARBARIAN: menu iniziale<br/>(Krill disinstallato, ricarica con il KERNAL)"]
    NC --> LL1["load_location (villaggio)"] --> PP["place_player (ingresso sud)"]
    PP --> SV["save_char + elenco eroi<br/>(rel_hold: una sola apertura)"]
    CG --> LL2["load_location (luogo salvato)"] --> POS["posizione salvata c_px, c_py"]
    SV --> GO
    POS --> GO["tod_start, recalc_stats, ui_exit"]
    GO --> ML["main_loop"]
```

Dal gioco si torna a `game_start` dal menu di gioco (*quit*: dissolvenza della musica, poi di nuovo LOBBY). Musica (15/11; 16/11: dopo aver disegnato l'elenco, `mp_done`; `START` non suona): `ui_menu` avvia Demon's Eye (`mus_place` con `SND_MENU`), l'uscita verso il gioco (`lb_leave`) la dissolve prima di `music_town` ([Musica](musica.md)).

## 3. Ciclo principale: un fotogramma

Sorgente: `src/game.asm` (`main_loop`). Il ciclo è agganciato al vblank: dura al massimo un fotogramma PAL (19 656 cicli);
se sfora si perde un fotogramma ([Prestazioni](prestazioni.md)).

```mermaid
flowchart TD
    W["wait_vblank<br/>(riga 252: bordo inferiore)"] --> AF["apply_frame<br/>scambio schermo A/B, colori, sprite preparati"]
    AF --> FR["frame + 1"] --> RI["read_input<br/>joystick porta 2 + matrice della tastiera:<br/>joy, joynew, keynew[8]"]
    RI --> HK["handle_keys<br/>abilita', Rage/Frenzy, pozioni, pergamena,<br/>inventario, mappa, menu di gioco"]
    HK --> UP["update_player<br/>Frenzy (fz_move), movimento con collisioni, direzione"]
    UP --> UA["update_attack<br/>tick_timers; Fire = abilita' scelta"]
    UA --> UM["update_monsters<br/>IA, i 4 piu' vicini si muovono, attacchi"]
    UM --> DT["drops_tick<br/>a fine combattimento un baule in coda"]
    DT --> UW["update_world<br/>orologio, boss finale, tile sotto il PG,<br/>esplorazione, Fire su scale/porte/bauli, morte"]
    UW --> UC["update_camera<br/>scorrimento a passi di tile"]
    UC --> UB["update_bar<br/>barra in alto: luogo o bersaglio"]
    UB --> NT["npc_tick<br/>villaggio: passo dei vaganti"]
    NT --> MR["maybe_redraw<br/>ridisegno del buffer nascosto"]
    MR --> BS["build_sprites<br/>PG, mostri visibili (multiplex), effetti"]
    BS --> W
```

(19/11) `update_bar` e `npc_tick` vengono **dopo** `update_camera`: con `redraw_due` (C=1 se in questo fotogramma
`maybe_redraw` cambia cella o ridisegna tutto) il lavoro che può aspettare un fotogramma salta: il passo degli NPC, il
ricalcolo dell'etichetta del luogo (`loc_check`), il pezzo del testo della barra (`bt_step`); e nel fotogramma di un
ridisegno completo (`rd_sync`) gli NPC tengono gli sprite del fotogramma prima (`npc_draw`). Vicino ai vaganti del villaggio
il ridisegno più questi lavori sforava il fotogramma (persi 3-4% camminando fra gli NPC, test `PERF-24`).

Le schermate (inventario, mappa, menu, negozi...) si aprono **dentro** uno di questi passi (`handle_keys`, `act_tick`)
e girano il loro ciclo finché non si chiudono ([14](#14-schermate-motore-dei-menu)); poi il ciclo principale riprende.

## 4. Interrupt raster

Sorgente: `src/game/hud.asm` (`irq_h`), `src/game/bar.asm`. Un solo IRQ raster che cambia riga a ogni fase
(`irq_ph`); CIA spente. Nelle schermate l'IRQ è spento (`irq_off`).

```mermaid
stateDiagram-v2
    direction LR
    [*] --> P0: irq_on (riga IRQ_L1 = 209)
    P0: fase 0, riga 209<br/>schermo HUD $8400, 24 righe
    P1: fase 1, riga 217<br/>multicolor, 38 colonne, sfondo nero
    P2: fase 2, riga 250 (fine HUD)<br/>registri del campo di gioco<br/>dall'ultimo apply_frame
    P3: fase 3, riga IRQ_BAR = 76<br/>(solo con la barra in alto)
    P0 --> P1
    P1 --> P2
    P2 --> P0: senza barra:<br/>spr_copy + sfx_update
    P2 --> P3: con la barra:<br/>bar_regs + sfx_update
    P3 --> P0: spr_copy
```

`sfx_update` (effetti e musica) gira una volta per fotogramma nella fase 2 anche se il ciclo principale sfora.
`spr_copy` copia le ombre degli sprite preparate da `build_sprites` (pubblicate tutte insieme, mai a metà).

## 5. Input e tasti

Sorgenti: `src/game.asm` (`read_input`), `src/game/game.asm` (`handle_keys`, `act_tick`). Movimento **solo WASD o
joystick** (regola di `CLAUDE.md`).

```mermaid
flowchart LR
    RI["read_input"] --> J["joy / joynew<br/>(porta 2; W A S D = direzioni)"]
    RI --> K["keynew[8]<br/>tasti appena premuti"]
    K --> HK["handle_keys"]
    HK -->|"H J K L"| SK["sel_skill: abilita' scelta<br/>(slash, whirlwind, battle cry, smash)"]
    HK -->|"U / O"| BF["buff_act: Rage / Frenzy"]
    HK -->|"1-4"| PO["use_potion (posto della cintura)"]
    HK -->|"5"| SC["use_scroll (portale)"]
    HK -->|"I"| INV["ui_inventory"]
    HK -->|"M"| MAP["ui_minimap"]
    HK -->|"RUN/STOP"| GM["ui_gamemenu: resume, save, quit"]
    J --> UP["update_player: movimento"]
    J -->|Fire| UA["update_attack: abilita'"]
    J -->|"Fire su scale, porte, bauli"| ACT["act_tick: tile_trigger"]
```

## 6. Cambio di luogo

Sorgente: `src/game/levels.asm`. Ogni passaggio (scale, portale, morte, nuova partita) passa da `change_level`
(A = piano nuovo, X = `spawn_mode`: 0 scale su, 1 scale giù, 2 portale, 3 morte, 4 ingresso sud del villaggio).

```mermaid
flowchart TD
    CL["change_level"] --> FD["snd_fade, irq_off, schermo nero,<br/>music_fadeout, snd_mute"]
    FD --> WH{"luogo lasciato"}
    WH -->|villaggio| NS
    WH -->|piano| SL["save_level: stato compatto nel suo slot in RAM (LVRAM)"]
    SL --> PM{"portale o morte?"}
    PM -->|"si'"| ST["st_out (GEN_STOUT): boss, 5 mostri caldi,<br/>10 bauli lasciati in STASH ($D000), pend_lvl = piano"]
    PM -->|no| CH{"piano nuovo di un altro capitolo?"}
    ST --> CH
    CH -->|"si'"| CS["chap_save: eroe + slot sul disco (sv_all), pend_lvl = 0"]
    CH -->|no| NS["cur_level = piano nuovo, c_maxd"]
    CS --> NS
    NS --> LL["load_location"]
    LL --> PP["place_player (spawn_mode)"]
    PP --> UE["ui_exit: palette, camera, ridisegno,<br/>HUD, sprite, irq_on"]
```

```mermaid
flowchart TD
    LL["load_location"] --> EG["enter_gfx"]
    EG --> V{"cur_level"}
    V -->|"0 villaggio"| LG0["load_gfx 0 (GFX0 -> $E000)"] --> GI0
    GI0["gfx_install 0: tile + mappa RLE -> MAP"] --> MN
    MN["ovl_cur = 0, ovl_town: il modulo MENU<br/>si rilegge a ogni ingresso (sezione 15),<br/>appoggio da $E000 (18/11)"]
    V -->|"1..20 dungeon"| LGN["load_gfx n (GFXn -> GFX_DUN_AT $EC6D),<br/>sempre dal disco"]
    LGN --> GI1["gfx_install 1: tile, sprite dei mostri del capitolo,<br/>varianti forti e boss, colori e nomi -> NM_AT"]
    MN --> PAL["palette, tabella dei tile solidi"]
    GI1 --> PAL
    PAL --> W2{"villaggio?"}
    W2 -->|si'| TP["town_post (portale), clear_lvlblk, music_town"]
    W2 -->|no| DG["music_dungeon, floor_types, gen_dungeon (sezione 7)"]
    DG --> CE["chap_ensure: se il capitolo cambia,<br/>slot del capitolo letti dal file dell'eroe"]
    CE --> CLR["clear_lvlblk, spawn_monsters,<br/>place_chests / fin_chests, place_boss"]
    CLR --> VB{"piano visitato<br/>(c_vis)?"}
    VB -->|si'| LDL["load_level: differenze dallo slot in RAM"] --> IR
    VB -->|no| IR["init_monsters_rt"]
    IR --> PE{"pend_lvl = piano?<br/>(portale o morte)"}
    PE -->|"si'"| MEM["st_in (GEN_STIN): boss, mostri caldi<br/>e bauli lasciati dalla STASH"] --> FI
    PE -->|no| FI["final_init, apply_chests, place_portal_tile"]
```

## 7. Generazione di un piano

Sorgenti: `src/game/dungeon.asm` (`gen_dungeon`, `gen_call`, `seed_level`), `src/game/gen_io.asm` (sotto l'I/O).
Regole e parametri in [Dungeon](dungeon.md).

```mermaid
sequenceDiagram
    participant L as load_location
    participant D as gen_dungeon (GAME)
    participant F as fin_load (CODE2)
    participant C as gen_call
    participant G as generatore ($D080, $01 = $34)
    L->>D: cur_level
    alt piano 20 (sala del trono)
        D->>F: FMAP: cache $FD00 (dal disco la prima volta)
        F-->>D: MAP = mappa di base (RLE, $01 = $35)
    end
    D->>C: A = GEN_MAIN
    Note over C: php, sei, $01 = $34
    C->>G: gen_dmain
    alt piano 1..19
        G->>G: seed_level (seed + piano), clear_map
        G->>G: gen_rooms, gen_links, carve_rooms
        G->>G: gen_stairs, post_walls
    else piano 20
        G->>G: gen_final (cio' che dipende dalla partita)
    end
    G-->>C: rts
    Note over C: $01 = $36, plp
    C-->>L: MAP pronta
```

Tutto ciò che sta prima di `init_monsters_rt` è deterministico (seed + piano): stessa mappa, stessi mostri, stessi bauli.

## 8. Precaricamento del tema (tolto)

**Tolto l'11/11 nel ramo `fast-loader`** (richiesta del committente: provare il caricatore veloce senza trucchi di
cache). Il modulo `prefetch.asm` (lettura in sottofondo del tema, `pf_*`) non esiste più (resta `theme.asm` con
`lvl_theme` e `vis_bit`). Con lui sono state tolte le cache `gfx_town`, `gfx_theme` e `fin_ok`, la residenza del modulo
MENU fra un ingresso e l'altro nel villaggio e il salto del brano già nel buffer: ogni ingresso in un luogo rilegge i suoi
file. Cosa reintrodurre dopo le misure con Krill's Loader lo decide il committente ([FastLoader](FastLoader.md)). La storia
(macchina a stati, `pf_use`, `pf_pause`) è in git (commit prima di `fast-loader`).

## 9. Lettura dal disco

Sorgenti: `src/game/disk.asm` (CODE2), `src/game/music.asm` (`snd_io`), `src/game/ui.asm` (`io_screen`). Dall'11/11
tutte le letture passano da **Krill's Loader** ([FastLoader](FastLoader.md)): `load_raw` (destinazione `ptr0`,
`LOAD_TO`) o `load_file` (indirizzo del file).

```mermaid
sequenceDiagram
    participant C as chiamante (load_gfx, fin_load, load_menu, ovl_town, brani)
    participant L as load_raw / load_file
    participant M as musica
    participant K as Krill (residente $0200)
    participant D as 1541 (codice di Krill)
    C->>L: nome (set_name4 / set_name, 0 finale), destinazione ptr0
    L->>M: snd_io: sfumatura e SID zitto
    L->>L: io_begin: titolo + "please wait" (io_screen) se non io_quiet
    L->>K: krill_loadraw (C = 1: LOAD_TO krill_loadaddrlo/hi)
    K->>D: hash del nome, blocchi (IRQ accesi)
    D-->>K: dati 2 bit + ATN
    K-->>C: C = 0 ok / C = 1 errore (A = stato), fine del file in krill_endaddrlo/hi
    opt brani (snd_get) e parti del MENU (ovl_town), dal 15/11
        C->>C: fine = attesa (buffer + lunghezza / fine della zona)? altrimenti si rilegge (3 letture al massimo)
    end
```

(15/11, ex TODO A2) Krill non segnala una lettura di lunghezza sbagliata: dove il gioco conosce la fine esatta del file la controlla
(`snd_get`: buffer + `snd_llo/hi`; `ovl_town`: `ml_end`) e rilegge; dopo 3 letture sbagliate il brano manca (`snd_cur` = 0,
niente musica) o `ovl_town` esce con C = 1. Causa e correzione del difetto che lo rendeva possibile: [FastLoader](FastLoader.md) 4.1.

Velocità: il modulo MENU (3,3 KB in 3 file) 2,3 s, un tema (2 KB) ~1 s (VICE, 1541 emulata; misure in
[FastLoader](FastLoader.md)). Con il KERNAL erano ~333–390 B/s.

## 10. Salvataggi

Sorgente: `src/game/rel.asm`. Dall'11/11 un file per eroe `save-0N` (eroe + 20 stati dei piani) e l'elenco `hl`,
scritti dal **plugin di save di Krill** (file preallocati, riscritti interi). Formato in [FORMATO_DATI](FORMATO_DATI.md),
quando in [Salvataggi](salvataggi.md).

```mermaid
flowchart LR
    SC["save_char: CHRBLK -> offset 0"]
    SA["sv_all: CHRBLK -> offset 0,<br/>5 slot del capitolo -> posti dei piani"]
    SL["save_level: lv_put -> slot del piano in RAM<br/>(LVRAM, nessun disco)"]
    HW["hdr_write: elenco eroi -> hl (plugin)"]
    subgraph QUANDO["Quando si scrive (11/11 sera)"]
        A1["nuovo eroe (game_start)"] --> SC
        A2["menu di gioco: save game"] --> SA
        A3["piano di un altro capitolo: chap_save"] --> SA
        A5["scale fra piani (change_level)"] --> SL
        A6["creazione / cancellazione eroi"] --> HW
    end
    SC --> GT
    SA --> GT
    GT["sv_get: file dell'eroe -> SV_IMG $E000<br/>(una volta sola con rel_hold)"] --> PT["sv_put (o rel_done): ricarica KSAVE,<br/>$01 = $35, plugin: 9 blocchi"]  --> SE["fine (18/11: il villaggio non si rilegge piu', sv_end tolta)"]
```

```mermaid
flowchart LR
    subgraph LETTURA["Quando si legge"]
        B1["LOBBY: continua"] --> LC["load_char: file -> SV_IMG -> CHRBLK"]
        B2["START / LOBBY: elenco eroi"] --> HR["hdr_read: hl -> hdrbuf"]
        B3["primo piano di un capitolo (chap_ensure)"] --> LV["sv_read: file -> SV_IMG, chap_copy:<br/>5 posti dei piani -> slot LVRAM ($01 = $34)"]
    end
```

## 11. Attacco del PG

Sorgenti: `src/game/game.asm` (`update_attack`, `perform_skill`, `hit_area`, `kill_monster`, `drops_tick`),
`src/game/combat.asm` (`hit_one`, `add_xp`). Regole in [Combattimento](combattimento.md).

```mermaid
sequenceDiagram
    participant UA as update_attack
    participant PS as perform_skill1
    participant HA as hit_area
    participant HO as hit_one (combat.asm)
    participant KM as kill_monster
    participant DQ as coda dei bauli
    UA->>UA: tick_timers (ricariche, Rage, Frenzy, pozioni)
    UA->>PS: Fire, ricarica globale 0, abilita' pronta<br/>(con Frenzy attiva 2 colpi, tranne battle cry)
    PS->>PS: ricarica, effetto sonoro
    PS->>HA: centro: davanti al PG (slash) o sul PG (whirlwind, battle cry, smash)
    loop ogni mostro vivo nell'area
        HA->>HO: tiro per colpire (d20 + ATT contro CA)
        HO->>HO: danni (dadi, critico, blocco), stordimento, usura dell'arma
        alt vita del mostro a 0
            HO->>KM: kill_monster
            KM->>KM: esperienza (add_xp: livelli), boss finale: fin_doors
            KM->>DQ: roll_loot: bottino in coda (baule al posto del mostro)
        end
    end
    Note over DQ: drops_tick: a fine combattimento,<br/>un baule per fotogramma (BFS su casella libera)
```

## 12. Mostri: IA a ogni fotogramma

Sorgente: `src/game/game.asm` (`update_monsters`, `sel_begin`/`sel_commit`, `mon_step`), `src/game/combat.asm`
(`mon_attack`, `hurt_player`). Regole in [Mostri](mostri.md).

```mermaid
flowchart TD
    UM["update_monsters"] --> SB["sel_begin: scelta dei 4 piu' vicini<br/>(con un fotogramma di ritardo)"]
    SB --> LP{"per ogni mostro"}
    LP --> AL{"vivo?"}
    AL -->|no| NX
    AL -->|si'| CAD{"cadenza: fuori schermo 1/16,<br/>addormentato 1/8, sveglio a fotogrammi alterni"}
    CAD -->|non tocca a lui| NX
    CAD -->|tocca a lui| WK["sveglio? (distanza, colpito)"]
    WK --> STN{"stordito?"}
    STN -->|si'| NX
    STN -->|no| CT{"a contatto con il PG?"}
    CT -->|si'| ATK["mon_attack: tiro per colpire, danno<br/>-> hurt_player (vita, lampo, suono)"]
    CT -->|no| SEL{"fra i 4 piu' vicini scelti?"}
    SEL -->|si'| ST["mon_step: passo verso il PG,<br/>senza avvicinamento percorso breve (mon_path), separazione"]
    SEL -->|no| OFF["sel_offer: candidato per il prossimo giro"]
    ATK --> NX
    ST --> NX
    OFF --> NX
    NX["mostro successivo"] --> LP
    LP -->|finiti| SC["sel_commit"]
```

## 13. Morte, portale, scale

Sorgenti: `src/game/game.asm` (`tile_trigger`, `player_die`, `go_down`, `go_up`, `go_portal`), `src/game/levels.asm`.

```mermaid
flowchart TD
    UW["update_world"] --> HP{"vita 0?"}
    HP -->|si'| PD["player_die: tod_tick, morti + 1,<br/>ui_died, meta' dell'oro, vita piena"]
    PD --> CL3["change_level 0, morte (STASH del piano)"]
    UW --> TT["tile_trigger / act_tick (Fire)"]
    TT -->|"scale giu'"| GD["go_down -> change_level n+1"]
    TT -->|"scale su"| GU["go_up -> change_level n-1<br/>(primo piano del capitolo: villaggio)"]
    TT -->|"cripta del villaggio"| GT["go_tdown -> primo piano del capitolo<br/>(c_chap: 1, 6, 11, 16)"]
    TT -->|"uscita aperta (12/11)"| CT["chap_travel: musica sfumata, schermo nero,<br/>c_chap + 1, salvataggio eroe e piani,<br/>change_level 0 (villaggio TWNc, ingresso sud)"]
    TT -->|portale| GP["go_portal: villaggio <-> c_retlvl (STASH)"]
    TT -->|"fontana (ci si passa sopra)"| FT["hp_full"]
    TT -->|baule| CF["chest_fire -> ui_chest"]
    TT -->|"porta della locanda / negozio"| VM["sezione 15"]
    TT -->|"leva (piano 20)"| LV["ui_lever"]
    SCR["pergamena (tasto 5)"] --> PT["portale sul piano: c_portal, c_retlvl"]
    KM["kill_monster: boss del piano del boss<br/>di un capitolo (lv_cboss)"] --> CW["chap_won: c_unl = c + 1"]
```

## 14. Schermate: motore dei menu

Sorgente: `src/game/ui.asm` (`ui_begin`, `ui_nav`, `ui_exit`). Tutte le schermate di testo (inventario, minimappa, baule,
menu di gioco, negozi, locanda...) usano lo stesso schema ([Interfaccia](interfaccia.md)).

```mermaid
sequenceDiagram
    participant G as gioco (handle_keys / act_tick)
    participant S as schermata
    participant U as ui_begin / ui_nav / ui_exit
    participant I as ui_input
    G->>S: apre (jsr)
    S->>U: ui_begin: irq_off, sprite spenti, schermo di testo, font della UI
    S->>S: disegno: titolo (ui_title), riquadri (ui_boxes), etichette
    loop finche' non si chiude
        S->>U: ui_nav
        U->>I: wait_vblank, frame + 1, sfx_update, read_input
        U-->>S: NAV_MOVE (W/S, giro) / NAV_FIRE / NAV_BACK (RUN/STOP) / NAV_NONE
        S->>S: azione o ridisegno della voce
    end
    S->>U: ui_exit
    U->>U: palette, camera, ridisegno, HUD, sprite,<br/>joynew e keynew azzerati, irq_on
    U-->>G: ritorno al ciclo principale
```

## 15. Menu del villaggio: modulo MENU

Sorgenti: `src/game/stash.asm` (`ovl_town`), `src/menu.asm`, `src/menu/`. Il modulo si carica all'ingresso nel
villaggio e poi resta ([Tecnica](tecnica.md#moduli-su-disco)).

```mermaid
sequenceDiagram
    participant V as enter_gfx (villaggio)
    participant O as ovl_town
    participant D as 1541
    participant P as tile_trigger (porta)
    participant M as modulo MENU
    V->>O: ingresso nel villaggio
    alt ovl_cur = 0 (dopo l'avvio o il LOBBY)
        O->>D: load_file menu (un file, 18/11) - finisce a $FD00, sotto il KERNAL<br/>zone 1, 3, 4, 5 dall'appoggio, zona 2 sul posto
        O->>O: fine del file = fine della zona? altrimenti la parte si rilegge (3 volte, poi C = 1, dal 15/11)
        O->>O: sei, $01 = $35, zx0_unpack x 3, $01 = $36
        Note over O: ovl_cur = 1 (2,3 s con Krill, 10,5 s con il KERNAL)
    end
    P->>O: Fire sotto la porta (riprova se mancasse)
    alt locanda
        P->>M: MENU_INN ($C900) -> ov_stash
        M->>M: mk_off ($01 = $35), schermata, scelta dell'equipaggiamento
        M->>M: uscita: $01 = $36, ui_exit (11/11 sera: niente salvataggio)
    else fabbro / alchimista
        P->>M: MENU_SHOP ($C903, A = negozio): mk_off, enter_shop
        M->>M: shop_roll (merce a caso), compra / vende / ripara
        M->>M: mk_exit: $01 = $36, ui_exit
    end
```

## 16. Musica ed effetti

Sorgenti: `src/game/music.asm`, `src/common/sid_player.inc`, `src/common/sfx.inc`. Dettagli in [Musica](musica.md).

```mermaid
stateDiagram-v2
    [*] --> Luogo
    Luogo: brano del luogo (SND_LBUF)<br/>villaggio / livello a caso / boss
    Combattimento: motivetto (SND_FBUF)
    Silenzio: dissolvenza / disco
    Luogo --> Combattimento: boss con nome sullo schermo (mus_cmb, build_sprites)
    Combattimento --> Combattimento: il boss resta sullo schermo
    Combattimento --> Luogo: 2 s senza il boss sullo schermo:<br/>il brano riprende da dove era
    Luogo --> Silenzio: change_level: music_fadeout
    Silenzio --> Luogo: music_town / music_dungeon:<br/>brano dal disco (file SNDn)
    Luogo --> Luogo: snd_io durante il disco (SID zitto),<br/>poi volume pieno
```

`sfx_play` (effetto sulla voce 1, che il brano lascia libera mentre suona) e `music_update` girano da `sfx_update`: in
gioco nell'IRQ di fine HUD, nelle schermate da `ui_input`.

## 17. Sala del trono e vittoria

Sorgenti: `src/game/dungeon.asm` (`fin_doors`, `fin_chests`), `src/game/gen_io.asm` (`gen_final`), `src/game/game.asm`
(`final_tick`, `kill_monster`), `src/game/ui.asm` (`ui_lever`). Regole in [Mostri](mostri.md).

```mermaid
flowchart TD
    E["piano 20: FMAP (mappa di base) + gen_final"] --> FC["fin_chests: bauli epici<br/>nelle stanze chiuse"]
    FC --> B["Lord of Ruin (place_boss)"]
    B --> FT["final_tick a ogni fotogramma:<br/>vita sotto 3/4, 1/2, 1/4 -> 2 evocati<br/>(al massimo 4 vivi)"]
    FT --> K{"boss ucciso?"}
    K -->|no| FT
    K -->|si'| FD["kill_monster -> fin_doors:<br/>si aprono le stanze dei tesori"]
    FD --> LV["leva (tile T_LEVER): ui_lever"]
    LV -->|tirata| AB["c_lever = 1: portale per The Endless Abyss<br/>(non ancora disponibile)"]
```
