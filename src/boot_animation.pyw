"""Welcome back Alex - startup splash.

Fast slash animation with a software-style interface layer in a midnight
blue and cyan palette. Runs full screen for about 3 seconds after sign-in,
then the blades slice open onto the desktop. Dark Hour opens with the
midnight clock ticking over and shattering (3 s longer). Modes: AUTO (Dark Hour between
midnight and 1am), DARK, P5 and NORMAL, set with toggle_mode.pyw. Any key or click skips to the exit.
"""
import os
import sys

# pythonw has no console, so write any error to splash_error.log beside this script
_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "splash_error.log")
if sys.stderr is None:
    try:
        sys.stderr = open(_LOG, "w", encoding="utf-8")
        sys.stderr.write("splash started with " + sys.executable + "\n")
        sys.stderr.flush()
    except OSError:
        pass

import ctypes
import math
import platform
import random
import shutil
import sys
import time

# ---- Settings ---------------------------------------------------------
DURATION = 3.0
IMPACT = 0.95                # moment ALEX lands
CLOSE_START, CLOSE_END, OPEN_START = 2.35, 2.55, 2.7
NAME = "ALEX"
PHRASES = ["MEMENTO MORI", "SYSTEM ONLINE", "TIME NEVER WAITS", "STAY SHARP", "SEIZE THE DAY"]
DISPLAY_FONT = "Impact"      # ships with Windows
MONO_FONT = "Consolas"       # ships with Windows
NORMAL = ("#03081a", "#071433", "#1c5fd6", "#4fd8ff", "#eef7ff")
DARK_HOUR = ("#020803", "#06170c", "#2e7d3c", "#c4ff5e", "#effee0")
P5 = ("#0b0b0b", "#d10a1f", "#7a0010", "#111111", "#ffffff")
KEY = "#010203"              # see-through colour used to reveal the desktop
GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/<>_"
# -----------------------------------------------------------------------

def read_mode():
    """Mode comes from --dark / --p5 / --normal / --auto, else splash_mode.txt beside this script."""
    for arg in sys.argv[1:]:
        if arg.lower() in ("--dark", "--p5", "--normal", "--auto"):
            return arg.lower()[2:]
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "splash_mode.txt")
        with open(path, encoding="utf-8") as f:
            value = f.read().strip().lower()
        if value in ("auto", "dark", "p5", "normal"):
            return value
    except OSError:
        pass
    return "auto"

MODE = read_mode()
DARK_MODE = MODE == "dark" or (MODE == "auto" and time.localtime().tm_hour == 0)
P5_MODE = MODE == "p5"
NIGHT, BG, BLUE, CYAN, ICE = DARK_HOUR if DARK_MODE else P5 if P5_MODE else NORMAL
BG_TICKER = "TAKE YOUR TIME  " if P5_MODE else "BURN MY DREAD  "

def clamp(v):
    return max(0.0, min(1.0, v))

def ease_out(u):
    return 1 - (1 - u) ** 3

def ease_in(u):
    return u ** 3

def mix(a, b, t):
    t = clamp(t)
    A = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    B = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(A, B))

def hrand(n):
    x = math.sin(n * 12.9898) * 43758.5453
    return x - math.floor(x)

def scramble(s, t, t0, per):
    """Text that decodes from random glyphs, one character at a time."""
    out = []
    for i, ch in enumerate(s):
        if ch == " ":
            out.append(" ")
            continue
        at = t0 + i * per
        if t >= at:
            out.append(ch)
        elif t >= at - 0.25:
            out.append(GLYPHS[(int(t * 40) * 7 + i * 13) % len(GLYPHS)])
    return "".join(out).rstrip()

_seed = 7
def _rand():
    global _seed
    _seed = (_seed * 9301 + 49297) % 233280
    return _seed / 233280
J = [_rand() for _ in range(128)]

# ---- Real system readings (with safe fallbacks) -----------------------
def read_uptime():
    try:
        k32 = ctypes.windll.kernel32
        k32.GetTickCount64.restype = ctypes.c_ulonglong
        s = int(k32.GetTickCount64() // 1000)
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
    except Exception:
        return "--:--:--"

def read_power():
    class SPS(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                    ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_byte),
                    ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
    try:
        s = SPS()
        ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
        if (s.BatteryFlag & 0xFF) == 128 or s.BatteryLifePercent == 255:
            return "AC POWER"
        return f"{s.BatteryLifePercent}%"
    except Exception:
        return "AC POWER"

def read_perf_mode():
    """Windows power mode slider: Best power efficiency / Balanced / Best performance."""
    names = {
        "961cc777-2547-4f9d-8174-7d86181b8a7a": "EFFICIENCY",
        "3af9b8d9-7c97-431d-ad78-34a8bfea439f": "BETTER BATTERY",
        "00000000-0000-0000-0000-000000000000": "BALANCED",
        "ded574b5-45a0-4f42-8737-46345c09c238": "BEST PERFORMANCE",
    }
    try:
        import winreg
        guid = ctypes.create_string_buffer(16)
        if ctypes.windll.powrprof.PowerGetEffectiveOverlayScheme(guid) == 0:
            b = guid.raw
            g = "%08x-%04x-%04x-%s-%s" % (int.from_bytes(b[0:4], "little"), int.from_bytes(b[4:6], "little"),
                                          int.from_bytes(b[6:8], "little"), b[8:10].hex(), b[10:16].hex())
            return names.get(g, "CUSTOM")
    except Exception:
        pass
    try:
        import winreg
        on_ac = read_power() == "AC POWER" or _on_ac()
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes")
        value, _ = winreg.QueryValueEx(key, "ActiveOverlayAcPowerScheme" if on_ac else "ActiveOverlayDcPowerScheme")
        return names.get(str(value).lower(), "CUSTOM")
    except Exception:
        return "BALANCED"

def _on_ac():
    class SPS(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                    ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_byte),
                    ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
    s = SPS()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    return s.ACLineStatus == 1

def read_disk():
    try:
        drive = os.environ.get("SystemDrive", "C:")
        free = shutil.disk_usage(drive + "\\").free / 1e9
        return f"{drive} {free:.0f} GB FREE"
    except Exception:
        return "OK"

def read_sysinfo():
    name = (platform.node() or "PC").upper()
    try:
        build = sys.getwindowsversion().build
        win = "WINDOWS 11" if build >= 22000 else "WINDOWS 10"
        return f"{name} · {win} · BUILD {build}"
    except AttributeError:
        return f"{name} · {platform.system().upper()}"

hour = time.localtime().tm_hour
if DARK_MODE:
    LINE1 = "THE DARK HOUR"
elif 5 <= hour < 12:
    LINE1 = "GOOD MORNING"
elif 12 <= hour < 17:
    LINE1 = "GOOD AFTERNOON"
elif 17 <= hour < 23:
    LINE1 = "GOOD EVENING"
else:
    LINE1 = "WELCOME BACK"
LINE1_SPACED = " ".join(LINE1)
BAND_TEXT = ("MEMENTO MORI" if DARK_MODE else "LIFE WILL CHANGE" if P5_MODE else random.choice(PHRASES)) + "  //  "
CLOCK = "00:00" if DARK_MODE else time.strftime("%H:%M")
DATE_TAG = time.strftime("%a %d %b %Y").upper()
SYSINFO = read_sysinfo()
READOUT = [("USER", "ALEX"), ("AUTH", "VERIFIED"), ("UPTIME", read_uptime()),
           ("POWER", read_power()), ("MODE", read_perf_mode()), ("DISK", read_disk()),
           ("SESSION", "DARK HOUR" if DARK_MODE else "SHOWTIME" if P5_MODE else "STARTING")]

# ---- Window (pygame) --------------------------------------------------
# Use real pixels so the splash lines up with the screen at any display scaling
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "0,0")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

