#!/usr/bin/env python3
"""File di prova del prototipo audio (13/11): tone.wav (1 kHz, 0,5 s, stereo 44,1 kHz) e sidtone.prg (tono continuo del SID:
BASIC "10 SYS2061" + volume 15, voce 1 a ~1 kHz, triangolo + gate, ciclo infinito). Scrive nella cartella corrente."""
import math, struct, wave
fr = 44100; n = int(fr * 0.5)
w = wave.open('tone.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(fr)
w.writeframes(b''.join(struct.pack('<hh', v, v) for v in (int(12000 * math.sin(2 * math.pi * 1000 * i / fr)) for i in range(n))))
w.close()
code = bytes([0xA9, 0x0F, 0x8D, 0x18, 0xD4, 0xA9, 0x00, 0x8D, 0x05, 0xD4, 0xA9, 0xF0, 0x8D, 0x06, 0xD4, 0xA9, 0x25, 0x8D, 0x00, 0xD4,
              0xA9, 0x11, 0x8D, 0x01, 0xD4, 0xA9, 0x11, 0x8D, 0x04, 0xD4, 0x4C, 0x2B, 0x08])
stub = bytes([0x0B, 0x08, 0x0A, 0x00, 0x9E]) + b'2061' + bytes([0, 0, 0])
open('sidtone.prg', 'wb').write(bytes([0x01, 0x08]) + stub + code)
