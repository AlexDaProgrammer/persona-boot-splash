"""Switch the startup splash mode.

Double-click to cycle: AUTO -> DARK HOUR -> PERSONA 5 -> NORMAL -> AUTO.
AUTO plays Dark Hour only between midnight and 1am.
Keep this file in the same folder as boot_animation.pyw.
In the popup, press Enter to preview the splash, or any other key to close.
"""
import os
import subprocess
import sys
import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))
MODE_FILE = os.path.join(HERE, "splash_mode.txt")
SPLASH = os.path.join(HERE, "boot_animation.pyw")
ORDER = ["auto", "dark", "p5", "normal"]
LABELS = {"auto": "AUTO", "dark": "DARK HOUR", "p5": "PERSONA 5", "normal": "NORMAL"}
NOTES = {
    "auto": "Dark Hour plays only between 00:00 and 01:00",
    "dark": "Dark Hour plays at every sign-in",
    "p5": "Persona 5 red mode plays at every sign-in",
    "normal": "Blue mode plays at every sign-in",
}
COLOURS = {
    "auto": ("#071433", "#4fd8ff", "#eef7ff"),
    "dark": ("#06170c", "#c4ff5e", "#effee0"),
    "p5": ("#d10a1f", "#111111", "#ffffff"),
    "normal": ("#071433", "#4fd8ff", "#eef7ff"),
}

try:
    with open(MODE_FILE, encoding="utf-8") as f:
        current = f.read().strip().lower()
except OSError:
    current = "auto"
if current not in ORDER:
    current = "auto"
new = ORDER[(ORDER.index(current) + 1) % len(ORDER)]
with open(MODE_FILE, "w", encoding="utf-8") as f:
    f.write(new)

bg, accent, ink = COLOURS[new]
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
w, h = 520, 190
x = (root.winfo_screenwidth() - w) // 2
y = (root.winfo_screenheight() - h) // 2
root.geometry(f"{w}x{h}+{x}+{y}")
c = tk.Canvas(root, width=w, height=h, bg=bg, highlightthickness=0)
c.pack()
c.create_polygon(0, 0, w, 0, w, 6, 0, 6, fill=accent, outline="")
c.create_text(28, 38, text="SYS // SPLASH MODE", fill=accent, font=("Consolas", 12), anchor="w")
c.create_text(28, 88, text=LABELS[new], fill=ink, font=("Impact", 40), anchor="w")
c.create_text(28, 134, text=NOTES[new], fill=accent, font=("Consolas", 11), anchor="w")
c.create_text(28, 164, text="ENTER  preview     ANY KEY  close", fill=ink, font=("Consolas", 10), anchor="w")

def preview(_e=None):
    root.destroy()
    exe = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([exe, SPLASH, "--" + new])

root.bind("<Return>", preview)
root.bind("<Key>", lambda e: root.destroy() if e.keysym != "Return" else None)
root.bind("<Button>", lambda e: root.destroy())
root.after(4000, root.destroy)
root.focus_force()
root.mainloop()
