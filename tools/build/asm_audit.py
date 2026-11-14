#!/usr/bin/env python3
"""Analisi del codice ASSEMBLATO (11/11, richiesta del committente: guardare il risultato finale, non i sorgenti in parte
generati). Legge i listati di 64tass (out/work/<prog>.lst: indirizzo, byte, istruzione, riga del sorgente) di tutti i
programmi del disco e cerca:
  1. finestre di istruzioni ripetute uguali (candidati a una routine) con il risparmio stimato;
  2. spioncino: jsr+rts (-> jmp), jmp alla riga dopo, lda subito dopo sta dello stesso indirizzo, cmp #0 dopo
     un'istruzione che imposta gia' i flag, salti a un jmp, lda/ldx/ldy dello stesso valore due volte di fila;
  3. codice irraggiungibile (dopo rts/jmp/rti senza etichetta, fino alla prossima etichetta);
  4. etichette di codice mai usate in nessun sorgente, test o strumento (candidati a codice morto);
  5. le routine piu' grandi.
Uscita: out/work/asm_audit/analisi_assembly.md (tabelle) e out/work/asm_audit.json. Uso: python3 tools/build/asm_audit.py"""
import collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "work")
PROGS = ["game", "lobby", "menu", "start", "barbarian", "lore", "help", "jukebox"]
# riga d'istruzione: .indirizzo [indirizzo di esecuzione (.logical)] byte  istruzione  sorgente (formati diversi per programma)
INS = re.compile(r"^\.([0-9a-f]{4})\t(?:([0-9a-f]{4})\t|\t)?((?:[0-9a-f]{2} ?){1,3})\t+(\w{3})(?:[ \t]+([^\t]*?))?\t+(.*)$")
LAB = re.compile(r"^\.([0-9a-f]{4})\t+(?:([0-9a-f]{4})\t+)?([A-Za-z_][\w.]*|[+-]+):?\s*(?:;.*)?$")
FLAGSET = {"lda", "ldx", "ldy", "and", "ora", "eor", "adc", "sbc", "inx", "iny", "dex", "dey", "inc", "dec", "tax", "tay",
           "txa", "tya", "asl", "lsr", "rol", "ror", "pla"}
FLAGSET_A = {"lda", "and", "ora", "eor", "adc", "sbc", "txa", "tya", "pla"}     # Z/N gia' secondo A (cmp #0 inutile)
BR = {"bcc", "bcs", "beq", "bne", "bmi", "bpl", "bvc", "bvs"}


def parse(prog):
    p = os.path.join(OUT, prog + ".lst")
    if not os.path.exists(p):
        return None
    ins, labels = [], collections.defaultdict(list)
    for ln in open(p, errors="ignore"):
        ln = ln.rstrip("\n")
        m = INS.match(ln)
        if m:
            a = int(m.group(2) or m.group(1), 16)
            src = m.group(6)
            ins.append(dict(a=a, b=m.group(3).split(), m=m.group(4), op=(m.group(5) or "").strip(), src=src))
            lm = re.match(r"^([A-Za-z_]\w*|[+-]+):?\s", src)
            if lm and not src.startswith(" "):
                labels[a].append(lm.group(1))
            continue
        m = LAB.match(ln)
        if m:
            labels[int(m.group(2) or m.group(1), 16)].append(m.group(3))
    return ins, labels


def norm(i):
    """istruzione normalizzata per il confronto: i salti relativi per distanza, il resto per byte"""
    if i["m"] in BR:
        return i["m"] + " rel"
    return " ".join(i["b"])


