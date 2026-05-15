import tkinter as tk
from PIL import Image, ImageTk
import numpy as np


# ── Palette ───────────────────────────────────────────────────────────────────
WHITE     = "#FFFFFF"
GRAY_50   = "#F8FAFC"
GRAY_100  = "#F1F5F9"
GRAY_200  = "#E2E8F0"
GRAY_400  = "#94A3B8"
GRAY_600  = "#475569"
GRAY_900  = "#0F172A"

TEAL_400  = "#2DD4BF"
TEAL_500  = "#14B8A6"
TEAL_600  = "#0D9488"
TEAL_50   = "#F0FDFA"

RED_500   = "#EF4444"
RED_100   = "#FEE2E2"
RED_700   = "#B91C1C"
BLUE_500  = "#3B82F6"
AMBER_500 = "#F59E0B"
AMBER_100 = "#FEF3C7"
GREEN_500 = "#22C55E"
ORANGE_500 = "#F97316"   # timer warning colour (< 30 s)

# ── Typography ────────────────────────────────────────────────────────────────
FONT_DISPLAY  = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI",  9, "normal")
FONT_HEADING  = ("Segoe UI", 11, "bold")
FONT_BODY     = ("Segoe UI", 10, "normal")
FONT_LABEL    = ("Segoe UI",  9, "bold")
FONT_STAT     = ("Segoe UI", 22, "bold")
FONT_BTN      = ("Segoe UI", 10, "bold")
FONT_MONO     = ("Consolas",  9, "normal")
FONT_MSG      = ("Segoe UI", 10, "normal")


# ─────────────────────────────────────────────────────────────────────────────
class StatCard(tk.Frame):
    """
    Clean stat card: muted label above, large bold value below,
    with a 3-px coloured accent strip at the top.
    """

    def _init_(self, parent, label: str, value: str = "—",
                 accent: str = TEAL_500, **kw):
        super()._init_(parent, bg=GRAY_50, bd=0, **kw)

        card = tk.Frame(self, bg=WHITE,
                        highlightthickness=1,
                        highlightbackground=GRAY_200)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Frame(card, bg=accent, height=3).pack(fill="x")

        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=16, pady=(8, 12))

        tk.Label(inner, text=label, bg=WHITE,
                 fg=GRAY_400, font=FONT_LABEL).pack(anchor="w")

        self._var = tk.StringVar(value=value)
        tk.Label(inner, textvariable=self._var, bg=WHITE,
                 fg=GRAY_900, font=FONT_STAT).pack(anchor="w")

    def set(self, value: str) -> None:
        self._var.set(value)


# ─────────────────────────────────────────────────────────────────────────────
class MistakePips(tk.Frame):
    """
    Large, visually distinct mistake indicator.

    Shows three heart / X badges:
      ♥️  green  = life remaining
      ✕  red    = life lost

    Each pip is a small labelled card so they read clearly at a glance.
    """

    MAX = 3

    def _init_(self, parent, **kw):
        super()._init_(parent, bg=WHITE, **kw)

        tk.Label(self, text="MISTAKES", bg=WHITE,
                 fg=GRAY_400, font=FONT_LABEL).pack(anchor="w",
                                                     padx=16, pady=(10, 4))

        pip_row = tk.Frame(self, bg=WHITE)
        pip_row.pack(padx=16, pady=(0, 10))

        self._pip_frames: list[tk.Frame]  = []
        self._pip_icons:  list[tk.Label]  = []
        self._pip_texts:  list[tk.Label]  = []

        for i in range(self.MAX):
            card = tk.Frame(pip_row, bg=GREEN_500,
                            highlightthickness=0,
                            padx=12, pady=6)
            card.pack(side="left", padx=(0 if i == 0 else 6, 0))

            icon = tk.Label(card, text="♥️",
                            bg=GREEN_500, fg=WHITE,
                            font=("Segoe UI", 18, "bold"))
            icon.pack()

            txt = tk.Label(card, text=f"Life {i + 1}",
                           bg=GREEN_500, fg=WHITE,
                           font=("Segoe UI", 7, "bold"))
            txt.pack()

            self._pip_frames.append(card)
            self._pip_icons.append(icon)
            self._pip_texts.append(txt)

    def update_pips(self, mistakes: int) -> None:
        """Flip pip i to a red X-card when mistake i is made."""
        for i in range(self.MAX):
            if i < mistakes:
                # Lost life — red X
                self._pip_frames[i].config(bg=RED_500)
                self._pip_icons[i].config(text="✕", bg=RED_500)
                self._pip_texts[i].config(text="Lost", bg=RED_500)
            else:
                # Remaining life — green heart
                self._pip_frames[i].config(bg=GREEN_500)
                self._pip_icons[i].config(text="♥️", bg=GREEN_500)
                self._pip_texts[i].config(text=f"Life {i + 1}", bg=GREEN_500)


