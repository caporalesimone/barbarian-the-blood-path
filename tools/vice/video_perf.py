#!/usr/bin/env python3
"""(19/11, TODO D5) Real-time videos of the game in VICE, to SEE the lost frames: one PNG per PAL frame of the C64 (50 per
emulated second, screenshot on the raster IRQ at line 250, when the frame on screen is complete), joined at 50 fps with ffmpeg:
the video runs at the speed of a real C64. When the main loop is late the picture does not change for one or more video frames
(the scroll jerks): that is the lost frame.

The hero walks (the policy of PERF-21: a direction until he stops, then the next one; input written at the rts of read_input as
in the tests), god mode on. Under the picture a caption: level, segment, game frames per second over the last second (50 = no
loss) and the lost frames of the segment (a frame of the main loop longer than 1.5 PAL frames, as in tests/regression/perf).

Segments (level 1 and level 14): walking, walking among the monsters, then Frenzy among the monsters with the run at +25%, +50%, +100% (fz_run; the timer
of the Frenzy kept on). Output: out/work/video/perf_level01.mp4, perf_level14.mp4 (+ a summary in perf_summary.txt).
Usage (container lab64-tools): lab64 run python3 tools/vice/video_perf.py [--seconds S]   (S = seconds per segment, default 6)"""
import os, re, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib.c64 import Game, FRAME, listing  # noqa: E402
from lib.play import new_game, go_level, alive, mpos, floor_next, U, D, LF, RT  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