def repeats(ins, labels, kmin=6, kmax=24):
    """finestre di k istruzioni uguali (nessuna etichetta dentro, nessun salto che esce): occorrenze, byte, risparmio"""
    found = {}
    n = len(ins)
    keyat = [norm(x) for x in ins]
    for k in range(kmax, kmin - 1, -1):
        seen = collections.defaultdict(list)
        for s in range(n - k + 1):
            w = ins[s:s + k]
            if any(w[j]["a"] in labels for j in range(1, k)):           # un'etichetta dentro: punto d'ingresso
                continue
            if any(x["m"] in BR for x in w):                              # salti: confronto non affidabile
                continue
            if any(w[j + 1]["a"] != w[j]["a"] + len(w[j]["b"]) for j in range(k - 1)):
                continue
            seen[tuple(keyat[s:s + k])].append(s)
        for key, starts in seen.items():
            starts2 = []
            for s in starts:                                              # occorrenze che non si sovrappongono
                if not starts2 or s >= starts2[-1] + k:
                    starts2.append(s)
            if len(starts2) < 2:
                continue
            size = sum(len(ins[starts2[0] + j]["b"]) for j in range(k))
            save = (len(starts2) - 1) * size - len(starts2) * 3 - 1     # una routine + jsr al posto di ogni copia
            if save < 8:
                continue
            cover = {(s, k) for s in starts2}
            if any(any(s0 <= s < s0 + k0 for s0, k0 in found) for s in starts2):
                continue                                                  # gia' dentro una finestra piu' lunga
            found[(starts2[0], k)] = dict(k=k, size=size, occ=len(starts2), save=save,
                                          where=[ins[s]["a"] for s in starts2], first=[ins[starts2[0] + j]["src"].strip() for j in range(min(k, 8))])
    return sorted(found.values(), key=lambda r: -r["save"])


def peephole(ins, labels):
    out = collections.defaultdict(list)
    for j in range(len(ins) - 1):
        a, b = ins[j], ins[j + 1]
        if b["a"] != a["a"] + len(a["b"]):
            continue
        if a["m"] == "jsr" and b["m"] == "rts":
            out["jsr + rts -> jmp (1 B e 9 cicli in meno" + (")" if b["a"] not in labels else "; la rts e' anche un punto d'arrivo: resta)")].append(a["a"])
        if a["m"] == "jmp" and a["op"].startswith("$") and int(a["op"][1:], 16) == b["a"]:
            out["jmp alla riga dopo (3 B inutili)"].append(a["a"])
        if a["m"] == "sta" and b["m"] == "lda" and a["op"] == b["op"] and b["a"] not in labels and "(" not in a["op"]:
            out["lda subito dopo sta dello stesso indirizzo (2-3 B)"].append(b["a"])
        if b["m"] == "cmp" and b["op"] == "#$00" and a["m"] in FLAGSET_A and b["a"] not in labels:
            out["cmp #0 dopo un'istruzione che imposta gia' Z/N (2 B)"].append(b["a"])
        if a["m"] == b["m"] and a["m"] in ("lda", "ldx", "ldy") and a["op"] == b["op"] and b["a"] not in labels:
            out["stesso caricamento due volte di fila"].append(b["a"])
    byaddr = {i["a"]: i for i in ins}
    for i in ins:
        if i["m"] in ("jmp", "jsr") and i["op"].startswith("$") and "(" not in i["op"]:
            t = byaddr.get(int(i["op"][1:], 16))
            if t and t["m"] == "jmp" and "(" not in t["op"]:
                out["%s a un jmp (si puo' saltare direttamente)" % i["m"]].append(i["a"])
    return out


def unreachable(ins, labels):
    res, j = [], 0
    while j < len(ins) - 1:
        i = ins[j]
        if i["m"] in ("rts", "rti") or (i["m"] == "jmp"):
            k, size, start = j + 1, 0, None
            while k < len(ins) and ins[k]["a"] == ins[k - 1]["a"] + len(ins[k - 1]["b"]) and ins[k]["a"] not in labels:
                if start is None: start = ins[k]["a"]
                size += len(ins[k]["b"]); k += 1
            if size and start is not None:
                res.append(dict(a=start, size=size, after=i["src"].strip()[:40]))
            j = k
        else:
            j += 1
    return res


