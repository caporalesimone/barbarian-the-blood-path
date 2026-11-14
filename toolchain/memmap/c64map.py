#!/usr/bin/env python3
"""Memory and disk map of a C64 project, AUTOMATIC and with no configuration (14/11). Copyright (c) 2026 - Simone Caporale

Usage (in the c64-builder container):  python3 toolchain/memmap/c64map.py [--work out/work] [--disk out/work/disk.d64] [--out DIR]
It reads only what the build already produces:
  - the 64tass listings (*.lst, option -L): for every emitted byte the address in the file, the run address (.logical) and the
    source file; the .virtual reservations (.byte ?, .word ?, .fill n); the addresses used by the instructions;
  - the labels (*.lbl, option -l), to name addresses;
  - the .d64 disk: directory, block chains, load address of every PRG.
A listing is a "module" of the program if its output file (-o) is on the disk (same content) or a disk file has its name
(game -> GAME, menu -> MENU1..3: compressed or split files). The other listings (test variants) are listed apart.
Output: DIR/index.html (RAM and disk) and DIR/memmap.json (the same data for other tools, with "metrics" in the format of the
viewer manifest).
--probe DIR (default out/work/memprobe if it exists): RAM dumps of the run-time probe in VICE (toolchain/memmap/probe.py); only
the dumps made with the same disk are used. They add the memory really written while the scenarios ran.

Limits (static analysis): data copied or unpacked by the program somewhere else, buffers used only through pointers and tables
read with an index past their first byte are not seen; the area of data that becomes free after start-up stays used.
The run-time probe covers part of it (what the scenarios run); the planned additions (annotations in the sources) are in the TODO."""
import argparse, glob, hashlib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import probe  # noqa: E402  (run-time memory probe in VICE: toolchain/memmap/probe.py)

# ------------------------------------------------------------------ the C64
SYSTEM = [  # (start, end included, name, note)
    (0x0000, 0x0001, "6510 port", "$00 direction, $01 memory banks"),
    (0x0002, 0x00FF, "zero page", "also used by BASIC and KERNAL when active"),
    (0x0100, 0x01FF, "stack", "6510 stack"),
    (0x0200, 0x03FF, "BASIC and KERNAL", "system buffers and vectors"),
    (0x0400, 0x07FF, "default screen", "$0400-$07E7 text, $07F8-$07FF sprite pointers"),
    (0x0800, 0x9FFF, "RAM", "BASIC programs from $0801"),
    (0xA000, 0xBFFF, "BASIC ROM / RAM", "RAM when $01 switches the ROM off"),
    (0xC000, 0xCFFF, "RAM", "4 KB never used by the system"),
    (0xD000, 0xDFFF, "I/O / RAM", "VIC, SID, color RAM, CIA; RAM when $01 switches the I/O off"),
    (0xE000, 0xFFFF, "KERNAL ROM / RAM", "RAM when $01 switches the ROM off"),
]
BANKS = [  # for the free space: (start, end, name)
    (0x0400, 0x9FFF, "RAM $0400-$9FFF"), (0xA000, 0xBFFF, "under the BASIC ROM"), (0xC000, 0xCFFF, "RAM $C000-$CFFF"),
    (0xD000, 0xDFFF, "under the I/O"), (0xE000, 0xFFFF, "under the KERNAL"),
]
IO = [  # registers: (start, end, name)
    (0xD000, 0xD3FF, "VIC-II"), (0xD400, 0xD7FF, "SID"), (0xD800, 0xDBFF, "color RAM"), (0xDC00, 0xDCFF, "CIA 1"),
    (0xDD00, 0xDDFF, "CIA 2"), (0xDE00, 0xDFFF, "I/O 1-2 (cartridges)"),
]
KERNAL = {0xFF81: "CINT", 0xFF84: "IOINIT", 0xFF87: "RAMTAS", 0xFF8A: "RESTOR", 0xFF8D: "VECTOR", 0xFF90: "SETMSG", 0xFF93: "SECOND",
          0xFF96: "TKSA", 0xFF99: "MEMTOP", 0xFF9C: "MEMBOT", 0xFF9F: "SCNKEY", 0xFFA2: "SETTMO", 0xFFA5: "ACPTR", 0xFFA8: "CIOUT",
          0xFFAB: "UNTLK", 0xFFAE: "UNLSN", 0xFFB1: "LISTEN", 0xFFB4: "TALK", 0xFFB7: "READST", 0xFFBA: "SETLFS", 0xFFBD: "SETNAM",
          0xFFC0: "OPEN", 0xFFC3: "CLOSE", 0xFFC6: "CHKIN", 0xFFC9: "CHKOUT", 0xFFCC: "CLRCHN", 0xFFCF: "CHRIN", 0xFFD2: "CHROUT",
          0xFFD5: "LOAD", 0xFFD8: "SAVE", 0xFFDB: "SETTIM", 0xFFDE: "RDTIM", 0xFFE1: "STOP", 0xFFE4: "GETIN", 0xFFE7: "CLALL",
          0xFFEA: "UDTIM", 0xFFED: "SCREEN", 0xFFF0: "PLOT", 0xFFF3: "IOBASE"}
WRITES = {"sta", "stx", "sty", "inc", "dec", "asl", "lsr", "rol", "ror", "sax", "dcp", "isc", "slo", "sre", "rla", "rra", "shy", "shx"}
BRANCH = {"bcc", "bcs", "beq", "bne", "bmi", "bpl", "bvc", "bvs"}


def h4(a):
    return "$%04X" % a


# ------------------------------------------------------------------ ranges (sorted list of [a, b) )
def ranges_of(addrs):
    """addresses -> contiguous ranges [a, b)"""
    out = []
    for a in sorted(set(addrs)):
        if out and out[-1][1] == a:
            out[-1][1] = a + 1
        else:
            out.append([a, a + 1])
    return [tuple(r) for r in out]


# ------------------------------------------------------------------ 64tass listings
HEXF = re.compile(r"^[0-9a-f]{2}( [0-9a-f]{2})*$")
MNEM = re.compile(r"^[a-z]{3}(\s|$)")


def split_line(line):
    """listing line -> (kind '.'|'>', address, pc or None, bytes, instruction, source) or None.
    Columns are separated by tabs but their width changes from listing to listing (with or without the .logical PC column):
    the PC is the field right after the address, the bytes are in the first fields, the source is the last one."""
    if not line or line[0] not in ".>" or len(line) < 5:
        return None
    f = line.split("\t")
    try:
        off = int(f[0][1:], 16)
    except ValueError:
        return None
    pc, i = None, 1
    if len(f) > 1 and re.fullmatch(r"[0-9a-f]{4}", f[1]):
        pc, i = int(f[1], 16), 2
    hx, mon, src = [], "", ""
    rest = f[i:]
    k = 0
    while k < len(rest) and rest[k] == "" and k < 2:
        k += 1
    if k < len(rest) and k <= 1 and HEXF.match(rest[k]):
        hx = rest[k].split(); k += 1
    nonempty = [(j, x) for j, x in enumerate(rest) if x != "" and j >= k]
    if nonempty and MNEM.match(nonempty[0][1]) and hx and len(nonempty) >= 1 and not nonempty[0][1].startswith(" "):
        mon = nonempty[0][1]; nonempty = nonempty[1:]
    if nonempty:
        src = nonempty[-1][1]
    return line[0], off, pc, hx, mon, src


