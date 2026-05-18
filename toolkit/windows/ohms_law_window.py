import math
import customtkinter as ctk
from toolkit.utils.electric_utils import copy_text_to_clipboard, show_error_dialog
from toolkit.utils.parsing import parse_value, format_value
from toolkit.windows.tool_window import tool_window
from tkinter import filedialog, messagebox
import os

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from toolkit.windows.smart_entry import SmartEntry

class ohms_law_window(tool_window):
    def __init__(self, master_root):
        super().__init__(master_root, 'Ohm\'s Law Calculator')

        # layout
        self.content_frame = ctk.CTkFrame(self, corner_radius=8)
        self.content_frame.grid(row=0, column=0, sticky='nsew', padx=12, pady=12)
        for column_index in range(3):
            self.content_frame.grid_columnconfigure(column_index, weight=1)
        self.content_frame.grid_rowconfigure(8, weight=1)

        # state
        self.auto_compute_enabled = ctk.BooleanVar(value=False)
        self._traces = []

        # inputs
        self.voltage_value_text = ctk.StringVar()
        self.current_value_text = ctk.StringVar()
        self.resistance_value_text = ctk.StringVar()
        self.power_value_text = ctk.StringVar()

        # header
        self.header_label = ctk.CTkLabel(self.content_frame, text='Enter any two values to compute the rest')
        self.header_label.grid(row=0, column=0, columnspan=3, sticky='w', padx=6, pady=(0, 6))

        # row: voltage
        self.label_voltage = ctk.CTkLabel(self.content_frame, text='Voltage (V)')
        self.label_voltage.grid(row=1, column=0, sticky='e', padx=6, pady=6)
        self.entry_voltage = SmartEntry(self.content_frame, textvariable=self.voltage_value_text, placeholder_text='e.g., 120')
        self.entry_voltage.grid(row=1, column=1, sticky='we', padx=6, pady=6)

        # row: current
        self.label_current = ctk.CTkLabel(self.content_frame, text='Current (A)')
        self.label_current.grid(row=2, column=0, sticky='e', padx=6, pady=6)
        self.entry_current = SmartEntry(self.content_frame, textvariable=self.current_value_text, placeholder_text='e.g., 2')
        self.entry_current.grid(row=2, column=1, sticky='we', padx=6, pady=6)

        # row: resistance
        self.label_resistance = ctk.CTkLabel(self.content_frame, text='Resistance (Ω)')
        self.label_resistance.grid(row=3, column=0, sticky='e', padx=6, pady=6)
        self.entry_resistance = SmartEntry(self.content_frame, textvariable=self.resistance_value_text, placeholder_text='e.g., 60', min_val=0)
        self.entry_resistance.grid(row=3, column=1, sticky='we', padx=6, pady=6)

        # row: power
        self.label_power = ctk.CTkLabel(self.content_frame, text='Power (W)')
        self.label_power.grid(row=4, column=0, sticky='e', padx=6, pady=6)
        self.entry_power = SmartEntry(self.content_frame, textvariable=self.power_value_text, placeholder_text='e.g., 240')
        self.entry_power.grid(row=4, column=1, sticky='we', padx=6, pady=6)

        # actions
        self.buttons_row = ctk.CTkFrame(self.content_frame)
        self.buttons_row.grid(row=5, column=0, columnspan=3, pady=(8, 4), sticky='we')
        self.button_compute = ctk.CTkButton(self.buttons_row, text='Compute', command=self.compute_ohms_law)
        self.button_compute.pack(side='left', padx=6)
        self.button_clear = ctk.CTkButton(self.buttons_row, text='Clear', command=self.clear_all_fields)
        self.button_clear.pack(side='left', padx=6)
        self.button_example = ctk.CTkButton(self.buttons_row, text='Example', command=self.fill_example_values)
        self.button_example.pack(side='left', padx=6)
        self.checkbox_auto_compute = ctk.CTkCheckBox(
            self.buttons_row,
            text='Auto-compute',
            variable=self.auto_compute_enabled,
            command=self.toggle_auto_compute
        )
        self.checkbox_auto_compute.pack(side='right', padx=6)

        # validation note
        self.note_label = ctk.CTkLabel(
            self.content_frame,
            text='Note: Provide any two of V, I, R, P. Relations: P=VI, V=IR, P=I²R, P=V²/R'
        )
        self.note_label.grid(row=6, column=0, columnspan=3, sticky='w', padx=6, pady=(0, 4))

        # errors/status
        self.status_label = ctk.CTkLabel(self.content_frame, text='', text_color='orange')
        self.status_label.grid(row=7, column=0, columnspan=3, sticky='w', padx=6, pady=(0, 6))

        # output
        self.output_textbox = ctk.CTkTextbox(self.content_frame, height=140)
        self.output_textbox.grid(row=8, column=0, columnspan=3, sticky='nsew', padx=6, pady=(4, 6))

        # Canvas for Ohm's Law Triangle/Wheel
        self.canvas_frame = ctk.CTkFrame(self.content_frame)
        self.canvas_frame.grid(row=9, column=0, columnspan=3, sticky='nsew', padx=6, pady=6)
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#1e1e1e", highlightthickness=0, height=200)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw_triangle())

        # footer actions
        self.footer_row = ctk.CTkFrame(self.content_frame)
        self.footer_row.grid(row=10, column=0, columnspan=3, sticky='we', padx=6, pady=(0, 6))
        self.button_copy_results = ctk.CTkButton(
            self.footer_row,
            text='Copy Results',
            command=lambda: copy_text_to_clipboard(self, self.output_textbox.get('1.0', 'end').strip())
        )
        self.button_copy_results.pack(side='right', padx=6)
        
        self.button_save_diagram = ctk.CTkButton(
            self.footer_row,
            text='Save Diagram',
            command=self.save_diagram_image
        )
        self.button_save_diagram.pack(side='right', padx=6)

        # keybinds
        try:
            self.bind('<Return>', lambda event: self.compute_ohms_law())
            self.bind('<Escape>', lambda event: self.clear_all_fields())
        except Exception:
            pass
            
        # init draw
        self.after(100, self._draw_triangle)

    def toggle_auto_compute(self):
        # remove existing traces
        try:
            for var_ref, trace_id in self._traces:
                try:
                    var_ref.trace_remove('write', trace_id)
                except Exception:
                    pass
        except Exception:
            pass
        self._traces = []

        # add traces if enabled
        if self.auto_compute_enabled.get():
            try:
                self._traces.append((self.voltage_value_text, self.voltage_value_text.trace_add('write', self._on_input_change)))
                self._traces.append((self.current_value_text, self.current_value_text.trace_add('write', self._on_input_change)))
                self._traces.append((self.resistance_value_text, self.resistance_value_text.trace_add('write', self._on_input_change)))
                self._traces.append((self.power_value_text, self.power_value_text.trace_add('write', self._on_input_change)))
            except Exception:
                pass

    def _draw_triangle(self, highlight=None):
        """Fixes the advanced codebase bug where _draw_triangle was called but only _draw_wheel existed"""
        self._draw_wheel(highlight)

    def _on_input_change(self, *args):
        if getattr(self, 'suppress_trace', False):
            return
        if self.auto_compute_enabled.get():
            self.compute_ohms_law()

    def compute_ohms_law(self):
        self.status_label.configure(text='')

        # Use SmartEntry's get_value() for safe parsing
        voltage_value = self.entry_voltage.get_value()
        current_value = self.entry_current.get_value()
        resistance_value = self.entry_resistance.get_value()
        power_value = self.entry_power.get_value()

        # Determine what was calculated (missing input)
        calculated_vars = []
        if voltage_value is None: calculated_vars.append('V')
        if current_value is None: calculated_vars.append('I')
        if resistance_value is None: calculated_vars.append('R')
        if power_value is None: calculated_vars.append('P')

        if sum(value is not None for value in (voltage_value, current_value, resistance_value, power_value)) < 2:
            self.set_output_text('')
            self.status_label.configure(text='Please enter any two valid values to compute the rest.')
            self._draw_triangle()
            return

        try:
            # solve for V
            if voltage_value is None and current_value is not None and resistance_value is not None:
                voltage_value = current_value * resistance_value
            if voltage_value is None and power_value is not None and current_value is not None:
                if current_value == 0:
                    raise ZeroDivisionError('Division by zero while computing voltage.')
                voltage_value = power_value / current_value
            if voltage_value is None and power_value is not None and resistance_value is not None:
                candidate_v2 = power_value * resistance_value
                if candidate_v2 < 0:
                    raise ValueError('Invalid inputs: product P·R must be non-negative.')
                voltage_value = math.sqrt(candidate_v2)

            # solve for I
            if current_value is None and voltage_value is not None and resistance_value is not None:
                if resistance_value == 0:
                    raise ZeroDivisionError('Division by zero while computing current.')
                current_value = voltage_value / resistance_value
            if current_value is None and power_value is not None and voltage_value is not None:
                if voltage_value == 0:
                    raise ZeroDivisionError('Division by zero while computing current.')
                current_value = power_value / voltage_value
            if current_value is None and power_value is not None and resistance_value is not None:
                if resistance_value < 0:
                    raise ValueError('Resistance cannot be negative.')
                candidate_i2 = power_value / resistance_value
                if candidate_i2 < 0:
                    raise ValueError('Invalid inputs: ratio P/R must be non-negative.')
                current_value = math.sqrt(candidate_i2)

            # solve for R
            if resistance_value is None and voltage_value is not None and current_value is not None:
                if current_value == 0:
                    raise ZeroDivisionError('Division by zero while computing resistance.')
                resistance_value = voltage_value / current_value
            if resistance_value is None and voltage_value is not None and power_value is not None:
                if power_value == 0:
                    raise ZeroDivisionError('Division by zero while computing resistance.')
                resistance_value = (voltage_value * voltage_value) / power_value
            if resistance_value is None and power_value is not None and current_value is not None:
                resistance_value = power_value / (current_value * current_value)

            # solve for P
            if power_value is None and voltage_value is not None and current_value is not None:
                power_value = voltage_value * current_value
            if power_value is None and voltage_value is not None and resistance_value is not None:
                if resistance_value == 0:
                    raise ZeroDivisionError('Division by zero while computing power.')
                power_value = (voltage_value * voltage_value) / resistance_value
            if power_value is None and current_value is not None and resistance_value is not None:
                power_value = (current_value * current_value) * resistance_value

            # reflect solved values back to UI (Only if they were missing!)
            self.suppress_trace = True
            try:
                 if 'V' in calculated_vars and voltage_value is not None:
                     self.voltage_value_text.set(f'{voltage_value:.6g}')
                 if 'I' in calculated_vars and current_value is not None:
                     self.current_value_text.set(f'{current_value:.6g}')
                 if 'R' in calculated_vars and resistance_value is not None:
                     self.resistance_value_text.set(f'{resistance_value:.6g}')
                 if 'P' in calculated_vars and power_value is not None:
                     self.power_value_text.set(f'{power_value:.6g}')
            finally:
                self.suppress_trace = False

            # prepare output lines
            voltage_formatted = format_value(voltage_value, 'V') if voltage_value is not None else '—'
            current_formatted = format_value(current_value, 'A') if current_value is not None else '—'
            resistance_formatted = format_value(resistance_value, 'Ω') if resistance_value is not None else '—'
            power_formatted = format_value(power_value, 'W') if power_value is not None else '—'

            lines = [
                f'V = {voltage_formatted}',
                f'I = {current_formatted}',
                f'R = {resistance_formatted}',
                f'P = {power_formatted}',
            ]
            self.set_output_text('\n'.join(lines))
            
            # Pass what was calculated to draw function
            self._draw_triangle(highlight=calculated_vars)
            
        except Exception as compute_error:
            self.status_label.configure(text=str(compute_error))
            self._draw_triangle()
     
    def _draw_wheel(self, highlight=None):
        if highlight is None: highlight = []
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50: return
        
        cx, cy = w/2, h/2
        rad_out = min(cx, cy) - 10
        rad_in = rad_out * 0.4
        
        quads = [
            {"lbl": "P", "c": "#e74c3c", "forms": ["VI", "I²R", "V²/R"], "ang": 90},   # Top-Left
            {"lbl": "V", "c": "#f1c40f", "forms": ["IR", "P/I", "√PR"], "ang": 0},    # Top-Right
            {"lbl": "R", "c": "#2ecc71", "forms": ["V/I", "V²/P", "P/I²"], "ang": 270}, # Bot-Right
            {"lbl": "I", "c": "#3498db", "forms": ["V/R", "P/V", "√P/R"], "ang": 180}   # Bot-Left
        ]
        
        for q in quads:
            # Draw Quadrant Arc
            start = q["ang"]
            is_hl = q["lbl"] in highlight
            fill = q["c"] if is_hl or not highlight else "#444"
            outline = "#fff"
            
            # Outer Sector
            self.canvas.create_arc(cx-rad_out, cy-rad_out, cx+rad_out, cy+rad_out,
                                  start=start, extent=90, fill=fill, outline=outline, width=2, style="pieslice")
                                  
            # Draw Formulas (3 per quadrant)
            r_txt = (rad_in + rad_out) * 0.75
            
            for i, form in enumerate(q["forms"]):
                sub_ang = start + 15 + (i * 30)
                rad_ang = math.radians(sub_ang)
                tx = cx + r_txt * math.cos(rad_ang)
                ty = cy - r_txt * math.sin(rad_ang)
                
                self.canvas.create_text(tx, ty, text=form, fill="#fff" if is_hl or not highlight else "#ccc",
                                       font=("Arial", 10, "bold"), angle=0)
            
            # Draw Main Label (Inner)
            r_lbl = rad_in * 0.6
            mid_ang = math.radians(start + 45)
            lx = cx + r_lbl * math.cos(mid_ang)
            ly = cy - r_lbl * math.sin(mid_ang)
            self.canvas.create_text(lx, ly, text=q["lbl"], fill=q["c"], font=("Arial", 20, "bold"))
            
        # Center Hub
        self.canvas.create_oval(cx-rad_in, cy-rad_in, cx+rad_in, cy+rad_in, fill="#222", outline="#fff", width=2)
        
        # Title in center
        self.canvas.create_text(cx, cy, text="Ohm's\nLaw", fill="#fff", justify="center", font=("Arial", 12))

    def clear_all_fields(self):
        for variable_ref in (
            self.voltage_value_text,
            self.current_value_text,
            self.resistance_value_text,
            self.power_value_text,
        ):
            variable_ref.set('')
        self.set_output_text('')
        self.status_label.configure(text='')
        self._draw_triangle()

    def fill_example_values(self):
        self.clear_all_fields()
        self.voltage_value_text.set('120')
        self.resistance_value_text.set('60')
        self.compute_ohms_law()

    def set_output_text(self, text_value: str):
        try:
            self.output_textbox.delete('1.0', 'end')
            if text_value:
                self.output_textbox.insert('end', text_value)
        except Exception:
            pass

    def save_diagram_image(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "PIL (Pillow) library is required to save images.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Ohm's Wheel Diagram"
        )
        if not file_path:
            return

        try:
            ps_data = self.canvas.postscript(colormode='color')
            import io
            ps_io = io.BytesIO(ps_data.encode('utf-8'))
            img = Image.open(ps_io)
            img.load()
            img.save(file_path, 'png')
            messagebox.showinfo("Success", f"Diagram saved to {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save diagram: {e}")