pygame.init()
SW, SH = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode((SW, SH), pygame.NOFRAME)
pygame.display.set_caption("Startup splash")
pygame.mouse.set_visible(False)
SW, SH = screen.get_size()
# Very high-resolution screens draw at about 1080p detail and scale up, to keep the frame rate smooth
RENDER_SCALE = min(1.0, math.sqrt(1920 * 1200 / (SW * SH)))
W, H = int(SW * RENDER_SCALE), int(SH * RENDER_SCALE)
target = screen if RENDER_SCALE >= 1.0 else pygame.Surface((W, H)).convert()

COLOURS = {}
def rgb(c):
    if c not in COLOURS:
        COLOURS[c] = pygame.Color(c)
    return COLOURS[c]

# Desktop reveal and fades use a Windows layered window: KEY pixels show the desktop through
SEE_THROUGH = False
_hwnd = None
_KEYREF = int(KEY[5:7], 16) << 16 | int(KEY[3:5], 16) << 8 | int(KEY[1:3], 16)
try:
    _u32 = ctypes.windll.user32
    _hwnd = pygame.display.get_wm_info()["window"]
    _GWL_EXSTYLE, _WS_EX_LAYERED, _WS_EX_TOPMOST = -20, 0x00080000, 0x00000008
    _u32.SetWindowLongW(_hwnd, _GWL_EXSTYLE, _u32.GetWindowLongW(_hwnd, _GWL_EXSTYLE) | _WS_EX_LAYERED)
    _u32.SetLayeredWindowAttributes(_hwnd, _KEYREF, 255, 0x1 | 0x2)
    _u32.SetWindowPos(_hwnd, -1, 0, 0, SW, SH, 0x0040)   # topmost, shown
    _u32.SetForegroundWindow(_hwnd)
    SEE_THROUGH = True
except Exception:
    pass

_alpha_now = [1.0]
def set_window_alpha(a):
    a = max(0.0, min(1.0, a))
    if abs(a - _alpha_now[0]) < 0.004 or _hwnd is None:
        return
    _alpha_now[0] = a
    try:
        _u32.SetLayeredWindowAttributes(_hwnd, _KEYREF, int(a * 255), 0x1 | 0x2)
    except Exception:
        pass


FONT_FILES = {}
def _font_file(family):
    if family not in FONT_FILES:
        FONT_FILES[family] = pygame.font.match_font(family.replace(" ", "").lower())
    return FONT_FILES[family]


class Font:
    """Stand-in for a Tk font: a pygame font at a pixel size, with measure()."""
    def __init__(self, family, px, weight):
        self.key = (family, px, weight)
        path = _font_file(family)
        self.pg = pygame.font.Font(path, px) if path else pygame.font.SysFont(None, px)
        if weight == "bold" and not (path and "bd" in os.path.basename(path).lower()):
            self.pg.set_bold(True)

    def measure(self, s):
        return self.pg.size(s)[0]


FONTS = {}
def font(family, px, weight="normal"):
    # Sizes snap to 3% steps so animated text reuses cached renders
    px = max(6, int(round(1.03 ** round(math.log(max(6, px)) / math.log(1.03)))))
    key = (family, px, weight)
    if key not in FONTS:
        FONTS[key] = Font(family, px, weight)
    return FONTS[key]


