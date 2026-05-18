import re
import math
from typing import Optional, List, Tuple

import customtkinter as ctk
from tkinter import filedialog
try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Color tables aligned with common resistor standards
_DIGIT_COLORS = [
    ("Black", "#000000", 0),
    ("Brown", "#8B4513", 1),
    ("Red", "#FF0000", 2),
    ("Orange", "#FF8C00", 3),
    ("Yellow", "#FFD700", 4),
    ("Green", "#008000", 5),
    ("Blue", "#0000FF", 6),
    ("Violet", "#8A2BE2", 7),
    ("Gray", "#808080", 8),
    ("White", "#FFFFFF", 9),
]

_MULTIPLIER_COLORS = [
    ("Silver", "#C0C0C0", 1e-2),
    ("Gold", "#D4AF37", 1e-1),
    ("Black", "#000000", 1e0),
    ("Brown", "#8B4513", 1e1),
    ("Red", "#FF0000", 1e2),
    ("Orange", "#FF8C00", 1e3),
    ("Yellow", "#FFD700", 1e4),
    ("Green", "#008000", 1e5),
    ("Blue", "#0000FF", 1e6),
    ("Violet", "#8A2BE2", 1e7),
    ("Gray", "#808080", 1e8),
    ("White", "#FFFFFF", 1e9),
]

_TOLERANCE_COLORS = [
    ("None", None, 0.20),
    ("Brown", "#8B4513", 0.01),
    ("Red", "#FF0000", 0.02),
    ("Green", "#008000", 0.005),
    ("Blue", "#0000FF", 0.0025),
    ("Violet", "#8A2BE2", 0.001),
    ("Gray", "#808080", 0.0005),
    ("Gold", "#D4AF37", 0.05),
    ("Silver", "#C0C0C0", 0.10),
]

_TEMPCO_COLORS = [
    ("None", None, None),
    ("Brown", "#8B4513", 100),
    ("Red", "#FF0000", 50),
    ("Orange", "#FF8C00", 15),
    ("Yellow", "#FFD700", 25),
    ("Blue", "#0000FF", 10),
    ("Violet", "#8A2BE2", 5),
]

_EIA96_CODES = {
    '01': 100, '02': 102, '03': 105, '04': 107, '05': 110, '06': 113, '07': 115, '08': 118, '09': 121, '10': 124,
    '11': 127, '12': 130, '13': 133, '14': 137, '15': 140, '16': 143, '17': 147, '18': 150, '19': 154, '20': 158,
    '21': 162, '22': 165, '23': 169, '24': 174, '25': 178, '26': 182, '27': 187, '28': 191, '29': 196, '30': 200,
    '31': 205, '32': 210, '33': 215, '34': 221, '35': 226, '36': 232, '37': 237, '38': 243, '39': 249, '40': 255,
    '41': 261, '42': 267, '43': 274, '44': 280, '45': 287, '46': 294, '47': 301, '48': 309, '49': 316, '50': 324,
    '51': 332, '52': 340, '53': 348, '54': 357, '55': 365, '56': 374, '57': 383, '58': 392, '59': 402, '60': 412,
    '61': 422, '62': 432, '63': 442, '64': 453, '65': 464, '66': 475, '67': 487, '68': 499, '69': 511, '70': 523,
    '71': 536, '72': 549, '73': 562, '74': 576, '75': 590, '76': 604, '77': 619, '78': 634, '79': 649, '80': 665,
    '81': 681, '82': 698, '83': 715, '84': 732, '85': 750, '86': 768, '87': 787, '88': 806, '89': 825, '90': 845,
    '91': 866, '92': 887, '93': 909, '94': 931, '95': 953, '96': 976
}
_EIA96_MULTIPLIERS = {
    'Y': 0.01, 'X': 0.1, 'A': 1, 'B': 10, 'C': 100, 'D': 1000, 'E': 10000, 'F': 100000
}

def _color_names(options) -> List[str]:
    return [n for (n, _hex, _v) in options]

def _digit_from_name(name: str) -> Optional[int]:
    for n, _hex, v in _DIGIT_COLORS:
        if n == name:
            return int(v)
    return None

def _mult_from_name(name: str) -> Optional[float]:
    for n, _hex, v in _MULTIPLIER_COLORS:
        if n == name:
            return float(v)
    return None