# ─────────────────────────────────────────────────────────────────────────────
class TimerWidget(tk.Frame):
    """
    Countdown timer card displayed in the stats row.

    Visual states:
      > 30 s  — teal  (normal)
      10-30 s — amber (warning)
      < 10 s  — red   (danger), pulses background

    Exposes:
      start(seconds)  — begin countdown
      stop()          — cancel any running countdown
      reset()         — stop and restore to initial display
    """

    def _init_(self, parent, **kw):
        super()._init_(parent, bg=GRAY_50, bd=0, **kw)

        # Outer card frame
        self._card = tk.Frame(self, bg=WHITE,
                              highlightthickness=1,
                              highlightbackground=GRAY_200)
        self._card.pack(fill="both", expand=True, padx=1, pady=1)

        # Top accent strip — colour changes with urgency
        self._strip = tk.Frame(self._card, bg=TEAL_500, height=3)
        self._strip.pack(fill="x")

        inner = tk.Frame(self._card, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=16, pady=(8, 12))

        tk.Label(inner, text="TIME LEFT", bg=WHITE,
                 fg=GRAY_400, font=FONT_LABEL).pack(anchor="w")

        self._time_var = tk.StringVar(value="2:00")
        self._time_lbl = tk.Label(inner, textvariable=self._time_var,
                                  bg=WHITE, fg=GRAY_900,
                                  font=FONT_STAT)
        self._time_lbl.pack(anchor="w")

        self._sub_var = tk.StringVar(value="Load image to start")
        self._sub_lbl = tk.Label(inner, textvariable=self._sub_var,
                                 bg=WHITE, fg=GRAY_400,
                                 font=("Segoe UI", 8, "normal"))
        self._sub_lbl.pack(anchor="w")

        # Internal state
        self._remaining:   int  = 0
        self._after_id:    str | None = None
        self._on_expire:   callable | None = None
        self._pulse_on:    bool = False

    # ── Public API ────────────────────────────────────────────────────
    def start(self, seconds: int, on_expire: callable = None) -> None:
        """Start counting down from seconds. Calls on_expire when done."""
        self.stop()
        self._remaining = seconds
        self._on_expire = on_expire
        self._pulse_on  = False
        self._tick()

    def stop(self) -> None:
        """Cancel the countdown without triggering on_expire."""
        if self._after_id:
            self._time_lbl.after_cancel(self._after_id)
            self._after_id = None

    def reset(self) -> None:
        """Stop and restore initial display."""
        self.stop()
        self._remaining = 0
        self._time_var.set("2:00")
        self._sub_var.set("Load image to start")
        self._apply_state("normal")

    # ── Internal ──────────────────────────────────────────────────────
    def _tick(self) -> None:
        s = self._remaining
        mins = s // 60
        secs = s % 60
        self._time_var.set(f"{mins}:{secs:02d}")

        if s > 30:
            self._apply_state("normal")
            self._sub_var.set("Keep going!")
        elif s > 10:
            self._apply_state("warning")
            self._sub_var.set("Running low…")
        elif s > 0:
            self._apply_state("danger")
            self._sub_var.set("Hurry up!")
            self._pulse()
        else:
            self._apply_state("expired")
            self._time_var.set("0:00")
            self._sub_var.set("Time's up!")
            if self._on_expire:
                self._on_expire()
            return

        self._remaining -= 1
        self._after_id = self._time_lbl.after(1000, self._tick)

    def _apply_state(self, state: str) -> None:
        colours = {
            "normal":  (TEAL_500,   GRAY_900, WHITE),
            "warning": (AMBER_500,  "#92400E", AMBER_100),
            "danger":  (RED_500,    RED_700,   RED_100),
            "expired": (RED_700,    RED_700,   RED_100),
        }
        strip_col, text_col, bg_col = colours.get(state, colours["normal"])
        self._strip.config(bg=strip_col)
        self._time_lbl.config(fg=text_col)
        self._card.config(highlightbackground=strip_col)

    def _pulse(self) -> None:
        """Alternate card background to draw attention in danger zone."""
        current = self._card.cget("bg")
        next_bg = RED_100 if current == WHITE else WHITE
        self._card.config(bg=next_bg)
        for child in self._card.winfo_children():
            try:
                child.config(bg=next_bg)
            except tk.TclError:
                pass
        # Cancel previous pulse and schedule next at 500 ms
        self._time_lbl.after(500, lambda: None)