class Canvas:
    """Immediate-mode stand-in for the Tk canvas calls the animation uses."""
    def __init__(self, surf):
        self.s = surf
        self.bg = BG
        self.text_cache = {}
        self.scan = None
        self.scan_visible = True

    @staticmethod
    def _pts(args):
        flat = []
        for a in args:
            if isinstance(a, (list, tuple)):
                flat.extend(a)
            else:
                flat.append(a)
        return [(flat[i], flat[i + 1]) for i in range(0, len(flat) - 1, 2)]

    def delete(self, _tag=None):
        self.s.fill(rgb(self.bg))

    def configure(self, bg=None):
        if bg:
            self.bg = bg

    def build_scanlines(self, gap):
        surf = pygame.Surface((W, H))
        surf.fill((255, 0, 255))
        for y in range(0, H, gap):
            pygame.draw.line(surf, rgb(NIGHT), (0, y), (W, y))
        surf.set_colorkey((255, 0, 255), pygame.RLEACCEL)
        surf.set_alpha(150, pygame.RLEACCEL)
        self.scan = surf.convert()
        self.scan.set_colorkey((255, 0, 255), pygame.RLEACCEL)
        self.scan.set_alpha(150, pygame.RLEACCEL)

    def tag_raise(self, _tag=None):
        if self.scan is not None and self.scan_visible:
            self.s.blit(self.scan, (0, 0))

    def itemconfigure(self, _tag, state=None):
        self.scan_visible = state != "hidden"

    def create_polygon(self, *args, fill=None, outline="", tags=None, width=1):
        pts = self._pts(args)
        if len(pts) >= 3 and fill:
            pygame.draw.polygon(self.s, rgb(fill), pts)

    def create_line(self, *args, fill=None, width=1, capstyle=None, tags=None):
        pts = self._pts(args)
        if len(pts) < 2 or not fill:
            return
        w = max(1, int(round(width)))
        col = rgb(fill)
        if len(pts) == 2:
            pygame.draw.line(self.s, col, pts[0], pts[1], w)
        else:
            pygame.draw.lines(self.s, col, False, pts, w)
        if capstyle == "round" and w >= 3:
            for p in (pts[0], pts[-1]):
                pygame.draw.circle(self.s, col, p, w / 2)

    def create_rectangle(self, x0, y0, x1, y1, fill=None, outline="", tags=None):
        if fill:
            r = pygame.Rect(int(min(x0, x1)), int(min(y0, y1)), int(abs(x1 - x0)) + 1, int(abs(y1 - y0)) + 1)
            self.s.fill(rgb(fill), r)

    def create_oval(self, x0, y0, x1, y1, fill=None, outline="", width=1, tags=None):
        r = pygame.Rect(int(min(x0, x1)), int(min(y0, y1)), max(1, int(abs(x1 - x0))), max(1, int(abs(y1 - y0))))
        if fill:
            pygame.draw.ellipse(self.s, rgb(fill), r)
        if outline:
            pygame.draw.ellipse(self.s, rgb(outline), r, max(1, int(round(width))))

    def scaled_text(self, x, y, text, fill, family, weight, base_px, scale, angle=0.0, alpha=1.0):
        """Big animated text: render once, rotate once, then just resize and fade the image."""
        if alpha <= 0.01 or scale <= 0:
            return
        key = ("big", text, family, weight, int(base_px), fill, round(angle))
        base = self.text_cache.get(key)
        if base is None:
            f = font(family, base_px, weight)
            base = f.pg.render(text, True, rgb(fill))
            if round(angle):
                base = pygame.transform.rotate(base, round(angle))
            base = base.convert_alpha()
            self.text_cache[key] = base
        bw, bh = base.get_size()
        sw, sh = max(1, int(bw * scale)), max(1, int(bh * scale))
        if x + sw / 2 < 0 or x - sw / 2 > W or y + sh / 2 < 0 or y - sh / 2 > H:
            return
        img = base if (sw, sh) == (bw, bh) else (
            pygame.transform.smoothscale(base, (sw, sh)) if scale < 1.6 else pygame.transform.scale(base, (sw, sh)))
        if alpha < 0.995:
            if img is base:
                img = base.copy()
            img.set_alpha(int(alpha * 255))
        self.s.blit(img, (int(x - sw / 2), int(y - sh / 2)))

    def create_text(self, x, y, text="", fill=None, font=None, anchor="center", angle=0.0, tags=None, fast=False,
                    alpha=1.0):
        if not text or not fill or alpha <= 0.01:
            return
        aq = round(angle * 2) / 2
        key = (text, font.key, fill, aq, fast)
        hit = self.text_cache.get(key)
        if hit is None:
            if len(self.text_cache) > 3000:
                self.text_cache.clear()
            if fast:
                # Faint background text: hard edges and see-through runs blit far faster
                base = font.pg.render(text, False, rgb(fill), (255, 0, 255))
                base.set_colorkey((255, 0, 255))
            else:
                base = font.pg.render(text, True, rgb(fill))
            w, h = base.get_size()
            surf = pygame.transform.rotate(base, aq) if aq else base
            if fast:
                surf = surf.convert()
                surf.set_colorkey((255, 0, 255), pygame.RLEACCEL)
            else:
                surf = surf.convert_alpha()
            hit = (surf, w, h)
            self.text_cache[key] = hit
        surf, w, h = hit
        dx = {"w": w / 2, "e": -w / 2}.get(anchor, 0.0)
        th = math.radians(aq)
        cx, cy = x + dx * math.cos(th), y - dx * math.sin(th)
        sw, sh = surf.get_size()
        if cx + sw / 2 < 0 or cx - sw / 2 > W or cy + sh / 2 < 0 or cy - sh / 2 > H:
            return
        if alpha < 0.995:
            surf.set_alpha(int(alpha * 255), pygame.RLEACCEL if fast else 0)
        elif surf.get_alpha() not in (None, 255):
            surf.set_alpha(255, pygame.RLEACCEL if fast else 0)
        self.s.blit(surf, (int(cx - sw / 2), int(cy - sh / 2)))


canvas = Canvas(target)


def keep_on_top():
    try:
        _u32.SetWindowPos(_hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)   # topmost, no move/size/activate
    except Exception:
        pass


def desktop_ready():
    """True once the taskbar exists and something has focus, i.e. the sign-in screen is gone."""
    try:
        return _u32.FindWindowW("Shell_TrayWnd", None) != 0 and _u32.GetForegroundWindow() != 0
    except Exception:
        return True


# At sign-in Windows is still showing its welcome screen, so cover the screen in black and
# hold the animation until the desktop is actually there (up to 30 s). Run by hand, it starts at once.
if not desktop_ready():
    _wait_from, _ready_at = time.perf_counter(), None
    while time.perf_counter() - _wait_from < 30:
        pygame.event.pump()
        keep_on_top()
        screen.fill((0, 0, 0))
        pygame.display.flip()
        if desktop_ready():
            _ready_at = _ready_at or time.perf_counter()
            if time.perf_counter() - _ready_at > 0.5:
                break
        time.sleep(0.03)
    try:
        _u32.SetForegroundWindow(_hwnd)
    except Exception:
        pass

start = time.perf_counter()
_frame_no = [0]

def skip(_event=None):
    """Jump straight to the exit."""
    global start
    target = PRE + CLOSE_START
    if time.perf_counter() - start < target:
        start = time.perf_counter() - target

SHARDS = []
for i in range(10):
    side = 1 if i % 2 else -1
    SHARDS.append({
        "fx": W / 2 + side * W * (0.34 + J[20 + i] * 0.14),
        "fy": H * (0.16 + J[40 + i] * 0.66),
        "s": H * (0.04 + J[60 + i] * 0.07),
        "a": J[80 + i] * math.pi * 2, "side": side, "at": 0.2 + i * 0.02,
        "kind": i % 3,
    })
TRI = [(0, -1.3), (0.45, 0.8), (-0.35, 0.6)]
COFFIN = [(-0.32, -0.5), (0.32, -0.5), (0.5, -0.22), (0.3, 0.5), (-0.3, 0.5), (-0.5, -0.22)]
DIAMOND = [(0, -1), (0.6, 0), (0, 1), (-0.6, 0)]
STAR4 = [(math.cos(k * math.pi / 4) * (0.22 if k % 2 else 1), math.sin(k * math.pi / 4) * (0.22 if k % 2 else 1))
         for k in range(8)]
HALFTONE_STEP = H / 26
HALFTONE = []    # corner dots for P5: (x, y, full radius)
_y = HALFTONE_STEP / 2
while _y < H:
    _x = HALFTONE_STEP / 2
    while _x < W:
        _d = max(1 - math.hypot(_x, _y) / (H * 0.6), 1 - math.hypot(W - _x, H - _y) / (H * 0.6))
        if _d * HALFTONE_STEP * 0.5 > 0.6:
            HALFTONE.append((_x, _y, _d * HALFTONE_STEP * 0.5))
        _x += HALFTONE_STEP
    _y += HALFTONE_STEP
COFFIN_SPOTS = [(0.08, 0.3), (0.92, 0.33), (0.05, 0.55), (0.83, 0.7), (0.96, 0.56)]
STYLE = "dark" if DARK_MODE else "p5" if P5_MODE else "normal"
RAY_COLOUR = ICE if STYLE == "normal" else CYAN
RAYS = [((i / 44) * math.pi * 2 + J[i + 3] * 0.1, 0.006 + J[i + 50] * 0.012) for i in range(44)]
BANDS = [(0.19, 0.15, BLUE, 0.08), (0.3, 0.018, CYAN, 0.11),
         (0.86, 0.2, NIGHT, 0.14), (0.74, 0.014, ICE, 0.17)]

BAND_PX = H * 0.095
BAND_UNIT = font(DISPLAY_FONT, BAND_PX).measure(BAND_TEXT)