def reach(ins, labels, src_lines, extern):
    """codice raggiungibile: dal primo byte, da ogni etichetta citata come indirizzo (#<, #>, .word, tabelle) e dai
    punti chiamati da altri programmi (extern); poi salti, chiamate e cadute. Restituisce i blocchi mai raggiunti."""
    byaddr = {i["a"]: k for k, i in enumerate(ins)}
    name2a = {}
    for a, ns in labels.items():
        for n in ns:
            name2a.setdefault(n, a)
    entries = {ins[0]["a"]} if ins else set()
    for ln in src_lines:
        for n in re.findall(r"[<>]\s*\(?\s*([A-Za-z_]\w*)", ln):
            if n in name2a: entries.add(name2a[n])
        m = re.search(r"\.(?:word|addr|rta)\s+(.*)", ln)
        if m:
            for n in re.findall(r"[A-Za-z_]\w*", m.group(1)):
                if n in name2a: entries.add(name2a[n])
    entries |= {a for a in extern if a in byaddr}
    seen, todo = set(), [a for a in entries if a in byaddr]
    while todo:
        a = todo.pop()
        if a in seen or a not in byaddr: continue
        seen.add(a)
        k = byaddr[a]
        i = ins[k]
        nxt = ins[k + 1]["a"] if k + 1 < len(ins) else a + len(i["b"])     # (dati in linea dopo jsr ui_pi: si saltano)
        op = i["op"]
        tgt = int(op[1:5], 16) if re.match(r"^\$[0-9a-f]{4}$", op) else None
        if i["m"] in BR or i["m"] == "jsr":
            if tgt is not None: todo.append(tgt)
            todo.append(nxt)
        elif i["m"] == "jmp":
            if tgt is not None: todo.append(tgt)
        elif i["m"] in ("rts", "rti", "brk"):
            pass
        else:
            todo.append(nxt)
            if i["m"] in ("bit",) and len(i["b"]) == 3 and i["b"][0] == "2c":    # trucco .byte $2c: salta 2 byte
                todo.append(a + 1)
    dead, cur = [], None
    for i in ins:
        if i["a"] not in seen:
            if cur and cur["end"] == i["a"]:
                cur["end"] += len(i["b"]); cur["size"] += len(i["b"])
            else:
                cur = dict(a=i["a"], end=i["a"] + len(i["b"]), size=len(i["b"]), label=(labels.get(i["a"]) or [""])[0], src=i["src"].strip()[:50])
                dead.append(cur)
    return [d for d in dead if d["size"] >= 3]


def used_names():
    """testo di tutti i sorgenti, inclusi generati, test e strumenti (per le etichette mai usate)"""
    txt = []
    for top in ("src", "out/work", "tests", "tools", "sim"):
        for dp, dn, fn in os.walk(os.path.join(ROOT, top)):
            dn[:] = [d for d in dn if d not in ("__pycache__", "zx0cache", "gfx", "snd", "prof", ".cache")]
            for f in fn:
                if f.endswith((".asm", ".inc", ".py", ".sh")) and not f.endswith(".lst"):
                    try: txt.append(open(os.path.join(dp, f), errors="ignore").read())
                    except OSError: pass
    return "\n".join(txt)


def dead_labels(prog, labels, alltxt):
    res = []
    for a, names in labels.items():
        for nm in names:
            if not re.match(r"^[A-Za-z]\w+$", nm) or nm.startswith("_"):
                continue
            n = len(re.findall(r"(?<![\w.])%s(?![\w])" % re.escape(nm), alltxt))
            if n <= 1:                                                   # solo la definizione
                res.append(dict(a=a, name=nm))
    return res


def sizes(ins, labels):
    pts = sorted((a, n[0]) for a, n in labels.items() if n and re.match(r"^[A-Za-z]\w+$", n[0]) and not n[0].startswith("_"))
    if not ins: return []
    end = ins[-1]["a"] + len(ins[-1]["b"])
    out = []
    for (a, n), nxt in zip(pts, pts[1:] + [(end, None)]):
        b = sum(len(i["b"]) for i in ins if a <= i["a"] < nxt[0])
        if b: out.append(dict(name=n, a=a, bytes=b))
    return sorted(out, key=lambda r: -r["bytes"])