# ─────────────────────────────────────────────────────────────────────────────
class StatBar(tk.Frame):
    """
    Horizontal stats row: Score · Remaining · Found · Mistakes · Timer.
    """

    def _init_(self, parent, **kw):
        super()._init_(parent, bg=GRAY_50, **kw)

        self._score_card  = StatCard(self, "SCORE",       "0",     TEAL_500)
        self._remain_card = StatCard(self, "REMAINING",   "—",     AMBER_500)
        self._found_card  = StatCard(self, "FOUND",        "0 / 5", GREEN_500)

        for card in (self._score_card, self._remain_card, self._found_card):
            card.pack(side="left", padx=(0, 10), fill="y")

        # ── Mistake pips card ─────────────────────────────────────────
        pip_card = tk.Frame(self, bg=WHITE,
                            highlightthickness=1,
                            highlightbackground=GRAY_200)
        pip_card.pack(side="left", padx=(0, 10), fill="y")
        tk.Frame(pip_card, bg=RED_500, height=3).pack(fill="x")
        self._pips = MistakePips(pip_card)
        self._pips.pack()

        # ── Timer card ────────────────────────────────────────────────
        self.timer = TimerWidget(self)
        self.timer.pack(side="left", fill="y")

    def update(self, score: int, remaining: int,
               found: int, mistakes: int) -> None:
        self._score_card.set(str(score))
        self._remain_card.set(str(remaining))
        self._found_card.set(f"{found} / 5")
        self._pips.update_pips(mistakes)


# ─────────────────────────────────────────────────────────────────────────────
class PrimaryButton(tk.Frame):
    """Solid teal button with hover darkening."""

    def _init_(self, parent, text: str, command=None,
                 bg: str = TEAL_500, fg: str = WHITE,
                 hover_bg: str = TEAL_600, **kw):
        super()._init_(parent, bg=parent["bg"], bd=0, **kw)
        self._command  = command
        self._bg       = bg
        self._hover_bg = hover_bg

        self._btn = tk.Label(self, text=text, bg=bg, fg=fg,
                             font=FONT_BTN, padx=20, pady=9,
                             cursor="hand2")
        self._btn.pack(fill="both", expand=True)

        for w in (self, self._btn):
            w.bind("<Button-1>", lambda _: self._command() if self._command else None)
            w.bind("<Enter>",    lambda _: self._btn.config(bg=self._hover_bg))
            w.bind("<Leave>",    lambda _: self._btn.config(bg=self._bg))


class GhostButton(tk.Frame):
    """Outlined secondary button — fills on hover."""

    def _init_(self, parent, text: str, command=None,
                 colour: str = TEAL_500, **kw):
        super()._init_(parent, bg=parent["bg"],
                         highlightthickness=1,
                         highlightbackground=colour, **kw)
        self._command = command
        self._colour  = colour

        self._lbl = tk.Label(self, text=text, bg=WHITE, fg=colour,
                             font=FONT_BTN, padx=20, pady=8,
                             cursor="hand2")
        self._lbl.pack(fill="both", expand=True)

        for w in (self, self._lbl):
            w.bind("<Button-1>", lambda _: self._command() if self._command else None)
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    def _on_enter(self, _=None):
        self._lbl.config(bg=self._colour, fg=WHITE)
        self.config(bg=self._colour)

    def _on_leave(self, _=None):
        self._lbl.config(bg=WHITE, fg=self._colour)
        self.config(bg=WHITE)