SEC = float(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else 6.0
OUTD = os.path.join(ROOT, "out", "work", "video")
DIRS = (RT, D, LF, U, RT | D, LF | U, RT | U, LF | D)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SCALE = 2


def p2_addr():
    """the raster IRQ phase 2 (line 250, src/game/hud.asm irq_h _p2): the frame on screen is complete"""
    m = re.search(r"^\.([0-9a-f]{4})\s.*_p2\s+lda ap_d018", listing("game"), re.M)
    return int(m.group(1), 16)


class Rec:
    def __init__(self, g, tag):
        self.g, self.L, self.tag = g, g.L, tag
        self.p2 = p2_addr()
        self.dir = os.path.join(OUTD, "frames_" + tag)
        shutil.rmtree(self.dir, ignore_errors=True); os.makedirs(self.dir)
        self.n = 0                                  # video frames
        self.reads = []                             # video frame index of each read of the input (one per game frame)
        self.rows = []

    def segment(self, name, seconds, frenzy=None, monsters=False):
        g, L = self.g, self.L
        if monsters:                                # next to a monster (the closest group): Frenzy among the monsters
            m = alive(g)
            best = max(m, key=lambda i: sum(1 for j in m if abs(mpos(g, i)[0] - mpos(g, j)[0]) + abs(mpos(g, i)[1] - mpos(g, j)[1]) < 8))
            p = floor_next(g, *mpos(g, best))
            g.teleport(p[0], p[1]); g.frames(2)
        g.poke(L["fz_run"], frenzy or 0)
        g.poke(L["tmr"] + L["T_FZ"], 250 if frenzy else 0, 0)
        if not g.at_input:
            g.frames(1)
        g.brk(self.p2)                              # (the stop on the rts of read_input is already set by frames())
        k, still, last, n0 = 0, 0, None, self.n
        c_prev, durs, reads0 = g.last, [], len(self.reads)
        while self.n - n0 < seconds * 50:
            c = g.go(30)
            pc = g.regs()["pc"]
            if pc == self.p2:
                f = os.path.join(self.dir, "s%05d.png" % self.n)
                g.screenshot(f)
                self.cap.append((self.n, name, frenzy))
                self.n += 1
                continue
            # read of the input: one game frame done
            self.reads.append(self.n)
            if c and c_prev: durs.append(c - c_prev)
            c_prev = c
            pos = (g.w16(L["px"]), g.w16(L["py"]))
            still = still + 1 if pos == last else 0
            last = pos
            if still >= 4: k += 1; still = 0
            j = DIRS[k % len(DIRS)]
            g.poke(L["joy"], j); g.poke(L["joynew"], 0)
            if frenzy:
                g.poke(L["tmr"] + L["T_FZ"], 250, 0); g.poke(L["fz_run"], frenzy)
        g.delbrk(); g.brk(g.RI); g.last = c_prev
        durs = durs[1:]
        lost = sum(1 for d in durs if d > 1.5 * FRAME)
        fps = 50.0 * (len(self.reads) - reads0) / max(1, self.n - n0)
        self.rows.append((self.tag, name, len(durs), lost, 100.0 * lost / max(1, len(durs)), fps))
        self.seg_lost[name] = 100.0 * lost / max(1, len(durs))
        print("  %s %-24s game frames %4d, lost %3d (%.1f%%), %.1f game fps" % self.rows[-1])

    def run(self, segs):
        self.cap, self.seg_lost = [], {}
        for s in segs: self.segment(*s)
        self.compose()

    def compose(self):
        """caption under every picture, then ffmpeg (50 fps, H.264)"""
        font = ImageFont.truetype(FONT, 18)
        small = ImageFont.truetype(FONT, 14)
        reads = self.reads
        cnt = [0] * (self.n + 1)                    # game frames ending in each video frame
        for r in reads:
            if r <= self.n: cnt[min(r, self.n)] += 1
        acc = 0
        win = []
        for i, name, fz in self.cap:
            src = os.path.join(self.dir, "s%05d.png" % i)
            im = Image.open(src).convert("RGB")
            w, h = im.size
            im = im.resize((w * SCALE, h * SCALE), Image.NEAREST)
            out = Image.new("RGB", (w * SCALE, h * SCALE + 56), (0, 0, 0))
            out.paste(im, (0, 0))
            win.append(cnt[i]); win = win[-50:]
            fps = sum(win) * 50.0 / len(win)
            d = ImageDraw.Draw(out)
            col = (90, 230, 90) if fps >= 48 else (240, 200, 60) if fps >= 40 else (240, 80, 80)
            d.text((10, h * SCALE + 6), "%s  %s" % (self.title, name), font=font, fill=(230, 230, 230))
            d.text((10, h * SCALE + 30), "game fps (last second): %4.1f / 50    lost frames in this segment: %.1f%%" %
                   (fps, self.seg_lost[name]), font=small, fill=col)
            out.save(src.replace("s%05d" % i, "c%05d" % i))
        mp4 = os.path.join(OUTD, "perf_%s.mp4" % self.tag)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "50", "-i", os.path.join(self.dir, "c%05d.png"),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", mp4], check=True)
        print("  -> %s (%d frames, %.1f s)" % (mp4, self.n, self.n / 50.0))


def main():
    os.makedirs(OUTD, exist_ok=True)
    g = Game()
    rows = []
    try:
        g.to_menu(); new_game(g)
        L = g.L
        g.poke(L["godmode"], 1); g.frames(5)
        for lv in (1, 14):
            if lv == 1:
                go_level(g, 1)
            else:
                g.call_keep(L["change_level"], regs="a=%02x,x=00" % lv, tmax=150); g.frames(2)
            r = Rec(g, "level%02d" % lv)
            r.title = "Level %d" % lv
            r.run([("walk", SEC), ("walk among the monsters", SEC, None, True), ("Frenzy run +25%", SEC, 25, False), ("Frenzy run +50%", SEC, 50, False),
                   ("Frenzy run +100%", SEC, 100, False)])
            rows += r.rows
    finally:
        g.close()
    with open(os.path.join(OUTD, "perf_summary.txt"), "w") as f:
        for row in rows: f.write("%s %-24s game frames %4d, lost %3d (%.1f%%), %.1f game fps\n" % row)


if __name__ == "__main__":
    main()