def main():
    alltxt = used_names()
    R = {}
    ext = collections.defaultdict(set)                    # chiamate da un programma all'altro (LOBBY/MENU -> GAME)
    parsed = {p: parse(p) for p in PROGS}
    for p, pr in parsed.items():
        if not pr: continue
        for i in pr[0]:
            if i["m"] in ("jsr", "jmp") and re.match(r"^\$[0-9a-f]{4}$", i["op"]):
                for q in parsed:
                    ext[q].add(int(i["op"][1:], 16))
    for prog in PROGS:
        pr = parsed[prog]
        if not pr: continue
        ins, labels = pr
        src_lines = [l.split("\t")[-1] for l in open(os.path.join(OUT, prog + ".lst"), errors="ignore")]
        R[prog] = dict(n_ins=len(ins), bytes=sum(len(i["b"]) for i in ins), repeats=repeats(ins, labels),
                       peep={k: v for k, v in peephole(ins, labels).items()}, unreach=unreachable(ins, labels),
                       dead=dead_labels(prog, labels, alltxt), top=sizes(ins, labels)[:20],
                       unreached=reach(ins, labels, src_lines, ext[prog]))
    json.dump(R, open(os.path.join(OUT, "asm_audit.json"), "w"), indent=1)
    write_md(R)
    print(json.dumps({p: dict(ins=r["n_ins"], bytes=r["bytes"], repeats=len(r["repeats"]), save=sum(x["save"] for x in r["repeats"]),
                              peep={k: len(v) for k, v in r["peep"].items()}, unreach=sum(u["size"] for u in r["unreach"]),
                              dead=len(r["dead"]), unreached=sum(x["size"] for x in r["unreached"])) for p, r in R.items()}, indent=1))


NOTES_UNREACHED = {
    "gen_jtab": "falso positivo: tabella dei salti del generatore (GEN_AT + 3 = post_walls, chiamata con gen_call)",
    "jmp ov_stash": "falso positivo: tabella dei salti del modulo MENU (MENU_SHOP = OVL_AT + 3, chiamata dal gioco)",
    "jmp detail_screen": "solo la variante di test TESTUI=2 (scheda dell'eroe salvato) la chiama da GAME: nel gioco normale no",
    "PRESS / SPACE": "START senza titolo: il PRESS SPACE serve solo alla variante col titolo (LORE)",
    "jsr irq_off": "START senza titolo: l'apertura del file TITLE serve solo alla variante col titolo (LORE)",
    "sp_resume": "player SID condiviso: START e LORE non usano la ripresa del brano",
    "sp_release": "player SID condiviso: START e LORE non usano il rilascio naturale",
    "rd_hdr": "LORE: l'elenco degli eroi lo legge solo START (codice condiviso in boot.asm)",
    "start_game": "LORE: parte sempre la storia, mai il gioco direttamente",
    "jmp post_walls": "falso positivo: tabella dei salti del generatore",
}