BG_PX, BG_ANGLE, BG_ROWS, BG_GAP = H * 0.12, -0.35, 12, H * 0.16
BG_UNIT = font(DISPLAY_FONT, BG_PX).measure(BG_TICKER)
BG_SPAN = math.hypot(W, H) * 1.3

SCAN_GAP = max(3, int(H / 240))
NAME_PX = H * 0.34
FLOAT_PX = H * 0.16
canvas.build_scanlines(SCAN_GAP)

desktop_mode = False


# ---- Dark Hour opening: the midnight clock ticks over, turns green, then shatters ----
TAU = math.pi * 2
PRE = 3.0 if DARK_MODE else 0.0
T_MID, T_CRACK, T_SHATTER = 1.8, 2.38, 2.62
CLOCK_WHITE, CLOCK_GREEN = "#f0f0f0", "#3fdc5a"
PRE_BG_BEFORE, PRE_BG_AFTER = "#000000", "#010703"
SERIF_FONT = "Times New Roman"   # ships with Windows
ROMAN = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
SHARD_N = 11
CRACK_ANG = [(k + 0.15 + hrand(k + 300) * 0.7) / SHARD_N * TAU for k in range(SHARD_N)]


def shard_range(k):
    return CRACK_ANG[k], (CRACK_ANG[k + 1] if k + 1 < SHARD_N else CRACK_ANG[0] + TAU)


def shard_of(a):
    a = a % TAU
    for k in range(SHARD_N - 1, -1, -1):
        if a >= CRACK_ANG[k]:
            return k
    return SHARD_N - 1


def seconds(T):
    return 0 if T >= T_MID else 56 + min(3, int(T / 0.45))


def polar(a, r):
    return math.sin(a) * r, -math.cos(a) * r


def clock_frame(T):
    return {"cx": W / 2, "cy": H * 0.52, "R": H * 0.36 * (1 + 0.05 * T),
            "sx": 0.8 + 0.08 * math.sin(T * 0.9), "rz": -0.22 + T * 0.06}


def shard_xf(k, T):
    u = clamp((T - T_SHATTER) / 0.6)
    if u <= 0:
        return {"dx": 0.0, "dy": 0.0, "spin": 0.0, "a": 1.0, "u": 0.0}
    a0, a1 = shard_range(k)
    m, e = (a0 + a1) / 2, ease_out(u)
    d = 0.1 + 1.5 * e + hrand(k + 310) * 0.6 * e
    return {"dx": math.sin(m) * d, "dy": -math.cos(m) * d + 1.3 * u * u,
            "spin": (hrand(k + 320) - 0.5) * 3.2 * e, "a": 1 - u, "u": u}


def hub_xf(T):
    u = clamp((T - T_SHATTER) / 0.5)
    return {"dx": 0.0, "dy": 1.6 * u * u, "spin": u * 1.4, "a": 1 - u, "u": u}


def make_p(F, xf, pivot):
    """Clock-local point (radius 1 = rim) to screen, through a shard's own spin and drift."""
    cs, sn = math.cos(xf["spin"]), math.sin(xf["spin"])
    c, s = math.cos(F["rz"]), math.sin(F["rz"])

    def P(x, y):
        px, py = x - pivot[0], y - pivot[1]
        lx = (pivot[0] + px * cs - py * sn + xf["dx"]) * F["R"] * F["sx"]
        ly = (pivot[1] + px * sn + py * cs + xf["dy"]) * F["R"]
        return F["cx"] + lx * c - ly * s, F["cy"] + lx * s + ly * c
    return P


def draw_clock(T, ground):
    F = clock_frame(T)
    mid = T >= T_MID
    base = CLOCK_GREEN if mid else CLOCK_WHITE
    lw = max(1.5, H * 0.004)
    xfs, Ps = [], []
    for k in range(SHARD_N):
        a0, a1 = shard_range(k)
        xfs.append(shard_xf(k, T))
        Ps.append(make_p(F, xfs[k], polar((a0 + a1) / 2, 0.8)))
    hx = hub_xf(T)
    HP = make_p(F, hx, (0.0, 0.0))

    def seg(P, p0, p1, w, col):
        canvas.create_line(*P(*p0), *P(*p1), fill=col, width=w, capstyle="round", tags="dyn")

    for k in range(SHARD_N):
        if xfs[k]["a"] <= 0:
            continue
        col = mix(ground, base, xfs[k]["a"])
        a0, a1 = shard_range(k)
        P = Ps[k]
        for r, w in ((1.0, lw * 1.7), (0.93, lw * 0.8), (0.62, lw * 0.6)):
            pts = []
            for j in range(13):
                pts += P(*polar(a0 + (a1 - a0) * j / 12, r))
            canvas.create_line(*pts, fill=col, width=w, tags="dyn")
        if xfs[k]["u"] > 0:
            for a in (a0, a1):
                seg(P, polar(a, 0.62), polar(a, 1.0), lw * 0.7, col)

    for i in range(60):
        a = i / 60 * TAU
        k = shard_of(a)
        if xfs[k]["a"] <= 0:
            continue
        seg(Ps[k], polar(a, 0.87 if i % 5 else 0.81), polar(a, 0.93),
            lw * 0.6 if i % 5 else lw * 1.4, mix(ground, base, xfs[k]["a"]))

    nf = font(SERIF_FONT, F["R"] * 0.12)
    for i, n in enumerate(ROMAN):
        a = i / 12 * TAU
        k = shard_of(a)
        if xfs[k]["a"] <= 0:
            continue
        x, y = Ps[k](*polar(a, 0.72))
        canvas.create_text(x, y, text=n, fill=mix(ground, base, xfs[k]["a"]), font=nf,
                           angle=-math.degrees(F["rz"] + xfs[k]["spin"] + a), tags="dyn")

    if hx["a"] > 0:
        col = mix(ground, base, hx["a"])
        s = seconds(T)
        ph = T - T_MID if mid else T % 0.45
        wob = math.exp(-ph * 18) * math.sin(ph * 60) * 0.05
        sec_a = s / 60 * TAU + wob
        min_a = 0.0 if mid else (59 + s / 60) / 60 * TAU
        hr_a = 0.0 if mid else (11 + (59 + s / 60) / 60) / 12 * TAU
        mx, my = HP(*polar(2.35, 0.36))
        canvas.create_text(mx, my, text="AM" if mid else "PM", fill=col, font=font(MONO_FONT, F["R"] * 0.075),
                           angle=-math.degrees(F["rz"] + hx["spin"]), tags="dyn")
        seg(HP, (0, 0), polar(hr_a, 0.42), lw * 2.6, col)
        seg(HP, (0, 0), polar(min_a, 0.68), lw * 1.7, col)
        seg(HP, polar(sec_a + math.pi, 0.14), polar(sec_a, 0.84), lw * 0.8, col)
        hcx, hcy = HP(0, 0)
        r = lw * 2.2
        canvas.create_oval(hcx - r, hcy - r, hcx + r, hcy + r, fill=col, outline="", tags="dyn")

    # Cracks race out along the break lines, then the face shatters
    cg = clamp((T - T_CRACK) / 0.16)
    if cg > 0 and T < T_SHATTER + 0.05:
        P0 = make_p(F, {"dx": 0, "dy": 0, "spin": 0}, (0.0, 0.0))
        reach = 0.08 + cg * 0.98
        for k, a in enumerate(CRACK_ANG):
            pts = []
            for j in range(8):
                r = 0.08 + (reach - 0.08) * j / 7
                pts += P0(*polar(a + (hrand(k * 17 + j) - 0.5) * 0.09, r))
            canvas.create_line(*pts, fill=DARK_HOUR[4], width=max(1.5, H * 0.003), tags="dyn")