RESERVE = re.compile(r"^\s*(?:[\w@.+-]+:?\s+)?\.(byte|char|word|addr|rta|long|dword|fill|res)\b\s*(.*)$", re.I)


class Module:
    def __init__(self, lst):
        self.lst = lst
        self.name = os.path.splitext(os.path.basename(lst))[0]
        self.output = None
        self.binary = False
        self.bytes = {}          # run address -> source file
        self.image = {}          # address in the loaded file -> run address (only where they differ: .logical)
        self.loaded = set()      # addresses of the loaded file (image) covered by the listing
        self.virtual = []        # (start, size, name, file)
        self.refs = {}           # address -> set of "r" / "w" / "x" / "i" (indexed) / "p" (pointer)
        self.files = {}          # source file -> emitted bytes
        self.labels = {}
        self.disk = []           # names of the linked disk files
        self.link = ""           # how it was linked to the disk


def parse_lst(path):
    m = Module(path)
    cur = None
    last = None                  # (file address, run address) after the last line of bytes: for "...repeated..."
    pend = []                    # pending reservations: (address, name, directive, argument, file)
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f):
            line = line.rstrip("\n")
            if n < 4 and line.startswith("; 64tass") and " -o " in line:
                o = re.search(r"\s-o\s+(\S+)", line)
                m.output = o.group(1) if o else None
                m.binary = bool(re.search(r"\s(-b|--nostart)\b", line))
                continue
            r = re.match(r"^;\s*\.\.\.repeated \d+ times \((\d+) bytes\)", line)
            if r and last:
                n_ = int(r.group(1))
                emit(m, last[0], last[1], n_, cur)
                last = (last[0] + n_, last[1] + n_)
                continue
            if line.startswith(";******"):
                r = re.search(r"(?:Processing input file|Processing file|Return to file):\s*(.+)$", line)
                if r:
                    cur = r.group(1).strip()
                continue
            x = split_line(line)
            if not x:
                continue
            kind, off, pc, hb, mon, src = x
            run = pc if pc is not None else off
            if hb:
                emit(m, off, run, len(hb), cur)
                last = (off + len(hb), run + len(hb))
                refs(m, mon)
            elif kind == ">":
                r = RESERVE.match(src)
                if r:
                    lab = src.split()[0] if not src[:1].isspace() else ""
                    pend.append((run, lab.rstrip(":"), r.group(1).lower(), r.group(2).split(";")[0].strip(), cur))
    # size of the reservations: up to the next one if contiguous, otherwise from the directive
    for i, (a, lab, d, arg, fl) in enumerate(pend):
        size = None
        if i + 1 < len(pend) and 0 < pend[i + 1][0] - a <= 4096 and pend[i + 1][4] == fl:
            size = pend[i + 1][0] - a
        if size is None or size > 1024:
            size = reserve_size(d, arg, m)
        m.virtual.append((a, size, lab, fl))
    return m


def emit(m, off, run, n, cur):
    for i in range(n):
        m.bytes[(run + i) & 0xFFFF] = cur
        m.loaded.add((off + i) & 0xFFFF)
        if run != off:
            m.image[(off + i) & 0xFFFF] = (run + i) & 0xFFFF
    m.files[cur] = m.files.get(cur, 0) + n


def reserve_size(d, arg, m):
    unit = {"byte": 1, "char": 1, "word": 2, "addr": 2, "rta": 2, "long": 3, "dword": 4}.get(d)
    if unit:
        return unit * max(1, arg.count(",") + 1)
    tok = arg.split(",")[0].strip()
    try:
        return int(tok.replace("$", "0x"), 0) if tok else 1
    except ValueError:
        return m.labels.get(tok, 1)


OPER = re.compile(r"^([a-z]{3})\s+(.*)$")


def refs(m, mon):
    """addresses used by an instruction ('Monitor' column of the listing)"""
    x = OPER.match(mon.strip())
    if not x:
        return
    op, arg = x.groups()
    if arg.startswith("#") or op in BRANCH:
        return
    a = re.search(r"\$([0-9a-f]{2,4})", arg)
    if not a:
        return
    addr = int(a.group(1), 16)
    k = "x" if op in ("jsr", "jmp") else "w" if op in WRITES else "r"
    s = m.refs.setdefault(addr, set())
    s.add(k)
    if arg.startswith("("):
        s.add("p")                                          # zero page pointer (or jmp vector)
        if k != "x":
            m.refs.setdefault((addr + 1) & 0xFFFF, set()).add("p")
    elif "," in arg:
        s.add("i")                                          # indexed: a table that starts here


def parse_lbl(path):
    d = {}
    for l in open(path, encoding="utf-8", errors="replace"):
        x = re.match(r"\s*([A-Za-z_][\w.]*)\s*=\s*\$([0-9a-fA-F]+)\s*$", l)
        if x:
            d[x.group(1)] = int(x.group(2), 16)
    return d