def write_md(R):
    o = ["# Analisi dell'assembly generato (11/11)", "", "Copyright © 2026 - Simone Caporale", "",
         "Richiesta del committente (11/11): analizzare **il codice finale** dato all'assemblatore (non i sorgenti, in parte",
         "generati) cercando sprechi, codice ripetuto da trasformare in routine, codice morto. Strumento: `tools/build/asm_audit.py`",
         "(rifà questa pagina e `out/work/asm_audit.json` dai listati `out/work/<programma>.lst` di 64tass: indirizzo, byte, istruzione e riga",
         "del sorgente di **ogni** programma del disco, file generati compresi). I file generati per l'assemblatore",
         "(`out/work/db.asm`, `out/work/gfx_consts.inc`, ...) hanno dall'11/11 i commenti che servono a leggerli (indici delle tabelle, nome e",
         "descrizione di ogni tile).", "",
         "Metodo: (1) **raggiungibilità** sul binario: dal primo byte, dalle etichette usate come indirizzo (`#<`, `#>`, `.word`,",
         "tabelle) e dalle chiamate fra programmi (LOBBY, MENU → GAME), seguendo salti, chiamate e cadute (i dati in linea",
         "dopo `jsr ui_pi` e il trucco `.byte $2c` sono gestiti); (2) **finestre ripetute** di 6–24 istruzioni uguali senza",
         "etichette né salti dentro (risparmio = copie − routine − `jsr`); (3) **spioncino** (`jsr`+`rts`, `lda` dopo `sta` dello",
         "stesso indirizzo, `cmp #0` inutile, salti a un `jmp`); (4) etichette mai citate; (5) routine più grandi.", "",
         "## Totali", "", "| Programma | istruzioni | byte di codice | non raggiunto | ripetuto (risparmio stimato) | spioncino |",
         "|---|---|---|---|---|---|"]
    for p, r in R.items():
        o.append("| %s | %d | %d | %d B | %d finestre (%d B) | %d |" % (p.upper(), r["n_ins"], r["bytes"], sum(x["size"] for x in r["unreached"]),
                 len(r["repeats"]), sum(x["save"] for x in r["repeats"]), sum(len(v) for v in r["peep"].values())))
    o += ["", "## Codice non raggiunto", "", "| Programma | indirizzo | byte | inizio | nota |", "|---|---|---|---|---|"]
    for p, r in R.items():
        for x in r["unreached"]:
            note = next((v for k, v in NOTES_UNREACHED.items() if k in x["src"] or k == x["label"]), "da controllare")
            o.append("| %s | $%04X | %d | `%s` | %s |" % (p.upper(), x["a"], x["size"], (x["label"] + " " if x["label"] else "") + x["src"].replace("|", "/"), note))
    o += ["", "## Codice ripetuto (candidati a una routine)", "", "| Programma | istruzioni | byte | copie | risparmio | indirizzi | inizio |",
          "|---|---|---|---|---|---|---|"]
    for p, r in R.items():
        for x in r["repeats"][:20]:
            o.append("| %s | %d | %d | %d | %d B | %s | `%s` |" % (p.upper(), x["k"], x["size"], x["occ"], x["save"],
                     " ".join("$%04X" % a for a in x["where"]), " / ".join(x["first"][:4]).replace("|", "/")))
    o += ["", "## Spioncino", "", "| Programma | caso | indirizzi |", "|---|---|---|"]
    for p, r in R.items():
        for k, v in r["peep"].items():
            o.append("| %s | %s | %s |" % (p.upper(), k, " ".join("$%04X" % a for a in v)))
    o += ["", "## Routine più grandi (GAME)", "", "| Routine | byte |", "|---|---|"]
    for t in R["game"]["top"][:15]:
        o.append("| `%s` | %d |" % (t["name"], t["bytes"]))
    o += ["", "## Conclusioni e cosa è stato fatto", "",
          "- Il codice di GAME è già asciutto: dopo le pulizie dell'11/11 (O1–O14) il codice morto vero era **49 B** (`fill_rect` e",
          "  la macro `#rect`, mai usate; `_off` di `chest_blocked` con la variabile `chst_hold`): **tolti**, con due `lda` dopo",
          "  `sta` dello stesso indirizzo e un `jsr ui_box` + `rts` (+55 B di margine). Gli altri `jsr`+`rts` hanno la `rts` come",
          "  punto d'arrivo di altri salti (si risparmia solo un ciclo, non byte).",
          "- Codice ripetuto in GAME: ~230 B stimati in tutto, in tanti pezzi piccoli (8–38 B l'uno): il più utile è la casella",
          "  del mostro (`lda mxl,x / pha / lda mxh,x / tax / pla / jsr pix2tile` e lo stesso per y, 4 copie ciascuno: ~46 B) e",
          "  l'impostazione dei puntatori della grafica (`GFX_FSTRIP`, 4 copie: ~38 B). Proposte nel TODO (D12).",
          "- START e LORE condividono `boot.asm` e il player SID: nelle due varianti restano **~155 B** (START) e **~180 B** (LORE) di",
          "  codice dell'altra variante (PRESS SPACE, apertura del titolo, lettura degli eroi, ripresa/rilascio del brano).",
          "  Non pesano su GAME: solo qualche decina di millisecondi di caricamento. Si possono escludere con `.if` (TODO D12).",
          "- LOBBY, MENU, BARBARIAN, HELP: niente di rilevante (qualche `jmp` alla riga dopo nelle tabelle d'ingresso,",
          "  che servono)."]
    os.makedirs(os.path.join(ROOT, "out", "work", "asm_audit"), exist_ok=True); open(os.path.join(ROOT, "out", "work", "asm_audit", "analisi_assembly.md"), "w").write("\n".join(o) + "\n")


if __name__ == "__main__":
    main()