def floater_text(i, T):
    ss = f"{seconds(T):02d}"
    if T >= T_MID:
        return ("00:00", "00:00", "00:00:00", "0000", "12:00")[i % 5]
    return ("11:59", "23:59", f"11:59:{ss}", "1159", f"23:59:{ss}")[i % 5]


def draw_floaters(T, ground):
    mid = T >= T_MID
    rush = (T - T_SHATTER) ** 2 * 6 if T > T_SHATTER else 0.0
    out = 1 - clamp((T - T_SHATTER) / 0.38) if T > T_SHATTER else 1.0
    base = CLOCK_GREEN if mid else CLOCK_WHITE
    for i in range(26):
        wx, wy = (hrand(i + 400) - 0.5) * 2.4, (hrand(i + 401) - 0.5) * 1.8
        speed = 0.35 + hrand(i + 402) * 0.5
        z = 0.3 + (hrand(i + 403) * 3 - T * speed - rush) % 3
        near, far = clamp((z - 0.3) / 0.25), clamp((3.3 - z) / 0.4)
        a = near * far * clamp(T / 0.3) * out * (0.3 + 0.7 * (1 - (z - 0.3) / 3))
        if a <= 0.01:
            continue
        px = min(H * 0.45, H * (0.045 + hrand(i + 404) * 0.07) / z)
        fam, wt = (SERIF_FONT, "normal") if i % 5 == 3 else (MONO_FONT, "bold")
        rot = (hrand(i + 405) - 0.5) * 1.3
        canvas.scaled_text(W / 2 + wx * W * 0.45 / z, H / 2 + wy * H * 0.5 / z, floater_text(i, T), base,
                           fam, wt, FLOAT_PX, px / FLOAT_PX, -math.degrees(rot), a)


def draw_prelude(T):
    mid = T >= T_MID
    ground = PRE_BG_AFTER if mid else PRE_BG_BEFORE
    canvas.create_rectangle(0, 0, W, H, fill=ground, outline="", tags="dyn")
    draw_floaters(T, ground)
    if T < T_SHATTER + 0.6:
        draw_clock(T, ground)
    if T_MID <= T < T_MID + 0.06:
        canvas.create_rectangle(0, 0, W, H, fill="#ffffff", outline="", tags="dyn")
    pp = clamp((T - T_MID) / 0.7)
    if 0 < pp < 1:
        F = clock_frame(T)
        rx, ry = F["R"] * (1 + pp * 2.5), F["R"] * (1 + pp * 2.5) * 0.82
        c, s = math.cos(F["rz"]), math.sin(F["rz"])
        pts = []
        for j in range(49):
            a = j / 48 * TAU
            x, y = math.cos(a) * rx, math.sin(a) * ry
            pts += [F["cx"] + x * c - y * s, F["cy"] + x * s + y * c]
        canvas.create_line(*pts, fill=mix(CLOCK_GREEN, ground, pp), width=H * 0.02 * (1 - pp) + 1, tags="dyn")
    if T_SHATTER <= T < T_SHATTER + 0.05:
        canvas.create_rectangle(0, 0, W, H, fill="#dcffe1", outline="", tags="dyn")


def tick():
    global desktop_mode
    T = time.perf_counter() - start
    if T >= DURATION + PRE:
        return False
    canvas.delete("dyn")

    if T < PRE:
        draw_prelude(T)
        canvas.tag_raise("scan")
        set_window_alpha(1.0)
        return True
    t = T - PRE

    def poly(pts, col, cam=None):
        flat = []
        for p in pts:
            flat += cam(*p) if cam else p
        canvas.create_polygon(flat, fill=col, outline="", tags="dyn")

    if t < CLOSE_END:
        draw_scene(t, poly)
        if PRE and T < T_SHATTER + 0.6:
            draw_clock(T, BG)   # last clock shards fly out over the start of the splash
        canvas.tag_raise("scan")
    elif not desktop_mode:
        desktop_mode = True
        canvas.itemconfigure("scan", state="hidden")
        if SEE_THROUGH:
            canvas.configure(bg=KEY)
        else:
            canvas.configure(bg=NIGHT)

    if t >= CLOSE_START:
        draw_blades(t, poly)

    # Flicker at power-on; fade during the opening if see-through is unavailable
    if not SEE_THROUGH and t >= OPEN_START:
        set_window_alpha(1 - clamp((t - OPEN_START) / (DURATION - OPEN_START)))
    elif 0.04 < t < 0.07 or 0.1 < t < 0.12:
        set_window_alpha(0.45)
    else:
        set_window_alpha(1.0)
    return True