def _tol_from_name(name: str) -> Optional[float]:
    for n, _hex, v in _TOLERANCE_COLORS:
        if n == name:
            return float(v)
    return None

class resistor_colors_window(ctk.CTkToplevel):
    def __init__(self, master_root):
        super().__init__(master_root)
        self.title("Resistor Calculator")
        self.geometry("900x600")
        self.minsize(720, 500)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # state
        self.auto_compute_enabled = ctk.BooleanVar(value=True)
        self.segmented_mode = ctk.StringVar(value="5")
        self.mode_text = ctk.StringVar(value="Forward")
        self.reverse_mode_text = ctk.StringVar(value="5")
        self.reverse_value_text = ctk.StringVar(value="")
        self.reverse_tolerance_text = ctk.StringVar(value="5%")
        self.reverse_found_bands: List[str] = []
        
        self.smd_code_text = ctk.StringVar(value="")
        self.smd_type = ctk.StringVar(value="Auto")

        self._on_change_after: Optional[str] = None
        self._smd_change_after: Optional[str] = None

        # Tabview
        self.tab_ctrl = ctk.CTkTabview(self)
        self.tab_ctrl.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tab_tht = self.tab_ctrl.add("Color Bands (THT)")
        self.tab_smd = self.tab_ctrl.add("SMD Codes")
        
        self._setup_tht_tab()
        self._setup_smd_tab()
        
        self.band_option_widgets: List[ctk.CTkComboBox] = []
        self.render_color_selectors()

        # binds
        self.bind("<KeyRelease>", lambda _e: self._on_any_change())
        self.reverse_value_entry.bind("<Return>", lambda _e: self.find_bands_for_value())
        self.canvas.bind("<Configure>", lambda e: self.update_color_preview())
        
        self.smd_code_entry.bind("<KeyRelease>", lambda _e: self._on_smd_change())

        self._install_responsive_layout()

    def _setup_tht_tab(self):
        parent = self.tab_tht
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        # header
        ctk.CTkLabel(parent, text="Through-Hole Resistor Color Codes", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))

        # info
        self.info_label = ctk.CTkLabel(
            parent,
            text="Select band colors or reverse-search by value.",
            wraplength=560, anchor="w", justify="left"
        )
        self.info_label.grid(row=1, column=0, sticky="we")

        # selectors + preview row
        top_row = ctk.CTkFrame(parent)
        top_row.grid(row=2, column=0, sticky="nsew", pady=(6, 6))
        top_row.grid_columnconfigure(0, weight=1)
        top_row.grid_columnconfigure(1, weight=1)

        # selectors panel
        self.selectors_frame = ctk.CTkFrame(top_row)
        self.selectors_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.selectors_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.selectors_frame, text="Band count:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.segmented = ctk.CTkSegmentedButton(
            self.selectors_frame,
            values=["4", "5", "6"],
            variable=self.segmented_mode,
            command=lambda _=None: self.render_color_selectors(),
        )
        self.segmented.grid(row=0, column=1, sticky="we", padx=6, pady=6)

        self._selectors_inner = ctk.CTkFrame(self.selectors_frame)
        self._selectors_inner.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.selectors_frame.grid_rowconfigure(1, weight=1)

        # preview panel
        self.preview_frame = ctk.CTkFrame(top_row)
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.preview_frame, text="Visual Preview", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=6, pady=(6, 2)
        )
        
        self.canvas = ctk.CTkCanvas(self.preview_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        
        # actions
        self.actions_row = ctk.CTkFrame(self.preview_frame)
        self.actions_row.grid(row=2, column=0, sticky="we", padx=6, pady=(0, 6))
        self.actions_row.grid_columnconfigure(4, weight=1)

        self.button_compute = ctk.CTkButton(self.actions_row, text="Compute", command=self.compute_resistor_value)
        self.button_compute.grid(row=0, column=0, padx=4)
        self.button_reset = ctk.CTkButton(self.actions_row, text="Reset", command=self.reset_selectors)
        self.button_reset.grid(row=0, column=1, padx=4)
        self.checkbox_auto_compute = ctk.CTkCheckBox(self.actions_row, text="Auto-compute", variable=self.auto_compute_enabled)
        self.checkbox_auto_compute.grid(row=0, column=2, padx=4)
        ctk.CTkButton(self.actions_row, text="Save Image", command=lambda: self.save_diagram(self.canvas), width=80, fg_color="green").grid(row=0, column=3, padx=4)
        self.button_copy = ctk.CTkButton(self.actions_row, text="Copy", width=60, command=lambda: self.copy_to_clipboard("both"))
        self.button_copy.grid(row=0, column=4, padx=4, sticky="e")

        # output
        self.result_label = ctk.CTkLabel(parent, text="Result:", anchor="w")
        self.result_label.grid(row=3, column=0, sticky="we", pady=(4, 0))
        self.output_textbox = ctk.CTkTextbox(parent, height=120)
        self.output_textbox.grid(row=4, column=0, sticky="nsew", pady=(0, 6))

        # reverse search tools
        self.reverse_frame = ctk.CTkFrame(parent)
        self.reverse_frame.grid(row=5, column=0, sticky="we")
        for c in range(0, 8):
            self.reverse_frame.grid_columnconfigure(c, weight=0)
        self.reverse_frame.grid_columnconfigure(5, weight=1)

        # Fix the bug by instantiating reverse_title first
        self.reverse_title = ctk.CTkLabel(self.reverse_frame, text="Reverse Band Search", font=ctk.CTkFont(weight="bold"))
        self.reverse_title.grid(row=0, column=0, columnspan=8, sticky="w", padx=6, pady=(6, 2))
        
        from toolkit.windows.smart_entry import SmartEntry

        ctk.CTkLabel(self.reverse_frame, text="Target (Ω):").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.reverse_value_entry = SmartEntry(self.reverse_frame, textvariable=self.reverse_value_text, min_val=0)
        self.reverse_value_entry.configure(placeholder_text="e.g. 4.7k")
        self.reverse_value_entry.grid(row=1, column=1, sticky="we", padx=6, pady=4)

        ctk.CTkLabel(self.reverse_frame, text="Tol:").grid(row=1, column=2, sticky="e", padx=6)
        self.reverse_tolerance_menu = ctk.CTkComboBox(
            self.reverse_frame,
            values=["0.05%", "0.1%", "0.25%", "0.5%", "1%", "2%", "5%", "10%", "20%"],
            variable=self.reverse_tolerance_text,
            state="readonly", width=80
        )
        self.reverse_tolerance_menu.grid(row=1, column=3, sticky="we", padx=6)

        ctk.CTkLabel(self.reverse_frame, text="Bands:").grid(row=1, column=4, sticky="e", padx=6)
        self.reverse_mode_segmented = ctk.CTkSegmentedButton(self.reverse_frame, values=["4", "5", "6"], variable=self.reverse_mode_text, width=80)
        self.reverse_mode_segmented.grid(row=1, column=5, sticky="w", padx=6)

        self.button_find_bands = ctk.CTkButton(self.reverse_frame, text="Find", width=60, command=self.find_bands_for_value)
        self.button_find_bands.grid(row=1, column=6, padx=6)
        self.button_apply_found = ctk.CTkButton(self.reverse_frame, text="Apply", width=60, command=self._apply_found_safe)
        self.button_apply_found.grid(row=1, column=7, padx=6)

        self.reverse_found_label = ctk.CTkLabel(self.reverse_frame, text="Found: —", anchor="w")
        self.reverse_found_label.grid(row=2, column=0, columnspan=8, sticky="we", padx=6, pady=(0, 6))

        self.footer_note = ctk.CTkLabel(parent, text="Note: 4-band uses 2 significant digits; 5/6-band uses 3.", anchor="w")
        self.footer_note.grid(row=6, column=0, sticky="we")

    def _setup_smd_tab(self):
        parent = self.tab_smd
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(parent, text="SMD Resistor Code Calculator", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        
        # Input Area
        input_frame = ctk.CTkFrame(parent)
        input_frame.grid(row=1, column=0, sticky="ew", pady=10)
        input_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(input_frame, text="SMD Code:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.smd_code_entry = ctk.CTkEntry(input_frame, textvariable=self.smd_code_text, placeholder_text="e.g. 103, 4702, 01C", font=ctk.CTkFont(size=16))
        self.smd_code_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(input_frame, text="Type:").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.smd_type_menu = ctk.CTkOptionMenu(input_frame, variable=self.smd_type, values=["Auto", "3-Digit", "4-Digit", "EIA-96"], command=lambda _: self._on_smd_change())
        self.smd_type_menu.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        
        # Split Panels
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        
        # Visual Panel
        vis_frame = ctk.CTkFrame(content)
        vis_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        vis_frame.grid_rowconfigure(1, weight=1)
        vis_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(vis_frame, text="Visual").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkButton(vis_frame, text="Save", command=lambda: self.save_diagram(self.smd_canvas), width=60, height=24, fg_color="green").grid(row=0, column=1, sticky="e", padx=5, pady=5)
        self.smd_canvas = ctk.CTkCanvas(vis_frame, bg="#2b2b2b", highlightthickness=0)
        self.smd_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.smd_canvas.bind("<Configure>", lambda e: self._draw_smd_visual())

        # Result Panel
        res_frame = ctk.CTkFrame(content)
        res_frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        res_frame.grid_columnconfigure(0, weight=1)
        res_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(res_frame, text="Result").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.smd_result_box = ctk.CTkTextbox(res_frame, font=ctk.CTkFont(size=14))
        self.smd_result_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(parent, text="Supported: 3-digit (Standard), 4-digit (Precision), EIA-96 (1% Precision)", text_color="gray").grid(row=3, column=0, sticky="w", pady=5)

    def render_color_selectors(self):
        for child in self._selectors_inner.winfo_children():
            child.destroy()
        self.band_option_widgets.clear()

        try:
            bands = int(self.segmented_mode.get())
        except Exception:
            bands = 5

        row = 0
        ctk.CTkLabel(self._selectors_inner, text=f"{bands}-band selection", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=6, pady=(6, 2)
        )
        row += 1

        def add_selector(label_text: str, values: List[str], default_idx: int = 0) -> ctk.CTkComboBox:
            nonlocal row
            ctk.CTkLabel(self._selectors_inner, text=label_text).grid(row=row, column=0, sticky="e", padx=6, pady=4)
            cb = ctk.CTkComboBox(self._selectors_inner, values=values, state="readonly")
            cb.grid(row=row, column=1, sticky="we", padx=6, pady=4)
            try:
                cb.set(values[default_idx])
            except Exception:
                pass
            cb.bind("<<ComboboxSelected>>", lambda _e: self._on_any_change())
            self.band_option_widgets.append(cb)
            row += 1
            return cb

        if bands == 4:
            add_selector("Digit 1", _color_names(_DIGIT_COLORS), 1)
            add_selector("Digit 2", _color_names(_DIGIT_COLORS), 0)
            add_selector("Multiplier", _color_names(_MULTIPLIER_COLORS), 3)
            add_selector("Tolerance", _color_names(_TOLERANCE_COLORS), 7)
        elif bands == 5:
            add_selector("Digit 1", _color_names(_DIGIT_COLORS), 1)
            add_selector("Digit 2", _color_names(_DIGIT_COLORS), 0)
            add_selector("Digit 3", _color_names(_DIGIT_COLORS), 0)
            add_selector("Multiplier", _color_names(_MULTIPLIER_COLORS), 2)
            add_selector("Tolerance", _color_names(_TOLERANCE_COLORS), 1)
        else:
            add_selector("Digit 1", _color_names(_DIGIT_COLORS), 1)
            add_selector("Digit 2", _color_names(_DIGIT_COLORS), 0)
            add_selector("Digit 3", _color_names(_DIGIT_COLORS), 0)
            add_selector("Multiplier", _color_names(_MULTIPLIER_COLORS), 2)
            add_selector("Tolerance", _color_names(_TOLERANCE_COLORS), 1)
            add_selector("Tempco", _color_names(_TEMPCO_COLORS), 0)

        self._selectors_inner.grid_columnconfigure(1, weight=1)
        self.update_color_preview()
        self._on_any_change()

    def _on_any_change(self, *_):
        try:
            if self._on_change_after is not None:
                self.after_cancel(self._on_change_after)
        except Exception:
            pass
        try:
            self._on_change_after = self.after(120, self._perform_recompute_safe)
        except Exception:
            pass

    def _perform_recompute_safe(self):
        self._on_change_after = None
        try:
            self.update_color_preview()
        except Exception:
            pass
        try:
            if self.auto_compute_enabled.get():
                self.compute_resistor_value()
        except Exception:
            pass

    def update_color_preview(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10: return

        bands = [cb.get() for cb in self.band_option_widgets]
        if not bands: return
        self._draw_resistor(w, h, bands)

    def _draw_resistor(self, w, h, band_names):
        body_color = "#e5cfa8"
        if len(band_names) >= 5 and band_names[4] not in ("Gold", "Silver", "None"):
             body_color = "#7da5c9"
        
        cx, cy = w / 2, h / 2
        body_w = w * 0.6
        body_h = h * 0.4
        x1, y1 = cx - body_w/2, cy - body_h/2
        x2, y2 = cx + body_w/2, cy + body_h/2
        
        # Leads
        self.canvas.create_line(0, cy, x1, cy, width=4, fill="#b0b0b0")
        self.canvas.create_line(x2, cy, w, cy, width=4, fill="#b0b0b0")
        
        # Body
        rad = body_h * 0.2
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=body_color, outline=body_color)
        self.canvas.create_oval(x1-rad, y1, x1+rad, y2, fill=body_color, outline=body_color)
        self.canvas.create_oval(x2-rad, y1, x2+rad, y2, fill=body_color, outline=body_color)
        
        def get_color(name):
             for coll in (_DIGIT_COLORS, _MULTIPLIER_COLORS, _TOLERANCE_COLORS, _TEMPCO_COLORS):
                 for n, hx, _ in coll:
                     if n == name: return hx
             return "#333" if name != "None" else ""

        n_bands = len(band_names)
        if n_bands == 4:
            positions = [0.25, 0.4, 0.55, 0.8]
        elif n_bands == 5:
            positions = [0.15, 0.3, 0.45, 0.6, 0.85]
        else:
            positions = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9]
            
        for i, name in enumerate(band_names):
            c = get_color(name)
            if not c: continue
            px = x1 + positions[i] * body_w
            bw = body_w * 0.08
            self.canvas.create_rectangle(px - bw/2, y1, px + bw/2, y2, fill=c, outline=c)

    def compute_resistor_value(self):
        bands = [cb.get() for cb in self.band_option_widgets]
        if not bands:
            return
        count = len(bands)
        try:
            if count == 4:
                d1 = _digit_from_name(bands[0])
                d2 = _digit_from_name(bands[1])
                mult = _mult_from_name(bands[2])
                tol = _tol_from_name(bands[3])
                if None in (d1, d2, mult, tol):
                    raise ValueError("Incomplete selection")
                value = (d1 * 10 + d2) * mult
            elif count in (5, 6):
                d1 = _digit_from_name(bands[0])
                d2 = _digit_from_name(bands[1])
                d3 = _digit_from_name(bands[2])
                mult = _mult_from_name(bands[3])
                tol = _tol_from_name(bands[4])
                if None in (d1, d2, d3, mult, tol):
                    raise ValueError("Incomplete selection")
                value = (d1 * 100 + d2 * 10 + d3) * mult
            else:
                raise ValueError("Unsupported band count")

            v_str = self.format_ohms_si(value)
            lo, hi = self.compute_tolerance_bounds(value, tol)
            tol_pct = tol * 100.0

            lines = [
                f"Value: {v_str}",
                f"Tolerance: ±{tol_pct:.2f}%",
                f"Bounds: {self.format_ohms_si(lo)} … {self.format_ohms_si(hi)}",
                f"Bands: {' | '.join(bands)}",
            ]
            if count == 6:
                lines.append(f"Tempco: {bands[5]}")

            self.result_label.configure(text=f"Result: {v_str}  (±{tol_pct:.2f}%)")
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("end", "\n".join(lines))
        except Exception as e:
            self.result_label.configure(text="Result: —")
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("end", f"Error: {e}")

    def parse_ohms_text(self, text: str) -> Optional[float]:
        if not text:
            return None
        s = text.strip().replace("Ω", "").replace("ohm", "").replace("Ohm", "").replace("OHM", "")
        m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*([kKmMgG]?)\s*$", s)
        if m:
            val = float(m.group(1))
            mult = {"": 1.0, "k": 1e3, "m": 1e6, "g": 1e9}[m.group(2).lower()]
            return val * mult
        m2 = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*[rR]\s*$", s)
        if m2:
            return float(m2.group(1))
        try:
            return float(s)
        except Exception:
            return None

    def _nearest_multiplier_color(self, ohms: float, digits: int) -> Tuple[str, float]:
        targets = (10.0, 99.9) if digits == 2 else (100.0, 999.9)
        best = None
        for n, _hex, m in _MULTIPLIER_COLORS:
            sig = ohms / m
            if sig < targets[0]:
                dist = targets[0] - sig
            elif sig > targets[1]:
                dist = sig - targets[1]
            else:
                dist = 0.0
            if best is None or dist < best[0]:
                best = (dist, n, m)
        return best[1], best[2]

    def compute_bands_from_value(self, ohms: float, bands: int) -> Tuple[List[str], float]:
        if ohms <= 0:
            return [], 0.0

        if bands == 4:
            target_low, target_high, digits = 10.0, 99.9, 2
        else:
            target_low, target_high, digits = 100.0, 999.9, 3

        chosen = None
        for n, _hex, m in sorted(_MULTIPLIER_COLORS, key=lambda x: x[2]):
            sig = ohms / m
            if target_low <= sig <= target_high:
                chosen = (n, m)
                break
        if chosen is None:
            chosen = self._nearest_multiplier_color(ohms, digits)
        if isinstance(chosen, tuple) and len(chosen) == 2:
            mult_name, mult_val = chosen
        else:
            mult_name, mult_val = chosen[0], chosen[1]

        sig = ohms / mult_val
        sig_rounded = int(round(sig))

        if digits == 2 and sig_rounded >= 100:
            mult_name, mult_val = self._nearest_multiplier_color(ohms * 0.1, digits)
            sig_rounded = int(round(ohms / mult_val))
        if digits == 3 and sig_rounded >= 1000:
            mult_name, mult_val = self._nearest_multiplier_color(ohms * 0.1, digits)
            sig_rounded = int(round(ohms / mult_val))

        s = str(sig_rounded).zfill(digits)
        def dcolor(ch: str) -> str:
            d = int(ch)
            return _DIGIT_COLORS[d][0]

        names: List[str] = []
        if digits == 2:
            names.extend([dcolor(s[0]), dcolor(s[1])])
        else:
            names.extend([dcolor(s[0]), dcolor(s[1]), dcolor(s[2])])
        names.append(mult_name)
        return names, mult_val

    def find_bands_for_value(self):
        value = self.reverse_value_entry.get_value()
        if value is None:
            self.reverse_found_bands = []
            self.reverse_found_label.configure(text="Found: invalid value")
            return
        try:
            bands = int(self.reverse_mode_text.get())
        except Exception:
            bands = 5

        names, _mult = self.compute_bands_from_value(value, bands)
        tol_map = {
            "0.05%": "Gray",
            "0.1%": "Violet",
            "0.25%": "Blue",
            "0.5%": "Green",
            "1%": "Brown",
            "2%": "Red",
            "5%": "Gold",
            "10%": "Silver",
            "20%": "None",
        }
        tol_name = tol_map.get(self.reverse_tolerance_text.get().strip(), "Gold")

        if bands == 4:
            names = names[:3]
            names.append(tol_name)
        elif bands in (5, 6):
            names = names[:4]
            names.append(tol_name)
            if bands == 6:
                names.append("None")

        self.reverse_found_bands = names
        self.reverse_found_label.configure(text=f"Found: {' | '.join(names)}")

    def _apply_found_safe(self):
        try:
            self.apply_found_bands_to_selectors(self.reverse_found_bands)
        except Exception:
            pass

    def apply_found_bands_to_selectors(self, bands):
        try:
            widgets = self.band_option_widgets
        except Exception:
            return
        if not widgets or not bands:
            return
        n = min(len(widgets), len(bands))
        for i in range(n):
            try:
                widgets[i].set(bands[i])
            except Exception:
                pass
        for j in range(n, len(widgets)):
            try:
                widgets[j].set("")
            except Exception:
                pass
        self._on_any_change()

    def copy_bands_to_clipboard(self):
        try:
            return self.copy_to_clipboard("bands")
        except Exception:
            pass

    def copy_result_to_clipboard(self):
        try:
            return self.copy_to_clipboard("result")
        except Exception:
            pass

    def copy_to_clipboard(self, what: str = "both"):
        header = ""
        details = ""
        try:
            header = self.result_label.cget("text")
        except Exception:
            header = ""
        try:
            details = self._safe_widget_get_text(self.output_textbox)
        except Exception:
            details = ""
        bands_str = ""
        try:
            if self.band_option_widgets:
                names = [w.get() for w in self.band_option_widgets]
                bands_str = " | ".join(n for n in names if n)
            elif self.reverse_found_bands:
                if isinstance(self.reverse_found_bands, (list, tuple)):
                    bands_str = " | ".join(map(str, self.reverse_found_bands))
                else:
                    bands_str = str(self.reverse_found_bands)
        except Exception:
            pass

        if what == "result":
            text = (header + ("\n" + details if details else "")).strip()
        elif what == "bands":
            text = f"Bands: {bands_str}".strip() if bands_str else ""
        else:
            parts = []
            if header:
                parts.append(header)
            if details:
                parts.append(details)
            if bands_str:
                parts.append(f"Bands: {bands_str}")
            text = "\n".join(parts).strip()

        try:
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            try:
                self.winfo_toplevel().clipboard_clear()
                self.winfo_toplevel().clipboard_append(text)
            except Exception:
                pass

    def _safe_widget_get_text(self, widget) -> str:
        if not widget:
            return ""
        for rng in (("1.0", "end"), ("0.0", "end")):
            try:
                val = widget.get(*rng)
                if isinstance(val, str):
                     return val.strip()
            except Exception:
                pass
        try:
            return str(widget.cget("text")).strip()
        except Exception:
            pass
        for getter in ("get", "get_value"):
            try:
                v = getattr(widget, getter)()
                return (v if isinstance(v, str) else str(v)).strip()
            except Exception:
                pass
        return ""

    def reset_selectors(self):
        try:
            m = int(self.segmented_mode.get())
        except Exception:
            m = 5
        self.segmented_mode.set(str(m))
        self.render_color_selectors()
        self.result_label.configure(text="Result:")
        self.output_textbox.delete("1.0", "end")

    def fill_example_values(self, band_count: int = 5):
        self.segmented_mode.set(str(band_count))
        self.render_color_selectors()
        presets = {
            4: ["Brown", "Black", "Red", "Gold"],
            5: ["Brown", "Black", "Black", "Brown", "Brown"],
            6: ["Red", "Violet", "Brown", "Red", "Brown", "None"],
        }
        vals = presets.get(band_count)
        if not vals:
            return
        for i, name in enumerate(vals):
            try:
                self.band_option_widgets[i].set(name)
            except Exception:
                pass
        self.update_color_preview()
        try:
            if self.auto_compute_enabled.get():
                self.compute_resistor_value()
        except Exception:
            pass

    def format_ohms_si(self, ohms: float) -> str:
        if ohms is None:
            return "—"
        v = abs(ohms)
        if v >= 1e9:
            return f"{ohms/1e9:.6g} GΩ"
        if v >= 1e6:
            return f"{ohms/1e6:.6g} MΩ"
        if v >= 1e3:
            return f"{ohms/1e3:.6g} kΩ"
        if v >= 1:
            return f"{ohms:.6g} Ω"
        if v >= 1e-3:
            return f"{ohms/1e-3:.6g} mΩ"
        if v >= 1e-6:
            return f"{ohms/1e-6:.6g} µΩ"
        return f"{ohms:.6g} Ω"

    def compute_tolerance_bounds(self, value: float, tolerance: float) -> Tuple[float, float]:
        delta = abs(value) * float(tolerance)
        return value - delta, value + delta

    def _install_responsive_layout(self):
        def _on_resize(_e=None):
            try:
                width = self.winfo_width()
            except Exception:
                width = 800
            wrap = max(260, int(width * 0.45))
            for attr in ("header_label", "info_label", "footer_note", "reverse_title", "reverse_found_label"):
                try:
                    lbl = getattr(self, attr, None)
                    if lbl:
                        lbl.configure(wraplength=wrap)
                except Exception:
                    pass

        try:
            self.bind("<Configure>", _on_resize)
            _on_resize()
        except Exception:
            pass

    # ------------------ SMD LOGIC ------------------
    def _on_smd_change(self):
        try:
            if self._smd_change_after:
                self.after_cancel(self._smd_change_after)
        except Exception:
            pass
        self._smd_change_after = self.after(200, self._compute_smd)
    
    def _compute_smd(self):
        text = self.smd_code_text.get().upper().strip()
        mode = self.smd_type.get()
        
        self.smd_result_box.configure(state="normal")
        self.smd_result_box.delete("1.0", "end")
        self._draw_smd_visual()
        
        if not text:
            self.smd_result_box.configure(state="disabled")
            return
            
        value_ohm = None
        tol_str = ""
        desc = ""
        
        try:
            if mode in ("Auto", "EIA-96") and len(text) == 3 and text[:2].isdigit() and text[2].isalpha():
                code = text[:2]
                mult_char = text[2]
                if code in _EIA96_CODES and mult_char in _EIA96_MULTIPLIERS:
                    base = _EIA96_CODES[code]
                    mult = _EIA96_MULTIPLIERS[mult_char]
                    value_ohm = base * mult
                    tol_str = "±1%"
                    desc = f"EIA-96: Code {code} ({base}) x {mult}"
            
            if value_ohm is None and mode in ("Auto", "3-Digit"):
                if re.match(r'^\d{3}$', text):
                    d1 = int(text[0])
                    d2 = int(text[1])
                    mult = int(text[2])
                    value_ohm = (d1 * 10 + d2) * (10 ** mult)
                    tol_str = "±5%"
                    desc = "3-Digit Standard"
                elif 'R' in text and len(text) <= 4:
                     val_str = text.replace('R', '.')
                     try:
                          value_ohm = float(val_str)
                          tol_str = "±5%"
                          desc = "3-Digit (R decimal)"
                     except: pass
            
            if value_ohm is None and mode in ("Auto", "4-Digit"):
                if re.match(r'^\d{4}$', text):
                     d1 = int(text[0])
                     d2 = int(text[1])
                     d3 = int(text[2])
                     mult = int(text[3])
                     value_ohm = (d1 * 100 + d2 * 10 + d3) * (10 ** mult)
                     tol_str = "±1%"
                     desc = "4-Digit Precision"
            
            if value_ohm is None and "R" in text:
                 try:
                     val_str = text.replace('R', '.')
                     value_ohm = float(val_str)
                     if len(text) == 4:
                          tol_str = "±1%"
                          desc = "4-Digit (R decimal)"
                 except: pass

            if value_ohm is not None:
                fmt_val = self.format_ohms_si(value_ohm)
                res = f"Value: {fmt_val}\nTolerance: {tol_str}\nType: {desc}"
                self.smd_result_box.insert("end", res)
            else:
                self.smd_result_box.insert("end", "Unknown Code or Format")
                
        except Exception as e:
            self.smd_result_box.insert("end", f"Error: {e}")
            
        self.smd_result_box.configure(state="disabled")

    def _draw_smd_visual(self):
        c = self.smd_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10: return
        
        cx, cy = w/2, h/2
        bw = w * 0.6
        bh = h * 0.4
        
        x1, y1 = cx - bw/2, cy - bh/2
        x2, y2 = cx + bw/2, cy + bh/2
        
        c.create_rectangle(x1, y1, x2, y2, fill="#1a1a1a", outline="#333", width=2)
        term_w = bw * 0.15
        c.create_rectangle(x1, y1, x1+term_w, y2, fill="#C0C0C0", outline="#888")
        c.create_rectangle(x2-term_w, y1, x2, y2, fill="#C0C0C0", outline="#888")
        
        code = self.smd_code_text.get().upper().strip()
        if code:
            c.create_text(cx, cy, text=code, fill="white", font=("Arial", int(bh * 0.5), "bold"))

    def save_diagram(self, canvas):
        if not HAS_PIL:
            print("Error: PIL not installed.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG Image", "*.png")])
        if not file_path: return

        try:
            ps_data = canvas.postscript(colormode="color")
            img = Image.open(io.BytesIO(ps_data.encode("utf-8")))
            img.save(file_path, "png")
        except Exception as e:
            print(f"Save diagram error: {e}")
