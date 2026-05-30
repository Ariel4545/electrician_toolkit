# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk
import math
from windows.tool_window import tool_window
from utils.parsing import parse_value, format_value
from tkinter import filedialog
try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# E24 Series Base (1.0 to 9.1)
_E24_BASE = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 
    2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 
    6.8, 7.5, 8.2, 9.1
]

class voltage_divider_window(tool_window):
    def __init__(self, master_root):
        super().__init__(master_root, 'Voltage Divider Calculator', '700x550')
        
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tab_fwd = self.tab_view.add("Calculate Vout")
        self.tab_rev = self.tab_view.add("Find Resistors")
        
        self._setup_forward_ui()
        self._setup_reverse_ui()

    # ------------------ FORWARD TAB ------------------
    def _setup_forward_ui(self):
        t = self.tab_fwd
        t.grid_columnconfigure(1, weight=1)
        
        # Variables
        self.fwd_vin = ctk.StringVar()
        self.fwd_r1 = ctk.StringVar()
        self.fwd_r2 = ctk.StringVar()
        
        self.fwd_vout = ctk.StringVar(value="---")
        self.fwd_current = ctk.StringVar(value="---")
        self.fwd_p1 = ctk.StringVar(value="---")
        self.fwd_p2 = ctk.StringVar(value="---")
        
        from windows.smart_entry import SmartEntry

        # Inputs
        ctk.CTkLabel(t, text="Source Voltage (Vin):").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.entry_fwd_vin = SmartEntry(t, textvariable=self.fwd_vin, placeholder_text="e.g. 5")
        self.entry_fwd_vin.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ctk.CTkLabel(t, text="Resistor 1 (R1) Ω:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.entry_fwd_r1 = SmartEntry(t, textvariable=self.fwd_r1, placeholder_text="e.g. 1k", min_val=0)
        self.entry_fwd_r1.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        ctk.CTkLabel(t, text="Resistor 2 (R2) Ω:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.entry_fwd_r2 = SmartEntry(t, textvariable=self.fwd_r2, placeholder_text="e.g. 10k", min_val=0)
        self.entry_fwd_r2.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        
        ctk.CTkButton(t, text="Calculate", command=self._calc_forward).grid(row=3, column=0, columnspan=2, pady=10)
        ctk.CTkButton(t, text="Save Schematic", command=lambda: self.save_schematic(self.fwd_canvas), fg_color="green").grid(row=6, column=0, columnspan=2, pady=5)
        
        # Results
        res_frame = ctk.CTkFrame(t, fg_color="transparent")
        res_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')
        res_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(res_frame, text="Vout:", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky='e', padx=10)
        ctk.CTkLabel(res_frame, textvariable=self.fwd_vout, font=("Arial", 14, "bold"), text_color="#2ecc71").grid(row=0, column=1, sticky='w')
        
        ctk.CTkLabel(res_frame, text="Current:").grid(row=1, column=0, sticky='e', padx=10)
        ctk.CTkLabel(res_frame, textvariable=self.fwd_current).grid(row=1, column=1, sticky='w')
        
        ctk.CTkLabel(res_frame, text="Power (R1):").grid(row=2, column=0, sticky='e', padx=10)
        ctk.CTkLabel(res_frame, textvariable=self.fwd_p1).grid(row=2, column=1, sticky='w')
        
        ctk.CTkLabel(res_frame, text="Power (R2):").grid(row=3, column=0, sticky='e', padx=10)
        ctk.CTkLabel(res_frame, textvariable=self.fwd_p2).grid(row=3, column=1, sticky='w')

        # Canvas
        self.fwd_canvas = ctk.CTkCanvas(t, bg="#1e1e1e", highlightthickness=0, height=200)
        self.fwd_canvas.grid(row=5, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        t.grid_rowconfigure(5, weight=1)
        
        self.fwd_canvas.bind("<Configure>", lambda e: self._draw_schematic_fwd())

    def _calc_forward(self):
        try:
            vin = self.entry_fwd_vin.get_value()
            r1 = self.entry_fwd_r1.get_value()
            r2 = self.entry_fwd_r2.get_value()
            
            if r1 is None or r2 is None or vin is None:
                self.fwd_vout.set("Invalid Input")
                return
            
            total_r = r1 + r2
            if total_r == 0:
                self.fwd_vout.set("Short!")
                return
            
            vout = vin * (r2 / total_r)
            i = vin / total_r
            p1 = i*i * r1
            p2 = i*i * r2
            
            self.fwd_vout.set(f"{vout:.3g} V")
            self.fwd_current.set(format_value(i, "A"))
            self.fwd_p1.set(format_value(p1, "W"))
            self.fwd_p2.set(format_value(p2, "W"))
            
            self._draw_schematic_fwd(vin, r1, r2, vout)
            
        except Exception:
            self.fwd_vout.set("Error")

    def _draw_schematic_fwd(self, vin=None, r1=None, r2=None, vout=None):
        self._draw_schematic(self.fwd_canvas, vin, r1, r2, vout)

    # ------------------ REVERSE TAB ------------------
    def _setup_reverse_ui(self):
        t = self.tab_rev
        t.grid_columnconfigure(1, weight=1)
        
        # Vars
        self.rev_vin = ctk.StringVar()
        self.rev_vout = ctk.StringVar()
        
        from windows.smart_entry import SmartEntry

        # Inputs
        ctk.CTkLabel(t, text="Source Voltage (Vin):").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.entry_rev_vin = SmartEntry(t, textvariable=self.rev_vin, placeholder_text="e.g. 12")
        self.entry_rev_vin.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ctk.CTkLabel(t, text="Target Vout:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.entry_rev_vout = SmartEntry(t, textvariable=self.rev_vout, placeholder_text="e.g. 3.3")
        self.entry_rev_vout.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        ctk.CTkButton(t, text="Find Components", command=self._calc_reverse).grid(row=2, column=0, columnspan=2, pady=10)
        ctk.CTkButton(t, text="Save Schematic", command=lambda: self.save_schematic(self.rev_canvas), fg_color="green").grid(row=5, column=0, columnspan=2, pady=5)
        
        # Results area
        self.rev_results = ctk.CTkTextbox(t, height=150)
        self.rev_results.grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        t.grid_rowconfigure(3, weight=1)
        
        # Canvas
        self.rev_canvas = ctk.CTkCanvas(t, bg="#1e1e1e", highlightthickness=0, height=150)
        self.rev_canvas.grid(row=4, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        t.grid_rowconfigure(4, weight=1)

    def _calc_reverse(self):
        try:
            vin = self.entry_rev_vin.get_value()
            target = self.entry_rev_vout.get_value()
            
            if vin is None or target is None:
                self.rev_results.delete("1.0", "end")
                self.rev_results.insert("end", "Invalid Input")
                return
                
            if vin == 0:
                self.rev_results.delete("1.0", "end")
                self.rev_results.insert("end", "Vin cannot be 0")
                return

            ratio = target / vin # = R2 / (R1 + R2)
            if not (0 < ratio < 1):
                self.rev_results.delete("1.0", "end")
                self.rev_results.insert("end", "Vout must be between 0 and Vin")
                return
            
            # Find best pairs
            # Algorithm:
            # Check standard decades: 100, 1k, 10k, 100k
            # For each R2 in E24 (scaled), calculate ideal R1.
            # Snap R1 to E24 (scaled).
            # Calculate error.
            
            suggestions = []
            
            decades = [100, 1000, 10000, 100000] # Check these ranges for R2
            
            seen_pairs = set()
            
            for decade in decades:
                for base in _E24_BASE:
                    r2_val = base * decade
                    
                    # ratio = r2 / (r1 + r2)  => r1 + r2 = r2 / ratio => r1 = (r2 / ratio) - r2
                    # r1 = r2 * (1/ratio - 1)
                    
                    r1_ideal = r2_val * ( (1.0/ratio) - 1.0 )
                    
                    # Find closest E24 for r1_ideal
                    r1_std = self._find_nearest_e24(r1_ideal)
                    
                    # Calculate actual Vout
                    actual_vout = vin * (r2_val / (r1_std + r2_val))
                    error_v = abs(actual_vout - target)
                    pct_error = (error_v / target) * 100 if target != 0 else 0
                    
                    pair_key = (r1_std, r2_val)
                    if pair_key in seen_pairs: continue
                    seen_pairs.add(pair_key)
                    
                    suggestions.append({
                        'R1': r1_std, 'R2': r2_val, 
                        'Vout': actual_vout, 'Error': pct_error
                    })
            
            # Sort by error
            suggestions.sort(key=lambda x: x['Error'])
            top = suggestions[:10]
            
            lines = [f"Target: {target} V (Vin: {vin} V)"]
            lines.append("-" * 30)
            
            for s in top:
                lines.append(f"R1: {format_value(s['R1'], 'Ω')}, R2: {format_value(s['R2'], 'Ω')}")
                lines.append(f"  -> Vout: {s['Vout']:.4f} V (Err: {s['Error']:.2f}%)")
                lines.append("-" * 20)
                
            self.rev_results.delete("1.0", "end")
            self.rev_results.insert("end", "\n".join(lines))
            
            # Draw schematic with best match
            if top:
                best = top[0]
                self._draw_schematic(self.rev_canvas, vin, best['R1'], best['R2'], best['Vout'])

        except Exception as e:
            self.rev_results.delete("1.0", "end")
            self.rev_results.insert("end", f"Error: {e}")

    def _find_nearest_e24(self, val):
        if val <= 0: return 1.0
        decade = 10 ** int(math.floor(math.log10(val)))
        norm = val / decade
        closest = min(_E24_BASE, key=lambda x: abs(x - norm))
        return closest * decade

    # ------------------ SHARED DRAWING ------------------
    def _draw_schematic(self, canvas, vin=None, r1=None, r2=None, vout=None):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 50: return
        
        cx, cy = w/2, h/2
        
        c_wire = "#aaaaaa"
        c_comp = "#ffffff"
        c_lbl = "#cccccc"
        c_out = "#2ecc71"
        
        x_line = cx
        y_start = 20
        y_end = h - 20
        
        # Main Line
        canvas.create_line(x_line, y_start, x_line, y_end, fill=c_wire, width=2)
        
        # Vin
        canvas.create_oval(x_line-4, y_start-4, x_line+4, y_start+4, fill=c_comp, outline=c_comp)
        lbl_vin = f"{vin:.1f}V" if (vin is not None) else "Vin"
        canvas.create_text(x_line, y_start-12, text=lbl_vin, fill=c_comp, font=("Arial", 10, "bold"))
        
        # R1
        y_r1 = y_start + (y_end - y_start) * 0.25
        canvas.create_line(x_line, y_r1-12, x_line, y_r1+12, fill="#1e1e1e", width=4) # mask
        canvas.create_rectangle(x_line-8, y_r1-18, x_line+8, y_r1+18, fill="#1e1e1e", outline=c_comp, width=2)
        lbl_r1 = format_value(r1, 'Ω') if r1 is not None else "R1"
        canvas.create_text(x_line+15, y_r1, text=lbl_r1, fill=c_lbl, anchor="w")
        
        # Vout Tap
        y_tap = (y_start + y_end) / 2
        canvas.create_oval(x_line-3, y_tap-3, x_line+3, y_tap+3, fill=c_out, outline=c_out)
        canvas.create_line(x_line, y_tap, x_line+30, y_tap, fill=c_out, width=2)
        lbl_vout = f"{vout:.2f}V" if (vout is not None) else "Vout"
        canvas.create_text(x_line+35, y_tap, text=lbl_vout, fill=c_out, anchor="w", font=("Arial", 10, "bold"))
        
        # R2
        y_r2 = y_start + (y_end - y_start) * 0.75
        canvas.create_line(x_line, y_r2-12, x_line, y_r2+12, fill="#1e1e1e", width=4) # mask
        canvas.create_rectangle(x_line-8, y_r2-18, x_line+8, y_r2+18, fill="#1e1e1e", outline=c_comp, width=2)
        lbl_r2 = format_value(r2, 'Ω') if r2 is not None else "R2"
        canvas.create_text(x_line+15, y_r2, text=lbl_r2, fill=c_lbl, anchor="w")
        
        # GND
        canvas.create_line(x_line-12, y_end, x_line+12, y_end, fill=c_comp, width=2)
        canvas.create_line(x_line-8, y_end+4, x_line+8, y_end+4, fill=c_comp, width=2)
        canvas.create_line(x_line-4, y_end+8, x_line+4, y_end+8, fill=c_comp, width=2)

    def save_schematic(self, canvas):
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
            print(f"Save schematic error: {e}")