def draw_scene(t, poly):
    ox = oy = 0.0
    if IMPACT < t < IMPACT + 0.25:
        a = (1 - (t - IMPACT) / 0.25) * H * 0.02
        ox, oy = math.sin(t * 97) * a, math.cos(t * 73) * a
    zoom = 1 + 0.03 * ease_out(clamp((t - IMPACT) / 1.4))

    def T(px, py):
        return (W / 2 + (px - W / 2) * zoom + ox, H / 2 + (py - H / 2) * zoom + oy)

    def cpoly(pts, col):
        poly(pts, col, T)

    def text(s, x, y, f, col, anchor="center", rot=0.0, cam=True, fast=False, alpha=1.0):
        if cam:
            x, y = T(x, y)
        canvas.create_text(x, y, text=s, fill=col, font=f, anchor=anchor,
                           angle=-math.degrees(rot), tags="dyn", fast=fast, alpha=alpha)

    canvas.create_rectangle(0, 0, W, H, fill=BG, outline="", tags="dyn")

    # Grid
    gp = clamp((t - 0.1) / 0.3)
    if gp > 0:
        col = mix(BG, BLUE, gp * 0.2)
        g = H / 12
        x = (W / 2) % g
        while x < W:
            canvas.create_line(x, 0, x, H, fill=col, tags="dyn")
            x += g
        y = (H / 2) % g
        while y < H:
            canvas.create_line(0, y, W, y, fill=col, tags="dyn")
            y += g

    # Background rows of BURN MY DREAD
    bgp = clamp((t - 0.15) / 0.25)
    if bgp > 0:
        ca, sa = math.cos(BG_ANGLE), math.sin(BG_ANGLE)
        bf = font(DISPLAY_FONT, BG_PX * zoom)
        for r in range(BG_ROWS):
            direction = 1 if r % 2 else -1
            speed = BG_UNIT * (1.3 + J[r + 90] * 0.6)
            off = ((t * speed + J[r + 100] * BG_UNIT) % BG_UNIT) * direction
            lx = -BG_SPAN / 2 - BG_UNIT + off
            ly = (r - (BG_ROWS - 1) / 2) * BG_GAP
            col, ra = (CYAN, bgp * 0.12) if r % 3 == 1 else (BLUE, bgp * 0.22)
            unit = bf.measure(BG_TICKER)
            for k in range(int(BG_SPAN / BG_UNIT) + 3):
                ux = lx * zoom + k * unit
                sx, sy = W / 2 + ux * ca - ly * zoom * sa, H / 2 + ux * sa + ly * zoom * ca
                text(BG_TICKER, sx + ox, sy + oy, bf, col, "w", BG_ANGLE, cam=False, fast=True, alpha=ra)

    # Opening slice
    sl = clamp(t / 0.12)
    if sl > 0 and t < 0.4:
        canvas.create_line(-W * 0.05, H * 0.95, -W * 0.05 + sl * W * 1.1, H * 0.95 - sl * H * 0.9,
                           fill=mix(ICE, BG, clamp((t - 0.18) / 0.2)), width=max(2, H * 0.004), tags="dyn")

    # Bands
    for by, bh, col, d in BANDS:
        p = ease_out(clamp((t - d) / 0.22))
        if p > 0:
            yc, h = H * by, H * bh
            sk, x0 = h * 1.6, -W * 0.3
            x1 = x0 + p * W * 1.7
            cpoly([(x0 + sk, yc - h / 2), (x1 + sk, yc - h / 2), (x1 - sk, yc + h / 2), (x0 - sk, yc + h / 2)], col)

    # Band ticker
    tk_p = clamp((t - 0.28) / 0.25)
    if tk_p > 0:
        off = (t * W * 0.18) % BAND_UNIT
        bfont = font(DISPLAY_FONT, BAND_PX * zoom)
        x = -W * 0.2 - off
        while x < W * 1.1:
            text(BAND_TEXT, x, H * 0.19, bfont, ICE, "w", fast=True, alpha=tk_p * 0.3)
            x += BAND_UNIT

    # Particles: each mode has its own set
    def shape_at(shape, cx, cy, a, sx, sy=None):
        sy = sx if sy is None else sy
        ca, sa = math.cos(a), math.sin(a)
        return [(cx + (x * sx * ca - y * sy * sa), cy + (x * sx * sa + y * sy * ca)) for x, y in shape]

    if STYLE == "dark":
        # Thin streaks falling through the dark
        dp = clamp((t - 0.2) / 0.3)
        if dp > 0:
            sw = max(1.5, H * 0.002)
            for i in range(16):
                x = W * hrand(i + 40)
                ln = H * (0.05 + hrand(i + 41) * 0.1)
                speed = H * (0.5 + hrand(i + 42) * 0.6)
                y = ((t * speed + hrand(i + 43) * H * 1.2) % (H * 1.2)) - H * 0.1
                cpoly([(x, y), (x + sw, y), (x + sw, y + ln), (x, y + ln)],
                      mix(BG, CYAN, dp * (0.25 + hrand(i + 44) * 0.35)))
        # A few coffin silhouettes rising slowly, outlined in green
        for i, (fx, fy) in enumerate(COFFIN_SPOTS):
            p = clamp((t - 0.2 - i * 0.06) / 0.45)
            if p <= 0:
                continue
            e = ease_out(p)
            h = H * (0.09 + hrand(i + 7) * 0.05)
            w = h * 0.42
            cx = W * fx
            cy = H * fy + (1 - e) * H * 0.12 - t * H * 0.03
            a = math.sin(t * 1.5 + i) * 0.08 + (hrand(i + 19) - 0.5) * 0.5
            cpoly(shape_at(COFFIN, cx, cy, a, w * 1.16, h * 1.08), mix(BG, CYAN, e * 0.85))
            cpoly(shape_at(COFFIN, cx, cy, a, w, h), NIGHT)
            cross = mix(NIGHT, CYAN, e * 0.5)
            cpoly(shape_at([(-0.04, -0.3), (0.04, -0.3), (0.04, 0.1), (-0.04, 0.1)], cx, cy, a, w, h), cross)
            cpoly(shape_at([(-0.18, -0.16), (0.18, -0.16), (0.18, -0.1), (-0.18, -0.1)], cx, cy, a, w, h), cross)
        # Embers rising and flickering on top
        ep = clamp((t - 0.25) / 0.3)
        if ep > 0:
            for i in range(38):
                speed = H * (0.12 + hrand(i + 200) * 0.3)
                y = H * 1.05 - ((t * speed + hrand(i + 201) * H * 1.1) % (H * 1.1))
                x = W * hrand(i + 202) + math.sin(t * (1.5 + hrand(i + 203) * 2) + i) * H * 0.02
                flick = 0.45 + 0.55 * abs(math.sin(t * (6 + hrand(i + 204) * 10) + i * 1.7))
                sc = H * (0.004 + hrand(i + 205) * 0.007)
                cpoly(shape_at(DIAMOND, x, y, t * 2 + i, sc), mix(BG, CYAN if i % 4 else ICE, ep * flick))

    elif STYLE == "p5":
        # Halftone dots fading in from two corners, like the P5 menus
        hp5 = clamp((t - 0.1) / 0.3)
        if hp5 > 0:
            dot = mix(BG, NIGHT, 0.5)
            for x, y, r in HALFTONE:
                r *= hp5
                if r > 0.6:
                    canvas.create_oval(x - r, y - r, x + r, y + r, fill=dot, outline="", tags="dyn")

        # Streaks shooting in from the screen edges, ending in sharp speech-bubble points
        per = 2 * (W + H)
        for i in range(20):
            second = i >= 13
            at = IMPACT + (i - 13) * 0.025 if second else 0.16 + i * 0.028
            p = clamp((t - at) / 0.13)
            if p <= 0:
                continue
            d = ((i * 0.381966 + hrand(i + 120) * 0.08) % 1) * per
            if d < W:
                ex, ey = d, -H * 0.02
            elif d < W + H:
                ex, ey = W * 1.02, d - W
            elif d < 2 * W + H:
                ex, ey = W - (d - W - H), H * 1.02
            else:
                ex, ey = -W * 0.02, H - (d - 2 * W - H)
            dx, dy = W / 2 - ex, H * 0.56 - ey
            dist = math.hypot(dx, dy)
            dx, dy = dx / dist, dy / dist
            r_stop = 1 / math.sqrt(dx * dx / (W * 0.3) ** 2 + dy * dy / (H * 0.27) ** 2)
            L = ease_out(p) * max(H * 0.1, (dist - r_stop) * (0.5 + hrand(i + 121) * 0.5))
            w = H * (0.014 + hrand(i + 122) * 0.026)
            nx, ny = -dy, dx
            tip = min(L, w * 2.6)
            body = L - tip
            bend = (hrand(i + 123) - 0.5) * w * 1.6

            def arrow(k):
                return [(ex + nx * w * k / 2, ey + ny * w * k / 2),
                        (ex + dx * body + nx * w * k * 0.32, ey + dy * body + ny * w * k * 0.32),
                        (ex + dx * (L + w * (k - 1)) + nx * bend, ey + dy * (L + w * (k - 1)) + ny * bend),
                        (ex + dx * body - nx * w * k * 0.32, ey + dy * body - ny * w * k * 0.32),
                        (ex - nx * w * k / 2, ey - ny * w * k / 2)]

            front, back = ((NIGHT, ICE), (ICE, NIGHT), (BLUE, NIGHT))[i % 3]
            cpoly(arrow(1.7), back)
            cpoly(arrow(1), front)

        # Sparkle stars on top: a scattered wave, then a burst out of ALEX when it lands
        for i in range(18):
            burst = i >= 8
            at = IMPACT + (i - 8) * 0.025 if burst else 0.35 + i * 0.06
            life = clamp((t - at) / (0.55 if burst else 0.7))
            if life <= 0 or life >= 1:
                continue
            sc = math.sin(life * math.pi) * H * (0.022 + hrand(i + 80) * 0.035)
            if burst:
                ang, dist = hrand(i + 81) * math.pi * 2, ease_out(life) * H * 0.55
                cx, cy = W / 2 + math.cos(ang) * dist * 1.6, H * 0.6 + math.sin(ang) * dist
            else:
                cx, cy = W * (0.08 + hrand(i + 82) * 0.84), H * (0.1 + hrand(i + 83) * 0.8)
            front, back = (ICE, NIGHT) if i % 2 else (NIGHT, ICE)
            cpoly(shape_at(STAR4, cx + sc * 0.1, cy + sc * 0.1, life * 1.5, sc * 1.3), back)
            cpoly(shape_at(STAR4, cx, cy, life * 1.5, sc), front)

    else:
        # Rising bubbles, like the P3 Reload menus: thin rings, only in the middle of each side
        bp = clamp((t - 0.15) / 0.35)
        if bp > 0:
            top, span = H * 0.28, H * 0.5
            for i in range(16):
                left = i % 2 == 0
                r = H * (0.008 + hrand(i + 500) * 0.022)
                speed = H * (0.05 + hrand(i + 501) * 0.07)
                k = (t * speed / span + hrand(i + 502)) % 1
                y = top + span * (1 - k)
                x = W * (0.04 + hrand(i + 503) * 0.15 if left else 0.81 + hrand(i + 503) * 0.15)
                x += math.sin(t * (1 + hrand(i + 504)) + i) * H * 0.01
                edge = min(1.0, k / 0.2, (1 - k) / 0.2)
                a = bp * edge * (0.45 + hrand(i + 505) * 0.4)
                x, y = T(x, y)
                rr = r * zoom
                canvas.create_oval(x - rr, y - rr, x + rr, y + rr, outline=mix(BG, CYAN, a),
                                   width=max(1, H * 0.0025), tags="dyn")

        for s in SHARDS:
            p = clamp((t - s["at"]) / 0.2)
            if p <= 0:
                continue
            e = ease_out(p)
            cx = s["fx"] + s["side"] * (1 - e) * W * 0.6
            cy = s["fy"] - (1 - e) * H * 0.2
            cpoly(shape_at(TRI, cx, cy, s["a"] + (1 - e) * 3 + t * 0.05, s["s"]), (CYAN, ICE, BLUE)[s["kind"]])

    # Speed lines
    rp = clamp((t - IMPACT) / 0.5)
    if 0 < rp < 1:
        col = mix(RAY_COLOUR, BG, ease_in(rp))
        r0 = H * 0.32 + ease_out(rp) * W * 0.55
        r1 = r0 + W * 0.5 * (1 - rp)
        for ang, wd in RAYS:
            wa = wd * (1 - rp)
            cpoly([(W / 2 + math.cos(ang - wa) * r0, H * 0.55 + math.sin(ang - wa) * r0),
                   (W / 2 + math.cos(ang) * r1, H * 0.55 + math.sin(ang) * r1),
                   (W / 2 + math.cos(ang + wa) * r0, H * 0.55 + math.sin(ang + wa) * r0)], col)

    # Greeting line with blinking cursor
    l1 = scramble(LINE1_SPACED, t, 0.45, 0.015)
    if l1:
        px = H * 0.052
        base = font(MONO_FONT, px, "bold")
        fw = base.measure(LINE1_SPACED)
        x0, y0, rot = W / 2 - fw / 2, H * 0.36, -0.06
        text(l1, x0, y0, font(MONO_FONT, px * zoom, "bold"), ICE, "w", rot)
        if t < IMPACT + 0.4 and int(t * 8) % 2 == 0:
            cw = base.measure(l1) + px * 0.2
            ca, sa = math.cos(rot), math.sin(rot)
            cpoly([(x0 + dx * ca - dy * sa, y0 + dx * sa + dy * ca)
                   for dx, dy in ((cw, -px * 0.45), (cw + px * 0.5, -px * 0.45),
                                  (cw + px * 0.5, px * 0.45), (cw, px * 0.45))], CYAN)

    # Name: afterimages, slam, colour split, glitch slices
    cx, cy, rot = W / 2, H * 0.6, -0.06

    def pop_at(tt):
        u = clamp((tt - IMPACT + 0.08) / 0.08)
        return 1 + (1 - u) ** 3 * 2.4 if u > 0 else 0

    if t < IMPACT + 0.22:
        fade = clamp((IMPACT + 0.22 - t) / 0.22)
        for k in (3, 2, 1):
            p = pop_at(t - k * 0.035)
            if p > 0:
                x, y = T(cx, cy)
                canvas.scaled_text(x, y, NAME, CYAN if k == 1 else BLUE, DISPLAY_FONT, "normal", NAME_PX,
                                   p * (1 + k * 0.06) * zoom, -math.degrees(rot), fade * (0.55 - k * 0.12))

    pop = pop_at(t)
    if pop:
        glitch = max(0.0, 1 - (t - IMPACT) / 0.3) if t < IMPACT + 0.3 else 0.0
        split = H * (0.008 + 0.03 * glitch)
        seed = int(t * 60)
        jx = (hrand(seed) - 0.5) * H * 0.05 * glitch if glitch > 0 else 0.0
        for dx, dy, col in ((-split + jx, 0, BLUE), (split - jx, split * 0.4, CYAN), (jx * 0.3, 0, ICE)):
            x, y = T(cx + dx, cy + dy)
            canvas.scaled_text(x, y, NAME, col, DISPLAY_FONT, "normal", NAME_PX, pop * zoom, -math.degrees(rot))

        if glitch > 0.05:
            top, hgt, left, wid = cy - H * 0.19, H * 0.38, cx - H * 0.55, H * 1.1
            for i in range(5):
                y = top + hrand(seed * 7 + i) * hgt
                h = H * (0.006 + hrand(seed * 3 + i) * 0.02) * glitch
                cpoly([(left, y), (left + wid, y), (left + wid, y + h), (left, y + h)], BG)
            for i in range(3):
                y = top + hrand(seed * 11 + i) * hgt
                h = H * (0.008 + hrand(seed * 5 + i) * 0.03) * glitch
                x = left + (hrand(seed * 13 + i) - 0.3) * wid * 0.5
                bw = wid * (0.2 + hrand(seed + i) * 0.4)
                cpoly([(x, y), (x + bw, y), (x + bw, y + h), (x, y + h)], ICE if i == 0 else CYAN)

    # Cut under the name
    up = ease_out(clamp((t - IMPACT - 0.08) / 0.25))
    if up > 0:
        yy, h, x0 = H * 0.8, H * 0.016, W * 0.3
        x1 = x0 + up * W * 0.4
        cpoly([(x0 + h, yy - h / 2), (x1 + h, yy - h / 2), (x1 - h, yy + h / 2), (x0 - h, yy + h / 2)], CYAN)

    if IMPACT < t < IMPACT + 0.05:
        # P5 hits with a hard black frame before the white one
        flash = NIGHT if STYLE == "p5" and t < IMPACT + 0.025 else ICE
        canvas.create_rectangle(0, 0, W, H, fill=flash, outline="", tags="dyn")

    # Interface layer: every block sits on its own dark panel so it stays readable
    hp = ease_out(clamp((t - 0.12) / 0.2))
    if hp > 0:
        A = BG if STYLE == "p5" else CYAN          # highlight that reads on the dark panels
        m, ln, o = H * 0.05, H * 0.06, (1 - hp) * H * 0.05
        lw = max(2, H * 0.003)
        bracket = ICE if STYLE == "p5" else CYAN
        for x, y, dx, dy in ((m - o, m - o, 1, 1), (W - m + o, m - o, -1, 1),
                             (m - o, H - m + o, 1, -1), (W - m + o, H - m + o, -1, -1)):
            canvas.create_line(x + dx * ln, y, x, y, x, y + dy * ln, fill=bracket, width=lw, tags="dyn")

        fs, m2 = H * 0.022, H * 0.085
        pad, lh = fs * 0.7, fs * 1.32
        mf, sf = font(MONO_FONT, fs), font(MONO_FONT, fs * 0.9)
        panel_col = mix(BG, NIGHT, hp)
        acc = mix(NIGHT, A, hp)
        ink = mix(NIGHT, ICE, hp)

        def panel(x, y, w, h):
            k = min(h * 0.4, fs * 0.9)
            canvas.create_polygon(x, y, x + w, y, x + w, y + h - k, x + w - k, y + h, x, y + h,
                                  fill=panel_col, outline="", tags="dyn")
            canvas.create_rectangle(x, y, x + max(2, H * 0.003), y + h, fill=acc, outline="", tags="dyn")

        head = "SYS // STARTUP SEQUENCE"
        panel(m2 - pad, m2 - fs * 0.95, mf.measure(head) + pad * 2, fs * 1.9)
        text(scramble(head, t, 0.2, 0.012), m2, m2, mf, acc, "w", cam=False)

        trw = max(mf.measure(DATE_TAG), mf.measure(CLOCK)) + pad * 2
        panel(W - m2 - trw + pad, m2 - fs * 0.95, trw, fs * 1.9 + lh)
        text(scramble(CLOCK, t, 0.3, 0.03), W - m2, m2, mf, ink, "e", cam=False)
        text(scramble(DATE_TAG, t, 0.32, 0.012), W - m2, m2 + lh, mf, acc, "e", cam=False)

        sw = mf.measure(SYSINFO)
        panel(W - m2 - sw - pad, H - m2 - fs * 0.95, sw + pad * 2, fs * 1.9)
        text(scramble(SYSINFO, t, 0.35, 0.008), W - m2, H - m2, mf, acc, "e", cam=False)

        lines = [f"> {k:<8}{v}" for k, v in READOUT]
        bw, bh = W * 0.13, H * 0.008
        by = H - m2 + fs * 0.2
        y0 = by - fs * 0.9 - len(lines) * lh
        blw = max([bw + mf.measure("100%") + fs * 0.6] + [sf.measure(s) for s in lines]) + pad * 2
        top = y0 - fs * 0.95
        panel(m2 - pad, top, blw, by + bh + pad - top)
        for i, full in enumerate(lines):
            at = 1.02 + i * 0.08
            line = scramble(full, t, at, 0.01)
            if line:
                text(line, m2, y0 + i * lh, sf, acc if i == 1 and t > at + 0.15 else ink, "w", cam=False)
        lp = ease_out(clamp((t - 1.1) / 1.1))
        canvas.create_rectangle(m2, by, m2 + bw, by + bh, fill=mix(NIGHT, ICE, 0.18 * hp), outline="", tags="dyn")
        if lp > 0:
            canvas.create_rectangle(m2, by, m2 + bw * lp, by + bh, fill=acc, outline="", tags="dyn")
            text(f"{round(lp * 100)}%", m2 + bw + fs * 0.6, by + bh / 2, sf, ink, "w", cam=False)


