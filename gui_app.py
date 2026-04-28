#!/usr/bin/env python3
"""
Outline Extractor — Desktop GUI (Tkinter)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from outline_extractor import extract_outline, COLOR_PRESETS


# ── Colour swatch helper ──────────────────────────────────────────────────────

BGR_TO_HEX = {
    "neon-cyan":   "#00FFFF",
    "neon-green":  "#00FF00",
    "neon-pink":   "#FF00B4",
    "neon-orange": "#FFA500",
    "neon-yellow": "#FFFF00",
    "neon-blue":   "#0064FF",
    "neon-red":    "#FF0000",
    "neon-purple": "#B400FF",
    "white":       "#FFFFFF",
    "gold":        "#FFD700",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("✦ Outline Extractor")
        self.configure(bg="#0d0d0d")
        self.resizable(True, True)
        self.minsize(700, 580)

        self._input_path = tk.StringVar()
        self._output_path = tk.StringVar()
        self._color_var = tk.StringVar(value="neon-cyan")
        self._thickness = tk.IntVar(value=1)
        self._blur = tk.IntVar(value=3)
        self._canny_low = tk.IntVar(value=30)
        self._canny_high = tk.IntVar(value=100)
        self._glow = tk.BooleanVar(value=True)
        self._glow_strength = tk.IntVar(value=5)

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        PAD = 12
        BG  = "#0d0d0d"
        FG  = "#e0e0e0"
        ACC = "#00FFFF"
        ENT = "#1a1a1a"
        BTN = "#1e1e1e"

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel",       background=BG, foreground=FG, font=("Consolas", 10))
        style.configure("Head.TLabel",  background=BG, foreground=ACC, font=("Consolas", 13, "bold"))
        style.configure("TFrame",       background=BG)
        style.configure("TCheckbutton", background=BG, foreground=FG, font=("Consolas", 10))
        style.configure("TScale",       background=BG, troughcolor="#333")
        style.configure("TCombobox",    fieldbackground=ENT, background=ENT,
                        foreground=FG, selectbackground=ENT, selectforeground=ACC)
        style.map("TCombobox", fieldbackground=[("readonly", ENT)])

        # Title
        ttk.Label(self, text="⬡  OUTLINE EXTRACTOR", style="Head.TLabel").pack(
            pady=(PAD*2, PAD), padx=PAD, anchor="w"
        )

        # ── Main layout ───────────────────────────────────────────────────────
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=(0, PAD))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # Left panel — controls
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, PAD//2))
        left.columnconfigure(1, weight=1)

        def lbl(parent, text, row, col=0, **kw):
            ttk.Label(parent, text=text).grid(
                row=row, column=col, sticky="w", pady=3, padx=(0, 8), **kw
            )

        def entry(parent, var, row):
            e = tk.Entry(parent, textvariable=var, bg=ENT, fg=FG,
                         insertbackground=ACC, relief="flat", font=("Consolas", 10))
            e.grid(row=row, column=1, sticky="ew", pady=3)
            return e

        # Input file
        lbl(left, "Input Image", 0)
        ef = ttk.Frame(left)
        ef.grid(row=0, column=1, sticky="ew", pady=3)
        ef.columnconfigure(0, weight=1)
        tk.Entry(ef, textvariable=self._input_path, bg=ENT, fg=FG,
                 insertbackground=ACC, relief="flat", font=("Consolas", 10)
                 ).grid(row=0, column=0, sticky="ew")
        tk.Button(ef, text="Browse", command=self._browse_input,
                  bg=BTN, fg=ACC, relief="flat", font=("Consolas", 9),
                  activebackground="#222", activeforeground=ACC, cursor="hand2",
                  padx=6).grid(row=0, column=1, padx=(4, 0))

        # Output file
        lbl(left, "Output Path", 1)
        of = ttk.Frame(left)
        of.grid(row=1, column=1, sticky="ew", pady=3)
        of.columnconfigure(0, weight=1)
        tk.Entry(of, textvariable=self._output_path, bg=ENT, fg=FG,
                 insertbackground=ACC, relief="flat", font=("Consolas", 10)
                 ).grid(row=0, column=0, sticky="ew")
        tk.Button(of, text="Browse", command=self._browse_output,
                  bg=BTN, fg=ACC, relief="flat", font=("Consolas", 9),
                  activebackground="#222", activeforeground=ACC, cursor="hand2",
                  padx=6).grid(row=0, column=1, padx=(4, 0))

        # Color picker
        lbl(left, "Outline Color", 2)
        color_frame = ttk.Frame(left)
        color_frame.grid(row=2, column=1, sticky="ew", pady=3)
        color_frame.columnconfigure(0, weight=1)
        self._color_combo = ttk.Combobox(
            color_frame, textvariable=self._color_var,
            values=list(COLOR_PRESETS.keys()) + ["custom hex…"],
            state="readonly", font=("Consolas", 10)
        )
        self._color_combo.grid(row=0, column=0, sticky="ew")
        self._color_combo.bind("<<ComboboxSelected>>", self._on_color_change)

        self._swatch = tk.Label(color_frame, width=4, bg=BGR_TO_HEX["neon-cyan"],
                                relief="flat")
        self._swatch.grid(row=0, column=1, padx=(6, 0))

        # Thickness
        lbl(left, "Thickness", 3)
        tk.Scale(left, variable=self._thickness, from_=1, to=6,
                 orient=tk.HORIZONTAL, bg=BG, fg=FG, troughcolor="#333",
                 highlightthickness=0, relief="flat", font=("Consolas", 9)
                 ).grid(row=3, column=1, sticky="ew", pady=2)

        # Blur
        lbl(left, "Pre-blur", 4)
        tk.Scale(left, variable=self._blur, from_=0, to=15,
                 orient=tk.HORIZONTAL, bg=BG, fg=FG, troughcolor="#333",
                 highlightthickness=0, relief="flat", font=("Consolas", 9)
                 ).grid(row=4, column=1, sticky="ew", pady=2)

        # Canny thresholds
        lbl(left, "Canny Low", 5)
        tk.Scale(left, variable=self._canny_low, from_=1, to=200,
                 orient=tk.HORIZONTAL, bg=BG, fg=FG, troughcolor="#333",
                 highlightthickness=0, relief="flat").grid(row=5, column=1, sticky="ew", pady=2)

        lbl(left, "Canny High", 6)
        tk.Scale(left, variable=self._canny_high, from_=1, to=300,
                 orient=tk.HORIZONTAL, bg=BG, fg=FG, troughcolor="#333",
                 highlightthickness=0, relief="flat").grid(row=6, column=1, sticky="ew", pady=2)

        # Glow toggle
        ttk.Checkbutton(left, text="Enable Neon Glow", variable=self._glow,
                        command=self._toggle_glow).grid(row=7, column=0, columnspan=2,
                                                        sticky="w", pady=6)

        lbl(left, "Glow Strength", 8)
        self._glow_scale = tk.Scale(
            left, variable=self._glow_strength, from_=1, to=10,
            orient=tk.HORIZONTAL, bg=BG, fg=FG, troughcolor="#333",
            highlightthickness=0, relief="flat"
        )
        self._glow_scale.grid(row=8, column=1, sticky="ew", pady=2)

        # Run button
        self._run_btn = tk.Button(
            left, text="⬡  EXTRACT OUTLINE",
            command=self._run,
            bg="#001a1a", fg=ACC, relief="flat",
            font=("Consolas", 11, "bold"),
            activebackground="#003333", activeforeground=ACC,
            cursor="hand2", pady=10
        )
        self._run_btn.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        # Status
        self._status_var = tk.StringVar(value="Ready.")
        tk.Label(left, textvariable=self._status_var, bg=BG,
                 fg="#888", font=("Consolas", 9), anchor="w"
                 ).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        # Right panel — preview
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Preview", font=("Consolas", 10, "bold"),
                  foreground="#555").pack(anchor="w", pady=(0, 6))

        self._preview_canvas = tk.Canvas(right, bg="#080808", relief="flat",
                                         highlightthickness=1,
                                         highlightbackground="#222")
        self._preview_canvas.pack(fill=tk.BOTH, expand=True)
        self._preview_canvas.bind("<Configure>", self._redraw_preview)
        self._preview_img_ref = None
        self._preview_pil = None

    # ── Event handlers ────────────────────────────────────────────────────────

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Select input image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                       ("All files", "*.*")]
        )
        if path:
            self._input_path.set(path)
            stem = Path(path).stem
            self._output_path.set(str(Path(path).parent / f"{stem}_outline.png"))
            self._load_preview(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save output as",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        if path:
            self._output_path.set(path)

    def _on_color_change(self, _=None):
        val = self._color_var.get()
        if val == "custom hex…":
            from tkinter.simpledialog import askstring
            hex_val = askstring("Custom Color", "Enter hex color (e.g. #FF00FF):",
                                parent=self)
            if hex_val:
                self._color_var.set(hex_val)
                self._swatch.configure(bg=hex_val if hex_val.startswith("#") else f"#{hex_val}")
        else:
            self._swatch.configure(bg=BGR_TO_HEX.get(val, "#ffffff"))

    def _toggle_glow(self):
        state = "normal" if self._glow.get() else "disabled"
        self._glow_scale.configure(state=state)

    def _load_preview(self, path):
        if not PIL_AVAILABLE:
            return
        try:
            img = Image.open(path)
            self._preview_pil = img
            self._redraw_preview()
        except Exception:
            pass

    def _redraw_preview(self, _=None):
        if not PIL_AVAILABLE or self._preview_pil is None:
            return
        c = self._preview_canvas
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 10 or ch < 10:
            return
        img = self._preview_pil.copy()
        img.thumbnail((cw, ch), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        self._preview_img_ref = tk_img
        c.delete("all")
        c.create_image(cw // 2, ch // 2, anchor="center", image=tk_img)

    def _run(self):
        inp = self._input_path.get().strip()
        out = self._output_path.get().strip()
        if not inp:
            messagebox.showwarning("Missing Input", "Please select an input image.")
            return
        if not out:
            messagebox.showwarning("Missing Output", "Please specify an output path.")
            return

        self._run_btn.configure(state="disabled", text="Processing…")
        self._status_var.set("Processing…")

        def worker():
            try:
                extract_outline(
                    input_path=inp,
                    output_path=out,
                    color_input=self._color_var.get(),
                    thickness=self._thickness.get(),
                    blur_before=self._blur.get(),
                    canny_low=self._canny_low.get(),
                    canny_high=self._canny_high.get(),
                    glow=self._glow.get(),
                    glow_strength=self._glow_strength.get(),
                )
                self.after(0, self._done_success, out)
            except Exception as e:
                self.after(0, self._done_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _done_success(self, out_path):
        self._run_btn.configure(state="normal", text="⬡  EXTRACT OUTLINE")
        self._status_var.set(f"Saved → {out_path}")
        if PIL_AVAILABLE:
            self._load_preview(out_path)
        messagebox.showinfo("Done!", f"Outline saved to:\n{out_path}")

    def _done_error(self, err):
        self._run_btn.configure(state="normal", text="⬡  EXTRACT OUTLINE")
        self._status_var.set(f"Error: {err}")
        messagebox.showerror("Error", err)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