# ─────────────────────────────────────────────────────────────────────────────
class ImageCanvas(tk.Frame):
    """
    Labelled image panel with header strip, subtitle, and click support.
    """

    DISPLAY_W = 500
    DISPLAY_H = 390

    def _init_(self, parent, title: str, accent: str = TEAL_500,
                 clickable: bool = False,
                 click_callback=None, **kw):
        super()._init_(parent, bg=WHITE,
                         highlightthickness=1,
                         highlightbackground=GRAY_200, **kw)
        self._clickable      = clickable
        self._click_callback = click_callback
        self._photo          = None
        self._circles:       list[tuple] = []
        self._build(title, accent)

    def _build(self, title: str, accent: str) -> None:
        hdr = tk.Frame(self, bg=WHITE)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=accent, width=4).pack(side="left", fill="y")

        title_block = tk.Frame(hdr, bg=WHITE)
        title_block.pack(side="left", fill="both", expand=True,
                         padx=14, pady=10)
        tk.Label(title_block, text=title, bg=WHITE,
                 fg=GRAY_900, font=FONT_HEADING).pack(anchor="w")

        subtitle = ("Click here to mark differences"
                    if self._clickable else "Reference — do not click")
        tk.Label(title_block, text=subtitle, bg=WHITE,
                 fg=GRAY_400, font=FONT_SUBTITLE).pack(anchor="w")

        tk.Frame(self, bg=GRAY_200, height=1).pack(fill="x")

        cursor = "crosshair" if self._clickable else "arrow"
        self._canvas = tk.Canvas(
            self, width=self.DISPLAY_W, height=self.DISPLAY_H,
            bg=GRAY_100, bd=0, highlightthickness=0, cursor=cursor)
        self._canvas.pack()
        self._draw_placeholder()

        if self._clickable:
            self._canvas.bind("<Button-1>", self._on_click)

    def _draw_placeholder(self) -> None:
        self._canvas.create_text(
            self.DISPLAY_W // 2, self.DISPLAY_H // 2,
            text="Load an image to begin",
            fill=GRAY_400, font=FONT_BODY, tags="placeholder")

    def _on_click(self, event) -> None:
        if self._click_callback:
            self._click_callback(event.x, event.y)

    def show_image(self, rgb: np.ndarray) -> None:
        self._canvas.delete("placeholder")
        img         = Image.fromarray(rgb)
        self._photo = ImageTk.PhotoImage(img)
        ih, iw      = rgb.shape[:2]
        ox = (self.DISPLAY_W - iw) // 2
        oy = (self.DISPLAY_H - ih) // 2
        self._canvas.delete("img")
        self._canvas.create_image(ox, oy, anchor="nw",
                                  image=self._photo, tags="img")
        self._canvas.tag_lower("img")
        self._redraw_circles()

    def add_circle(self, cx: int, cy: int, r: int, colour: str) -> None:
        tag = f"circ_{len(self._circles)}"
        self._circles.append((cx, cy, r, colour, tag))
        self._paint_circle(cx, cy, r, colour, tag)

    def _paint_circle(self, cx, cy, r, colour, tag) -> None:
        self._canvas.create_oval(
            cx-r-5, cy-r-5, cx+r+5, cy+r+5,
            outline=colour, width=1, stipple="gray12", tags=tag)
        self._canvas.create_oval(
            cx-r, cy-r, cx+r, cy+r,
            outline=colour, width=2, tags=tag)

    def _redraw_circles(self) -> None:
        for (cx, cy, r, colour, tag) in self._circles:
            self._canvas.delete(tag)
            self._paint_circle(cx, cy, r, colour, tag)

    def clear_circles(self) -> None:
        for (*_, tag) in self._circles:
            self._canvas.delete(tag)
        self._circles.clear()

    def reset(self) -> None:
        self.clear_circles()
        self._canvas.delete("all")
        self._draw_placeholder()


# ─────────────────────────────────────────────────────────────────────────────
class MessageBar(tk.Frame):
    """Bottom status strip with teal dot accent."""

    def _init_(self, parent, **kw):
        super()._init_(parent, bg=GRAY_100,
                         highlightthickness=1,
                         highlightbackground=GRAY_200, **kw)
        tk.Frame(self, bg=GRAY_200, height=1).pack(fill="x")

        row = tk.Frame(self, bg=GRAY_100)
        row.pack(fill="x", padx=16, pady=8)

        tk.Label(row, text="●", bg=GRAY_100, fg=TEAL_500,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        self._var = tk.StringVar(value="Load an image to start playing.")
        tk.Label(row, textvariable=self._var,
                 bg=GRAY_100, fg=GRAY_600,
                 font=FONT_MSG, anchor="w").pack(side="left", fill="x")

    def set(self, text: str) -> None:
        self._var.set(text)