def draw_blades(t, poly):
    if t < CLOSE_END:
        off = (1 - ease_in(clamp((t - CLOSE_START) / (CLOSE_END - CLOSE_START)))) * H * 0.85
    elif t < OPEN_START:
        off = 0.0
    else:
        off = ease_in(clamp((t - OPEN_START) / (DURATION - OPEN_START))) * H * 1.1
    e, L0, R0 = H * 0.012, -W * 0.2, W * 1.2
    poly([(L0, -H * 2), (R0, -H * 2), (R0, H * 0.42 - off + e), (L0, H * 0.62 - off + e)], ICE)
    poly([(L0, -H * 2), (R0, -H * 2), (R0, H * 0.42 - off), (L0, H * 0.62 - off)], NIGHT)
    poly([(L0, H * 0.62 + off - e), (R0, H * 0.42 + off - e), (R0, H * 3), (L0, H * 3)], ICE)
    poly([(L0, H * 0.62 + off), (R0, H * 0.42 + off), (R0, H * 3), (L0, H * 3)], NIGHT)
    if CLOSE_END <= t < OPEN_START + 0.05:
        sp = clamp((t - CLOSE_END) / (OPEN_START - CLOSE_END))
        canvas.create_line(L0, H * 0.62, R0, H * 0.42, fill=mix(ICE, CYAN, sp),
                           width=H * 0.012 * (1 - sp * 0.6), tags="dyn")


clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            skip()
    if running and not tick():
        running = False
    if running:
        _frame_no[0] += 1
        if _frame_no[0] % 15 == 0:
            keep_on_top()   # stay above the taskbar while Windows finishes loading
        if target is not screen:
            pygame.transform.smoothscale(target, (SW, SH), screen)
        pygame.display.flip()
        clock.tick(60)
pygame.quit()