# ------------------------------------------------------------------ .d64 disk
def d64(path):
    img = open(path, "rb").read()
    tracks = 40 if len(img) >= 196608 else 35
    spt = lambda t: 21 if t <= 17 else 19 if t <= 24 else 18 if t <= 30 else 17
    off, o = {}, 0
    for t in range(1, tracks + 1):
        for s in range(spt(t)):
            off[(t, s)] = o
            o += 256
    blk = lambda t, s: img[off[(t, s)]:off[(t, s)] + 256]

    def chain(t, s):
        out, seen = [], set()
        while t and (t, s) in off and (t, s) not in seen:
            seen.add((t, s)); out.append((t, s))
            b = blk(t, s); t, s = b[0], b[1]
        return out

    def data(ch):
        d = b""
        for t, s in ch:
            b = blk(t, s)
            d += b[2:] if b[0] else b[2:b[1] + 1]
        return d

    pet = lambda bs: "".join(chr(c + 32) if 0x41 <= c <= 0x5A else chr(c - 128) if 0xC1 <= c <= 0xDA else chr(c) if 32 <= c < 127 else "?"
                             for c in bs.rstrip(b"\xa0"))
    bam = blk(18, 0)
    files = []
    for t, s in chain(18, 1):
        b = blk(t, s)
        for e in range(8):
            x = b[e * 32:(e + 1) * 32]
            if not x[2] & 7:
                continue
            ch = chain(x[3], x[4])
            body = data(ch)
            f = {"name": pet(x[5:21]), "type": ["DEL", "SEQ", "PRG", "USR", "REL"][x[2] & 7] if (x[2] & 7) < 5 else "?",
                 "blocks": x[30] + 256 * x[31], "chain": ch, "data": body}
            if f["type"] == "PRG" and len(body) >= 2:
                la = body[0] + 256 * body[1]
                if la >= 0x0200:                               # below $0200 (e.g. $0000): fake address, the program loads it elsewhere
                    f["load"] = la
                    f["end"] = la + len(body) - 2              # excluded
                else:
                    f["fake_load"] = la
            files.append(f)
    owner = {}
    for i, f in enumerate(files):
        for ts in f["chain"]:
            owner[ts] = i
    for ts in chain(18, 0):
        owner.setdefault(ts, "dir")
    free_bam = {(t, s) for t in range(1, 36) for s in range(spt(t)) if bam[4 * t + 1 + s // 8] >> (s % 8) & 1}
    return {"name": pet(bam[0x90:0xA0]), "id": pet(bam[0xA2:0xA4]), "tracks": tracks, "spt": spt, "files": files, "owner": owner,
            "free_bam": free_bam, "free": sum(bam[4 * t] for t in range(1, 36) if t != 18),
            "total": sum(spt(t) for t in range(1, 36) if t != 18)}


# ------------------------------------------------------------------ analysis
def resolve(p, work):
    """path written in the 64tass command line (relative to the folder it was run from)"""
    if os.path.isabs(p):
        return p
    d = work
    for _ in range(6):
        q = os.path.join(d, p)
        if os.path.isfile(q):
            return q
        d = os.path.dirname(d)
    return os.path.join(os.getcwd(), p)


def analyse(work, disk_path):
    work = os.path.abspath(work)
    mods = []
    for p in sorted(glob.glob(os.path.join(work, "*.lst"))):
        m = parse_lst(p)
        lb = os.path.splitext(p)[0] + ".lbl"
        if os.path.isfile(lb):
            m.labels = parse_lbl(lb)
        m.prg = None
        if m.output and os.path.isfile(resolve(m.output, work)):
            raw = open(resolve(m.output, work), "rb").read()
            m.prg = raw
            if not m.binary and len(raw) > 2:            # PRG bytes the listing does not show: filler (* = ..., .align)
                la = raw[0] + 256 * raw[1]
                m.filler = [a & 0xFFFF for a in range(la, la + len(raw) - 2) if (a & 0xFFFF) not in m.loaded]
        m.filler = getattr(m, "filler", [])
        mods.append(m)
    disk = d64(disk_path) if disk_path and os.path.isfile(disk_path) else None
    if disk:
        byhash = {}
        for f in disk["files"]:
            byhash.setdefault(hashlib.sha1(f["data"]).hexdigest(), []).append(f["name"])
        for m in mods:
            if m.prg:
                for cand in ([m.prg] if m.binary else [m.prg, m.prg[2:]]):
                    hit = byhash.get(hashlib.sha1(cand).hexdigest())
                    if hit:
                        m.disk, m.link = hit, "same content"
                        break
            if not m.disk:                                   # compressed or split files: same name, or name + digits
                stem = m.name.lower()
                for s in (stem, stem[:-1] if stem.endswith("z") else None):
                    if not s:
                        continue
                    hit = [f["name"] for f in disk["files"] if f["name"].lower() == s or re.fullmatch(re.escape(s) + r"[-_]?\d+", f["name"].lower())]
                    if hit:
                        m.disk, m.link = hit, "same name"
                        break
        built = {}
        for p in sorted(glob.glob(os.path.join(work, "**", "*.prg"), recursive=True) + glob.glob(os.path.join(work, "**", "*.bin"), recursive=True)):
            built.setdefault(hashlib.sha1(open(p, "rb").read()).hexdigest(), os.path.relpath(p, work))
        for f in disk["files"]:
            f["built"] = built.get(hashlib.sha1(f["data"]).hexdigest())
            f["modules"] = [m.name for m in mods if f["name"] in m.disk]
    used = [m for m in mods if m.disk] if disk else mods
    other = [m for m in mods if m not in used]
    return used, other, disk


# ------------------------------------------------------------------ memory layers
CODE, RES, REF, IMG, LOAD, FILL, DATA = ("code and data", "reserved variables", "used by the code", "image to be moved", "module file",
                                         "filler", "data file")


def layers(used, disk):
    """address -> {kind: set(who)}; kinds: CODE (emitted bytes, at the run address), RES (.virtual), IMG (image of a .logical
    block: in the file at one place, run elsewhere), FILL (PRG bytes with no source), LOAD / DATA (disk file at its load address:
    of a module, e.g. compressed, or data that stays), REF (address used by an instruction and covered by nothing else)"""
    occ = {}
    put = lambda a, k, who: occ.setdefault(a & 0xFFFF, {}).setdefault(k, set()).add(who)
    for m in used:
        for a in m.bytes:
            put(a, CODE, m.name)
        for a, size, _, _ in m.virtual:
            for i in range(size):
                put(a + i, RES, m.name)
        for a in m.image:
            put(a, IMG, m.name)
        for a in m.filler:
            put(a, FILL, m.name)
    if disk:
        for f in disk["files"]:
            if "load" in f:       # module file (e.g. compressed): its listing counts; the other files are data that stays
                for a in range(f["load"], min(f["end"], 0x10000)):
                    put(a, LOAD if f.get("modules") else DATA, f["name"])
    for m in used:
        for a, k in m.refs.items():
            o = occ.get(a, {})
            if a < 2 or CODE in o or RES in o:
                continue
            if io_name(a) or a in KERNAL:
                continue                                      # system registers and routines, not program RAM
            put(a, REF, m.name)
    return occ


def io_name(a):
    for s, e, n in IO:
        if s <= a <= e:
            return n
    return None


def is_free(o, strict):
    if not o:
        return True
    if CODE in o or RES in o or REF in o or DATA in o:
        return False
    return not strict


def free_ranges(occ, strict=False, minsize=1):
    """free space per bank: strict=False = free from the program (images to be moved, fillers and module files, compressed or to be
    copied, count as free after use); strict=True = never used by anything"""
    out = []
    for s, e, bank in BANKS:
        cur = None
        for a in range(s, e + 2):
            if a <= e and is_free(occ.get(a), strict):
                cur = a if cur is None else cur
            elif cur is not None:
                if a - cur >= minsize:
                    out.append((cur, a, bank))
                cur = None
    return out


def segments(addrs):
    return ranges_of(addrs)


def overlaps(used):
    out = []
    for i, a in enumerate(used):
        sa = set(a.bytes) | {x + k for x, s, _, _ in a.virtual for k in range(s)}
        for b in used[i + 1:]:
            sb = set(b.bytes) | {x + k for x, s, _, _ in b.virtual for k in range(s)}
            both = sa & sb
            if both:
                out.append((a.name, b.name, ranges_of(both)))
    return out


# ------------------------------------------------------------------ run-time probe (VICE)
def probe_data(folder, disk_path):
    """dumps of the probe made with this disk -> dict or None"""
    dumps, ignored = probe.load(folder, probe.file_sha1(disk_path) if disk_path else None)
    if not dumps:
        return {"dumps": 0, "ignored": ignored} if ignored else None
    run = set().union(*(d["written"] for d in dumps))
    never = [a for a in range(0x0400, 0x10000) if probe.probed(a) and a not in run]
    return {"dumps": len(dumps), "ignored": ignored, "run": run, "never": never,
            "scenarios": sorted(((d["tag"], len(d["written"])) for d in dumps), key=lambda x: x[0])}


def bank_of(a):
    for s, e, bank in BANKS:
        if s <= a <= e:
            return bank
    return None


def probe_ranges(addrs):
    """addresses -> [(a, b, bank)] split at the bank borders (bank None below $0400)"""
    cuts = sorted({x for s, e, _ in BANKS for x in (s, e + 1)})
    out = []
    for a, b in ranges_of(addrs):
        pts = [a] + [c for c in cuts if a < c < b] + [b]
        out += [(x, y, bank_of(x)) for x, y in zip(pts, pts[1:])]
    return out


def probe_html(pr, occ):
    P = []
    w = P.append
    w("<section><h2>Measured in VICE (run-time probe)</h2>")
    if not pr.get("run"):
        w("<p class='note' style='margin-top:0'>%d RAM dumps found, none made with this disk (test variants or an older build): "
          "run the probe again (<code>./build.sh --probe</code>).</p></section>" % pr["dumps"])
        return "".join(P)
    nv = probe_ranges(pr["never"])
    w("<div class='kv'><div><b>%d B</b><span>RAM never written while running ($033C-$03FB, $0400-$07FF, $0803-$FFFF)</span></div>" % len(pr["never"]))
    for s, e, bank in BANKS:
        w("<div><b>%d B</b><span>never written: %s</span></div>" % (sum(b - a for a, b, k in nv if k == bank), E(bank)))
    w("<div><b>%d</b><span>VICE sessions (dumps)%s</span></div></div>" % (pr["dumps"], (", %d of other disks ignored" % pr["ignored"]) if pr["ignored"] else ""))
    w("<p class='note'>Right after the boot the RAM is filled with a known pattern, the scenarios run, then the RAM is saved: a byte "
      "still equal to the pattern was <b>never written</b>. This is the real use while running (data copied or unpacked, buffers, "
      "screen) that the static analysis cannot see, but only for what the scenarios run (the tests of the project).</p>")
    # page grid: share of every page written at run time
    w("<div class='pages' style='margin-top:10px'><div></div>" + "".join("<div class='h'>%X</div>" % c for c in range(16)))
    run = pr["run"]
    for r in range(16):
        w("<div class='rh'>$%X000</div>" % r)
        for c in range(16):
            pg = r * 16 + c
            pa = [a for a in range(pg * 256, pg * 256 + 256) if probe.probed(a)]
            if not pa:
                w("<div class='pg sys' title='$%02X00-$%02XFF  not probed' style='background:transparent'></div>" % (pg, pg)); continue
            n = sum(1 for a in pa if a in run)
            st = sum(1 for a in pa if a not in run and is_free(occ.get(a), False))
            tip = "$%02X00-$%02XFF  %s\nwritten at run time: %d of %d B\nnever written: %d B (%d of them free also for the static analysis)" % (
                pg, pg, sys_name(pg * 256), n, len(pa), len(pa) - n, st)
            w("<div class='pg' title='%s'><i style='flex:%d;background:#8a1c14'></i><i style='flex:%d;background:#4f9d4566'></i></div>" % (
                E(tip, True), n, len(pa) - n))
    w("</div><div class='legend' style='margin-top:6px'><span><i style='background:#8a1c14'></i>written at run time</span>"
      "<span><i style='background:#4f9d4566'></i>never written</span></div>")
    # never written stretches, compared with the static view
    w("<h3>Never written while running</h3><div class='wrap'><table><tr><th>From</th><th>To</th><th class='n'>Bytes</th><th>Bank</th>"
      "<th>Static analysis</th></tr>")
    small = 0
    for a, b, bank in nv:
        if b - a < 16:
            small += b - a; continue
        used = sorted(cover(occ, a, b))
        nfree = sum(1 for x in range(a, b) if is_free(occ.get(x), False))
        st = "free" if nfree == b - a else ("used by: " + ", ".join(used)) if not nfree else "%d B free; used by: %s" % (nfree, ", ".join(used))
        w("<tr><td class='mono'>%s</td><td class='mono'>%s</td><td class='n'>%d</td><td>%s</td><td>%s</td></tr>" % (h4(a), h4(b - 1), b - a, E(bank or ""), E(st)))
    w("</table></div><p class='note'>Stretches of at least 16 bytes; %d more bytes in shorter stretches. \"Used by\" on a never written "
      "stretch = the program declares or loads something there that the scenarios never wrote (code not loaded in the tests, variables "
      "never set, reservations larger than needed): candidates to check, not free memory for sure.</p>" % small)
    # written but statically free
    hid = [a for a in pr["run"] if 0x0400 <= a and is_free(occ.get(a), True)]
    hr = [(a, b) for a, b in ranges_of(hid) if b - a >= 16]
    w("<details><summary>Written at run time where the static analysis sees nothing (%d B)</summary><p class='note'>Buffers behind "
      "pointers, unpacked or copied data, screen and sprite areas, memory cleared at start-up, the test shortcuts.</p>"
      "<div class='wrap'><table><tr><th>From</th><th>To</th><th class='n'>Bytes</th><th>Bank</th></tr>" % len(hid))
    for a, b in hr:
        w("<tr><td class='mono'>%s</td><td class='mono'>%s</td><td class='n'>%d</td><td>%s</td></tr>" % (h4(a), h4(b - 1), b - a, E(bank_of(a) or "")))
    w("</table></div></details>")
    w("<details><summary>Scenarios (%d)</summary><div class='wrap'><table><tr><th>Scenario</th><th class='n'>Bytes written</th></tr>" % len(pr["scenarios"]))
    for t, n in pr["scenarios"]:
        w("<tr><td class='mono'>%s</td><td class='n'>%d</td></tr>" % (E(t), n))
    w("</table></div></details></section>")
    return "".join(P)


# ------------------------------------------------------------------ HTML page
E = html.escape
PALETTE = ["#c8301e", "#8e5bb0", "#e8762b", "#1f8a8a", "#c2477e", "#b8860b", "#7a4a2a", "#5d8a2f", "#d4622a", "#6a4c93", "#2f9e8f",
           "#a0522d", "#9a3b5f", "#8a7a20", "#4a6a50", "#b5653f"]          # no blue (data files) and no light green (free)
KCOL = {CODE: "#8a1c14", RES: "#e8762b", REF: "#f2c230", DATA: "#2f6db5", IMG: "#7fa7d9", FILL: "#c9b98f", LOAD: "#b9cce6"}
CSS = """
:root{--paper:#f3ead3;--card:#fbf6e9;--ink:#2a2118;--ink2:#6a5a40;--rule:#d6c8a2;--red:#8a1c14;--night:#14121c;--key:#fffaf0;
--mono:"DejaVu Sans Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
@media (prefers-color-scheme:dark){:root{--paper:#18140f;--card:#221c15;--ink:#efe4c8;--ink2:#b3a37f;--rule:#3b3125;--red:#e2735c;--key:#2e261d}}
*{box-sizing:border-box}html,body{background:var(--paper)}body{margin:0;color:var(--ink);font:14.5px/1.5 var(--sans)}
.top{background:var(--night);color:#f0e6c8;position:relative;overflow:hidden}.top .in{max-width:1240px;margin:0 auto;padding:20px 330px 18px 16px}
.top h1{margin:0;font:700 22px var(--mono);letter-spacing:.04em}.top .proj{font:600 12.5px var(--mono);letter-spacing:.18em;text-transform:uppercase;color:#d9c99e}
.top .sub{font:12.5px var(--mono);color:#c9bd9c;margin-top:6px}
.rainbow{position:absolute;right:-40px;top:0;bottom:0;width:300px;display:flex;transform:skewX(-28deg)}.rainbow i{flex:1}
.stripes{height:12px;display:grid;grid-template-rows:repeat(5,1fr)}
.r1{background:#c8301e}.r2{background:#e8762b}.r3{background:#f2c230}.r4{background:#4f9d45}.r5{background:#2f6db5}
@media (max-width:760px){.top .in{padding-right:16px}.rainbow{width:150px;opacity:.5}}
main{max-width:1240px;margin:0 auto;padding:20px 16px 60px}
section{background:var(--card);border:1px solid var(--rule);border-top:3px solid var(--red);padding:14px 16px 16px;margin:0 0 16px;min-width:0}
h2{display:inline-block;font:600 12.5px var(--mono);letter-spacing:.08em;text-transform:uppercase;background:var(--ink);color:var(--paper);padding:2px 8px;margin:0 0 12px}
h3{font:700 17px var(--mono);margin:14px 0 6px;color:var(--red)}
.kv{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 18px;margin:4px 0 6px}
.kv div{border-left:3px solid var(--rule);padding-left:9px}.kv b{display:block;font:700 18px var(--mono)}.kv span{font-size:12.5px;color:var(--ink2)}
table{width:100%;border-collapse:collapse;font-size:13px}th{background:var(--ink);color:var(--paper);text-align:left;padding:4px 8px;font:600 11.5px var(--mono)}
td{border-bottom:1px solid var(--rule);padding:4px 8px;vertical-align:top}td.n,th.n{text-align:right;font-family:var(--mono);white-space:nowrap}
.mono{font-family:var(--mono);font-size:12.5px}.dim{color:var(--ink2)}.note{font-size:13px;color:var(--ink2);margin:8px 0 0}
.wrap{overflow-x:auto}details{margin-top:8px}summary{cursor:pointer;color:var(--red);font:600 13px var(--mono)}
.tag{font:600 11px var(--mono);padding:0 6px;border:1.5px solid currentColor;border-radius:5px;box-shadow:0 2px 0 currentColor;background:var(--key);white-space:nowrap}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12.5px;margin:6px 0 10px}.legend i{display:inline-block;width:14px;height:10px;margin-right:5px;vertical-align:-1px;border:1px solid rgba(0,0,0,.25)}
.pages{display:grid;grid-template-columns:44px repeat(16,minmax(0,1fr));gap:2px;font:11px var(--mono)}
.pages .h{color:var(--ink2);text-align:center;align-self:end}.pages .rh{color:var(--ink2);text-align:right;padding-right:4px;align-self:center}
.pg{height:30px;display:flex;flex-direction:column;border:1px solid var(--rule);background:#3a8f3a22;cursor:default}.pg i{display:block}
.pg.sys{outline:1px dashed var(--ink2);outline-offset:-3px}
svg.tracks{width:100%;height:auto;display:block;font:11px var(--mono)}
.grid{display:grid;gap:1px;font:9px var(--mono)}.grid .s{height:13px;border:1px solid rgba(0,0,0,.08)}
"""


def page_html(used, other, disk, occ, title, pr=None):
    P = []
    w = P.append
    col = {m.name: PALETTE[i % len(PALETTE)] for i, m in enumerate(used)}
    fr = free_ranges(occ)
    frs = free_ranges(occ, strict=True)
    tot = lambda rs: sum(b - a for a, b, _ in rs)
    w("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>")
    w("<title>%s</title><style>%s</style></head><body>" % (E((title + " · " if title else "") + "Memory map"), CSS))
    w("<div class='top'><div class='rainbow'><i class='r1'></i><i class='r2'></i><i class='r3'></i><i class='r4'></i><i class='r5'></i></div>"
      "<div class='in'><div class='proj'>%s</div><h1>MEMORY MAP</h1><div class='sub'>generated automatically from 64tass listings, "
      "labels and disk (toolchain/memmap/c64map.py)</div></div></div><div class='stripes'><i class='r1'></i><i class='r2'></i>"
      "<i class='r3'></i><i class='r4'></i><i class='r5'></i></div><main>" % E(title or "C64 project"))

    # --- summary
    w("<section><h2>Summary</h2><div class='kv'>")
    w("<div><b>%d B</b><span>RAM free from the program ($0400-$FFFF)</span></div>" % tot(fr))
    for s, e, bank in BANKS:
        w("<div><b>%d B</b><span>%s</span></div>" % (sum(b - a for a, b, k in fr if k == bank), E(bank)))
    w("<div><b>%d B</b><span>never used (not even by images, fillers, loaded files)</span></div>" % tot(frs))
    w("<div><b>%d</b><span>modules (listings linked to the disk)</span></div>" % len(used))
    if disk:
        w("<div><b>%d / %d</b><span>free blocks on the disk</span></div>" % (disk["free"], disk["total"]))
    w("</div><p class='note'><b>Free from the program</b> = no module has code, data, a reserved variable or an address used by an "
      "instruction there, and no data file of the disk is loaded there. Images to be moved (of <code>.logical</code> blocks), PRG fillers "
      "and module files (e.g. compressed, then unpacked elsewhere) count as free after use: <b>never used</b> excludes them too. Modules "
      "loaded in turn (overlays) are added up: every module card also gives the free space with only that module in memory. Static "
      "analysis: the limits are at the bottom of the page.</p></section>")

    # --- overview by pages: who uses every page (modules loaded in turn are shown side by side)
    w("<section><h2>Overview (256-byte pages)</h2><div class='legend'>")
    for m in used:
        w("<span><i style='background:%s'></i>%s</span>" % (col[m.name], E(m.name)))
    w("<span><i style='background:%s'></i>data files</span><span><i style='background:%s'></i>only images, fillers, module files</span>"
      "<span><i style='background:#4f9d4566'></i>free</span></div>" % (KCOL[DATA], KCOL[LOAD]))
    w("<div class='pages'><div></div>" + "".join("<div class='h'>%X</div>" % c for c in range(16)))
    for r in range(16):
        w("<div class='rh'>$%X000</div>" % r)
        for c in range(16):
            pg = r * 16 + c
            share, free, data, trans = {}, 0, 0, 0
            for a in range(pg * 256, pg * 256 + 256):
                o = occ.get(a, {})
                who = set()
                for k in (CODE, RES, REF):
                    who |= o.get(k, set())
                if who:
                    for x in who:
                        share[x] = share.get(x, 0) + 1.0 / len(who)
                elif DATA in o:
                    data += 1
                elif o:
                    trans += 1
                else:
                    free += 1
            tip = "$%02X00-$%02XFF  %s" % (pg, pg, sys_name(pg * 256)) + "".join("\n%s: %d B" % (x, round(v)) for x, v in sorted(share.items(), key=lambda kv: -kv[1])) + \
                  ("\ndata files: %d B" % data if data else "") + ("\nimages/fillers/module files: %d B" % trans if trans else "") + ("\nfree: %d B" % free if free else "")
            bars = "".join("<i style='flex:%.2f;background:%s'></i>" % (v, col[x]) for x, v in sorted(share.items()))
            bars += ("<i style='flex:%d;background:%s'></i>" % (data, KCOL[DATA]) if data else "") + ("<i style='flex:%d;background:%s'></i>" % (trans, KCOL[LOAD]) if trans else "")
            bars += "<i style='flex:%d;background:#4f9d4566'></i>" % free if free else ""
            w("<div class='pg%s' title='%s'>%s</div>" % (" sys" if pg < 4 else "", E(tip, True), bars))
    w("</div><p class='note'>Every cell is a page; the bars are proportional to the bytes of every module (code, data, variables, used "
      "addresses). Several colors in one page = modules that use it in turn. Hover a cell for the details. Dashed border: pages 0-3, of the system.</p></section>")

    # --- layers
    w("<section><h2>Layers by module</h2>")
    w(tracks(used, disk, occ, col))
    w("<p class='note'>Horizontal axis: address from $0000 to $FFFF. One row per module (code and data at the run address, reserved "
      "variables, images to be moved), then the disk files at their load address and the space free from the program. Hover a stretch "
      "for the details.</p></section>")

    # --- free space
    w("<section><h2>Space free from the program</h2><div class='wrap'><table><tr><th>From</th><th>To</th><th class='n'>Bytes</th><th>Bank</th>"
      "<th>Never used?</th></tr>")
    strict = {a for x, y, _ in frs for a in range(x, y)}
    for a, b, bank in sorted(fr):
        if b - a < 16:
            continue
        n_s = sum(1 for x in range(a, b) if x in strict)
        w("<tr><td class='mono'>%s</td><td class='mono'>%s</td><td class='n'>%d</td><td>%s</td><td class='mono'>%s</td></tr>" % (
            h4(a), h4(b - 1), b - a, E(bank), "yes" if n_s == b - a else "%d B of %d" % (n_s, b - a) if n_s else "no: " + E(", ".join(sorted(cover(occ, a, b))))))
    small = sum(b - a for a, b, _ in fr if b - a < 16)
    w("</table></div>" "<p class='note'>Stretches of at least 16 bytes; %d more free bytes in shorter stretches.</p></section>" % small)

    # --- run-time probe
    if pr:
        w(probe_html(pr, occ))

    # --- overlaps
    ov = overlaps(used)
    if ov:
        w("<section><h2>Modules in the same memory</h2><p class='note' style='margin-top:0'>Two modules that use the same addresses "
          "cannot be in memory together: normal for modules loaded in turn (overlays); otherwise it is a bug.</p>"
          "<details><summary>%d pairs of modules</summary><div class='wrap'><table><tr><th>Module</th><th>Module</th><th class='n'>Shared bytes</th><th>Areas</th></tr>" % len(ov))
        for a, b, rs in ov:
            w("<tr><td>%s</td><td>%s</td><td class='n'>%d</td><td class='mono'>%s</td></tr>" % (E(a), E(b), sum(y - x for x, y in rs),
              E(", ".join("%s-%s" % (h4(x), h4(y - 1)) for x, y in rs[:6]) + (" ..." if len(rs) > 6 else ""))))
        w("</table></div></details></section>")

    # --- modules
    w("<section><h2>Modules</h2>")
    for m in used:
        w(module_html(m, col[m.name], occ))
    if other:
        w("<h3>Other listings</h3><p class='note' style='margin-top:0'>Listings whose file is not on the disk (e.g. test variants): "
          "not counted in the free space. %s</p>" % E(", ".join("%s (%d B)" % (m.name, len(m.bytes)) for m in other)))
    w("</section>")

    # --- disk
    if disk:
        w(disk_html(disk, used, col))

    others = sorted(x for x in os.listdir(OUTDIR[0]) if x.endswith(".html") and x != "index.html") if OUTDIR[0] and os.path.isdir(OUTDIR[0]) else []
    if others:
        w("<section><h2>Other pages</h2><p class='note' style='margin-top:0'>In the same folder (written by other tools of the project): %s</p></section>" % ", ".join(
            "<a href='%s'>%s</a>" % (E(x, True), E(x)) for x in others))
    w("<section><h2>Limits</h2><ul class='note' style='margin:0;padding-left:18px'>"
      "<li>This is a <b>static</b> analysis: it sees what the assembler writes, not what the program does while it runs.</li>"
      "<li>Data copied or unpacked elsewhere (e.g. a compressed file) is seen only at its load address.</li>"
      "<li>Data that becomes useless after start-up (e.g. copied elsewhere at start-up) stays used.</li>"
      "<li>Buffers used only through pointers, and tables read with an index past their first byte, are not seen; the screen, unless "
      "it is declared with a reservation, is seen only through the addresses used directly.</li>"
      "<li>An address between $D000 and $DFFF used by the code counts as an I/O register, unless it is inside code or variables of the program.</li>"
      "<li>Run-time probe (if present): it sees only what the scenarios run; the test shortcuts (memory written by the monitor) count "
      "as written; a byte written with the same value as the pattern looks untouched (about 1 in 250 for data that is not $00, $FF, $20).</li>"
      "</ul></section></main></body></html>")
    return "\n".join(P)


def legend():
    items = [(KCOL[CODE], CODE), (KCOL[RES], RES), (KCOL[REF], REF), (KCOL[DATA], DATA + " (at its load address)"),
             (KCOL[IMG], "image to be moved (.logical)"), (KCOL[FILL], "PRG " + FILL), (KCOL[LOAD], LOAD + " (e.g. compressed)"), ("#4f9d4566", "free")]
    return "<div class='legend'>" + "".join("<span><i style='background:%s'></i>%s</span>" % (c, E(t)) for c, t in items) + "</div>"


def sys_name(a):
    for s, e, n, _ in SYSTEM:
        if s <= a <= e:
            return n
    return ""


def cover(occ, a, b):
    out = set()
    for x in range(a, b):
        for k, who in occ.get(x, {}).items():
            out |= {"%s %s" % (k, w_) for w_ in who}
    return out


def tracks(used, disk, occ, col):
    W, LH, X0 = 1200, 18, 150
    rows = []
    sc = lambda a: X0 + a * (W - X0 - 10) / 65536.0

    def bar(y, rs, color, tip_fn, opacity=1.0):
        out = []
        for a, b in rs:
            x0, x1 = sc(a), sc(b)
            out.append("<rect x='%.1f' y='%d' width='%.1f' height='%d' fill='%s' fill-opacity='%.2f'><title>%s</title></rect>" % (
                x0, y, max(1.0, x1 - x0), LH - 4, color, opacity, E(tip_fn(a, b))))
        return "".join(out)

    y = 22
    out = []
    # scale
    for k in range(0, 17):
        x = sc(k * 4096)
        out.append("<line x1='%.1f' y1='14' x2='%.1f' y2='%d' stroke='currentColor' stroke-opacity='.15'/>" % (x, x, 9999))
        if k < 16:
            out.append("<text x='%.1f' y='11' fill='currentColor' fill-opacity='.6'>$%X000</text>" % (x + 2, k))
    # system
    for s, e, n, note in SYSTEM:
        out.append("<rect x='%.1f' y='%d' width='%.1f' height='%d' fill='currentColor' fill-opacity='%s'><title>%s</title></rect>" % (
            sc(s), y, sc(e + 1) - sc(s) - 1, LH - 4, ".10" if "RAM" == n else ".22", E("%s-%s %s: %s" % (h4(s), h4(e), n, note))))
    out.append("<text x='4' y='%d' fill='currentColor'>C64 system</text>" % (y + 11))
    y += LH + 4
    for m in used:
        c = col[m.name]
        segs = ranges_of(m.bytes)
        tip = lambda a, b, m=m: "%s %s-%s (%d B): %s" % (m.name, h4(a), h4(b - 1), b - a, ", ".join(sorted({m.bytes[x] or "?" for x in range(a, b) if x in m.bytes}))[:300])
        out.append("<text x='4' y='%d' fill='currentColor'>%s</text>" % (y + 11, E(m.name[:18])))
        out.append(bar(y, segs, c, tip))
        vr = ranges_of({(a + i) & 0xFFFF for a, s, _, _ in m.virtual for i in range(s)})
        out.append(bar(y + 3, vr, KCOL[RES], lambda a, b, m=m: "%s variables %s-%s (%d B)" % (m.name, h4(a), h4(b - 1), b - a), .9))
        ir = ranges_of(m.image)
        out.append(bar(y + 6, ir, KCOL[IMG], lambda a, b, m=m: "%s image to be moved %s-%s (%d B) -> runs at %s" % (
            m.name, h4(a), h4(b - 1), b - a, h4(m.image.get(a, a))), .9))
        y += LH
    if disk:
        y += 4
        out.append("<text x='4' y='%d' fill='currentColor'>disk files</text>" % (y + 11))
        lanes = []
        for f in disk["files"]:
            if "load" not in f:
                continue
            for i, lane in enumerate(lanes):
                if all(f["load"] >= g["end"] or f["end"] <= g["load"] for g in lane):
                    lane.append(f); break
            else:
                lanes.append([f])
        for lane in lanes:
            for f in lane:
                out.append(bar(y, [(f["load"], min(f["end"], 0x10000))], KCOL[LOAD], lambda a, b, f=f: "%s %s-%s (%d B)%s" % (
                    f["name"], h4(a), h4(b - 1), b - a, (", modules: " + ", ".join(f["modules"])) if f.get("modules") else
                    (", from the build: " + f["built"]) if f.get("built") else "")))
                out.append("<rect x='%.1f' y='%d' width='1' height='%d' fill='currentColor' fill-opacity='.5'/>" % (sc(f["load"]), y, LH - 4))
            y += LH - 6
        y += 6
    rr = ranges_of(a for a, o in occ.items() if REF in o and len(o) == 1)
    out.append("<text x='4' y='%d' fill='currentColor'>used by the code</text>" % (y + 11))
    out.append(bar(y, rr, "#c99a00", lambda a, b: "%s-%s (%d B) used by: %s" % (h4(a), h4(b - 1), b - a, ", ".join(sorted({w for x in range(a, b) for w in occ[x][REF]})))))
    y += LH
    out.append("<text x='4' y='%d' fill='currentColor'>free</text>" % (y + 11))
    out.append(bar(y, [(a, b) for a, b, _ in free_ranges(occ)], "#4f9d45", lambda a, b: "free %s-%s (%d B)" % (h4(a), h4(b - 1), b - a)))
    y += LH + 4
    svg = "".join(out).replace("y2='9999'", "y2='%d'" % y)
    return "<div class='wrap'><svg class='tracks' viewBox='0 0 %d %d' style='min-width:900px'>%s</svg></div>" % (W, y, svg)


def module_html(m, color, occ):
    P = []
    w = P.append
    own = {}
    for a, o in occ.items():                     # only this module and the data files
        k = {x: v for x, v in o.items() if (m.name in v and x in (CODE, RES, REF, IMG, FILL)) or x == DATA}
        if k:
            own[a] = k
    fm = free_ranges(own)
    segs = ranges_of(m.bytes)
    vbytes = sum(s for _, s, _, _ in m.virtual)
    w("<h3><span style='display:inline-block;width:12px;height:12px;background:%s;margin-right:8px'></span>%s</h3>" % (color, E(m.name)))
    w("<div class='mono dim'>listing %s · output %s · on the disk: %s (%s)</div>" % (E(os.path.basename(m.lst)), E(m.output or "?"),
      E(", ".join(m.disk) or "no"), E(m.link)))
    w("<div class='kv' style='margin-top:8px'><div><b>%d B</b><span>code and data</span></div><div><b>%d B</b><span>reserved variables (%d)</span></div>"
      "<div><b>%d</b><span>contiguous stretches</span></div><div><b>%d B</b><span>images to be moved</span></div><div><b>%d B</b><span>filler</span></div>"
      "<div><b>%d B</b><span>free with only this module (and the data files)</span></div></div>" % (
          len(m.bytes), vbytes, len(m.virtual), len(segs), len(m.image), len(m.filler), sum(b - a for a, b, _ in fm)))
    w("<div class='mono'>%s</div>" % E(" · ".join("%s-%s" % (h4(a), h4(b - 1)) for a, b in segs[:16]) + (" ..." if len(segs) > 16 else "")))
    # source files
    per = {}
    for a, f in m.bytes.items():
        per.setdefault(f or "?", []).append(a)
    w("<details><summary>Source files (%d)</summary><div class='wrap'><table><tr><th>File</th><th class='n'>Bytes</th><th>Addresses</th></tr>" % len(per))
    for f, al in sorted(per.items(), key=lambda x: -len(x[1])):
        rs = ranges_of(al)
        w("<tr><td class='mono'>%s</td><td class='n'>%d</td><td class='mono'>%s</td></tr>" % (E(f), len(al),
          E(", ".join("%s-%s" % (h4(a), h4(b - 1)) for a, b in rs[:5]) + (" ..." if len(rs) > 5 else ""))))
    w("</table></div></details>")
    if m.virtual:
        w("<details><summary>Reserved variables (%d, %d B)</summary><div class='wrap'><table><tr><th>Address</th><th>Name</th><th class='n'>Bytes</th><th>File</th></tr>" % (len(m.virtual), vbytes))
        for a, s, lab, f in sorted(m.virtual):
            w("<tr><td class='mono'>%s</td><td class='mono'>%s</td><td class='n'>%d</td><td class='mono dim'>%s</td></tr>" % (h4(a), E(lab), s, E(f or "")))
        w("</table></div></details>")
    # zero page, I/O, KERNAL
    zp = sorted(a for a in m.refs if a < 0x100)
    zpres = {(a + i) for a, s, _, _ in m.virtual for i in range(s) if a < 0x100}
    io = {}
    for a, k in m.refs.items():
        n = io_name(a)
        if n and a not in m.bytes and a not in zpres:
            io.setdefault(n, {}).setdefault(a, set()).update(k)
    ker = sorted(a for a in m.refs if a in KERNAL)
    names = {v: k for k, v in m.labels.items()}
    w("<details><summary>Zero page, I/O, KERNAL</summary>")
    w("<p class='mono' style='margin:6px 0'>zero page used by the code (%d B): %s</p>" % (len(zp), E(", ".join("%s-%s" % ("$%02X" % a, "$%02X" % (b - 1)) if b - a > 1 else "$%02X" % a for a, b in ranges_of(zp)))))
    for chip, regs in sorted(io.items()):
        w("<p class='mono' style='margin:4px 0'>%s: %s</p>" % (E(chip), E(", ".join("%s%s(%s)" % (h4(a), " " + names[a] if a in names else "", "".join(sorted(k - {"i", "p"})) or "r") for a, k in sorted(regs.items())))))
    if ker:
        w("<p class='mono' style='margin:4px 0'>KERNAL: %s</p>" % E(", ".join("%s %s" % (KERNAL[a], h4(a)) for a in ker)))
    w("</details>")
    big = sorted(fm, key=lambda r: -(r[1] - r[0]))[:8]
    w("<details><summary>Free space with only this module</summary><p class='mono' style='margin:6px 0'>%s</p></details>" % E(
        ", ".join("%s-%s %d B (%s)" % (h4(a), h4(b - 1), b - a, k) for a, b, k in sorted(big))))
    return "".join(P)


def disk_html(disk, used, col):
    P = []
    w = P.append
    fcol = {}
    for i, f in enumerate(disk["files"]):
        mm = f.get("modules")
        fcol[i] = col.get(mm[0]) if mm else PALETTE[(i + 7) % len(PALETTE)]
    w("<section><h2>Disk</h2><div class='kv'><div><b>%s</b><span>name, ID %s</span></div><div><b>%d</b><span>files</span></div>"
      "<div><b>%d / %d</b><span>free blocks (BAM)</span></div><div><b>%d</b><span>tracks</span></div></div>" % (
          E(disk["name"]), E(disk["id"]), len(disk["files"]), disk["free"], disk["total"], disk["tracks"]))
    spt = disk["spt"]
    w("<div class='wrap'><div class='grid' style='grid-template-columns:30px repeat(21,minmax(14px,1fr));min-width:520px'>")
    w("<div></div>" + "".join("<div class='dim' style='text-align:center'>%d</div>" % s for s in range(21)))
    for t in range(1, disk["tracks"] + 1):
        w("<div class='dim' style='text-align:right;padding-right:3px'>%d</div>" % t)
        for s in range(21):
            if s >= spt(t):
                w("<div></div>"); continue
            o = disk["owner"].get((t, s))
            if o == "dir":
                c, tip = "#2a2118", "track %d sector %d: directory and BAM" % (t, s)
            elif o is None:
                free = (t, s) in disk["free_bam"]
                c, tip = ("#4f9d4566" if free else "#e0301e"), "track %d sector %d: %s" % (t, s, "free" if free else "used in the BAM but by no file")
            else:
                f = disk["files"][o]
                c, tip = fcol[o], "track %d sector %d: %s (block %d of %d)" % (t, s, f["name"], f["chain"].index((t, s)) + 1, len(f["chain"]))
            w("<div class='s' style='background:%s' title='%s'></div>" % (c, E(tip, True)))
    w("</div></div>")
    w("<h3>Directory</h3><div class='wrap'><table><tr><th>#</th><th>Name</th><th>Type</th><th class='n'>Blocks</th><th>Loaded at</th>"
      "<th>First block</th><th class='n'>Fragments</th><th>Comes from</th></tr>")
    for i, f in enumerate(disk["files"]):
        frag = 1 + sum(1 for (a, b) in zip(f["chain"], f["chain"][1:]) if b[0] != a[0])
        src = ("modules: " + ", ".join(f["modules"])) if f.get("modules") else ("build: " + f["built"]) if f.get("built") else ""
        w("<tr><td class='n'>%d</td><td class='mono'><span style='display:inline-block;width:10px;height:10px;background:%s;margin-right:6px'></span>%s</td>"
          "<td>%s</td><td class='n'>%d</td><td class='mono'>%s</td><td class='mono'>%d/%d</td><td class='n'>%d</td><td class='mono dim'>%s</td></tr>" % (
              i + 1, fcol[i], E(f["name"]), f["type"], f["blocks"], ("%s-%s" % (h4(f["load"]), h4(f["end"] - 1))) if "load" in f else
              ("elsewhere (file says %s)" % h4(f["fake_load"])) if "fake_load" in f else "",
              f["chain"][0][0] if f["chain"] else 0, f["chain"][0][1] if f["chain"] else 0, frag, E(src)))
    w("</table></div><p class='note'>Fragments = stretches on different tracks. \"Comes from\": module with the listing, or build file with "
      "the same content.</p></section>")
    return "".join(P)


OUTDIR = [None]


# ------------------------------------------------------------------ main
def project_title():
    p = os.path.join(ROOT, "toolchain.env")
    if os.path.isfile(p):
        x = re.search(r'^C64_VIEW_TITLE="([^"]*)"', open(p).read(), re.M)
        if x:
            return x.group(1)
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--work", default="out/work", help="folder with *.lst, *.lbl, *.prg (default out/work)")
    ap.add_argument("--disk", default="out/work/disk.d64", help=".d64 disk (default out/work/disk.d64)")
    ap.add_argument("--out", default="out/work/memory-map", help="output folder (default out/work/memory-map)")
    ap.add_argument("--title", default=None, help="project name (default: C64_VIEW_TITLE of toolchain.env)")
    ap.add_argument("--probe", default=None, help="RAM dumps of the run-time probe in VICE (default out/work/memprobe if it exists)")
    a = ap.parse_args()
    used, other, disk = analyse(a.work, a.disk)
    if not used:
        sys.exit("c64map: no 64tass listing (*.lst, option -L) in %s" % a.work)
    occ = layers(used, disk)
    os.makedirs(a.out, exist_ok=True)
    OUTDIR[0] = a.out
    title = a.title if a.title is not None else project_title()
    pdir = a.probe if a.probe is not None else os.path.join(a.work, "memprobe")
    pr = probe_data(pdir, a.disk if disk else None)
    open(os.path.join(a.out, "index.html"), "w").write(page_html(used, other, disk, occ, title, pr))
    fr = free_ranges(occ)
    data = {"schema": 1, "free_bytes": sum(b - a for a, b, _ in fr),
            "free_by_bank": {bank: sum(y - x for x, y, k in fr if k == bank) for _, _, bank in BANKS},
            "free_ranges": [{"from": a, "to": b - 1, "bank": k} for a, b, k in fr],
            "never_used_bytes": sum(b - a for a, b, _ in free_ranges(occ, strict=True)),
            "modules": [{"name": m.name, "listing": os.path.basename(m.lst), "output": m.output, "disk": m.disk, "link": m.link,
                         "bytes": len(m.bytes), "reserved": sum(s for _, s, _, _ in m.virtual), "segments": [[x, y - 1] for x, y in ranges_of(m.bytes)]}
                        for m in used],
            "other_listings": [m.name for m in other]}
    data["metrics"] = [{"id": "ram_free_static", "label": "RAM free from the program (static)", "value": data["free_bytes"], "unit": "B",
                        "better": "up", "hint": "toolchain/memmap: $0400-$FFFF with no code, data, variables or data files"}]
    if pr and pr.get("run"):
        nv = probe_ranges(pr["never"])
        data["probe"] = {"dumps": pr["dumps"], "ignored": pr["ignored"], "never_written_bytes": len(pr["never"]),
                         "never_written_by_bank": {bank: sum(y - x for x, y, k in nv if k == bank) for _, _, bank in BANKS},
                         "never_written_ranges": [{"from": x, "to": y - 1, "bank": k} for x, y, k in nv],
                         "scenarios": [{"tag": t, "written": n} for t, n in pr["scenarios"]]}
        data["metrics"].append({"id": "ram_never_written", "label": "RAM never written in the tests (VICE)", "value": len(pr["never"]),
                                "unit": "B", "better": "up", "hint": "run-time probe, %d VICE sessions" % pr["dumps"]})
    elif pr:
        data["probe"] = {"dumps": 0, "ignored": pr["ignored"]}
    if disk:
        data["disk"] = {"name": disk["name"], "id": disk["id"], "blocks_free": disk["free"], "blocks_total": disk["total"],
                        "files": [{"name": f["name"], "type": f["type"], "blocks": f["blocks"], "load": f.get("load"), "end": (f["end"] - 1) if "end" in f else None,
                                   "modules": f.get("modules", []), "built": f.get("built")} for f in disk["files"]]}
    json.dump(data, open(os.path.join(a.out, "memmap.json"), "w"), indent=1)
    print("c64map: %s (%d modules, %d B free from the program%s%s)" % (os.path.join(a.out, "index.html"), len(used), data["free_bytes"],
          ", disk %d/%d blocks free" % (disk["free"], disk["total"]) if disk else "",
          ", probe: %d B never written in %d VICE sessions" % (len(pr["never"]), pr["dumps"]) if pr and pr.get("run") else ""))


if __name__ == "__main__":
    main()
