import math
import customtkinter as ctk
from toolkit.utils.electric_utils import show_error_dialog, round_up_breaker_amps
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

class power_calculator_window(tool_window):
    def __init__(self, master_root):
        super().__init__(master_root, 'Power Calculator')

        # layout
        self.content_frame = ctk.CTkFrame(self, corner_radius=8)
        self.content_frame.grid(row=0, column=0, sticky='nsew', padx=12, pady=12)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # state
        self.auto_compute_enabled = ctk.BooleanVar(value=False)

        # inputs
        self.power_type_text = ctk.StringVar(value='DC')
        self.voltage_value_text = ctk.StringVar()
        self.current_value_text = ctk.StringVar()
        self.power_factor_text = ctk.StringVar(value='1.0')
        self.efficiency_text = ctk.StringVar(value='1.0')
        self.real_power_text = ctk.StringVar()
        self.apparent_power_text = ctk.StringVar()

        # row 0: type
        self.label_type = ctk.CTkLabel(self.content_frame, text='Type')
        self.label_type.grid(row=0, column=0, sticky='e', padx=6, pady=6)
        self.option_type = ctk.CTkOptionMenu(
            self.content_frame,
            variable=self.power_type_text,
            values=['DC', 'AC Single-phase', 'AC Three-phase'],
            command=lambda _: self._on_type_changed()
        )
        self.option_type.grid(row=0, column=1, sticky='we', padx=6, pady=6)

        # row 1: voltage
        self.label_voltage = ctk.CTkLabel(self.content_frame, text='Voltage (V)')
        self.label_voltage.grid(row=1, column=0, sticky='e', padx=6, pady=6)
        self.entry_voltage = SmartEntry(self.content_frame, textvariable=self.voltage_value_text, placeholder_text='e.g., 230')
        self.entry_voltage.grid(row=1, column=1, sticky='we', padx=6, pady=6)

        # row 2: current
        self.label_current = ctk.CTkLabel(self.content_frame, text='Current (A)')
        self.label_current.grid(row=2, column=0, sticky='e', padx=6, pady=6)
        self.entry_current = SmartEntry(self.content_frame, textvariable=self.current_value_text, placeholder_text='e.g., 10')
        self.entry_current.grid(row=2, column=1, sticky='we', padx=6, pady=6)

        # row 3: power factor (AC)
        self.label_power_factor = ctk.CTkLabel(self.content_frame, text='Power Factor (AC)')
        self.label_power_factor.grid(row=3, column=0, sticky='e', padx=6, pady=6)
        self.entry_power_factor = SmartEntry(self.content_frame, textvariable=self.power_factor_text, placeholder_text='1.0 for DC', min_val=0, max_val=1, si=False)
        self.entry_power_factor.grid(row=3, column=1, sticky='we', padx=6, pady=6)

        # row 4: efficiency
        self.label_efficiency = ctk.CTkLabel(self.content_frame, text='Efficiency (0..1, optional)')
        self.label_efficiency.grid(row=4, column=0, sticky='e', padx=6, pady=6)
        self.entry_efficiency = SmartEntry(self.content_frame, textvariable=self.efficiency_text, placeholder_text='e.g., 0.92', min_val=0, max_val=1, si=False)
        self.entry_efficiency.grid(row=4, column=1, sticky='we', padx=6, pady=6)

        # row 5: optional power inputs
        self.optional_frame = ctk.CTkFrame(self.content_frame)
        self.optional_frame.grid(row=5, column=0, columnspan=2, sticky='we', padx=6, pady=(0, 6))
        self.optional_frame.grid_columnconfigure((1, 3), weight=1)

        self.label_real_power = ctk.CTkLabel(self.optional_frame, text='Real Power P (W)')
        self.label_real_power.grid(row=0, column=0, sticky='e', padx=6, pady=4)
        self.entry_real_power = SmartEntry(self.optional_frame, textvariable=self.real_power_text, placeholder_text='optional')
        self.entry_real_power.grid(row=0, column=1, sticky='we', padx=(0, 6), pady=4)

        self.label_apparent_power = ctk.CTkLabel(self.optional_frame, text='Apparent Power S (VA)')
        self.label_apparent_power.grid(row=0, column=2, sticky='e', padx=6, pady=4)
        self.entry_apparent_power = SmartEntry(self.optional_frame, textvariable=self.apparent_power_text, placeholder_text='optional')
        self.entry_apparent_power.grid(row=0, column=3, sticky='we', padx=(0, 6), pady=4)

        # row 6: Energy Cost Estimator
        self.cost_frame = ctk.CTkFrame(self.content_frame)
        self.cost_frame.grid(row=6, column=0, columnspan=2, sticky='we', padx=6, pady=(0, 6))
        self.cost_frame.grid_columnconfigure((1, 3), weight=1)
        
        ctk.CTkLabel(self.cost_frame, text="Rate ($/kWh)").grid(row=0, column=0, sticky="e", padx=6)
        self.rate_text = ctk.StringVar(value="0.15")
        SmartEntry(self.cost_frame, textvariable=self.rate_text, si=False).grid(row=0, column=1, sticky="we", padx=6)
        
        ctk.CTkLabel(self.cost_frame, text="Hours/Day").grid(row=0, column=2, sticky="e", padx=6)
        self.hours_text = ctk.StringVar(value="24")
        SmartEntry(self.cost_frame, textvariable=self.hours_text, si=False).grid(row=0, column=3, sticky="we", padx=6)

        # actions
        self.footer_frame = ctk.CTkFrame(self.content_frame)
        self.footer_frame.grid(row=7, column=0, columnspan=2, sticky='we', padx=6, pady=6)
        self.button_compute = ctk.CTkButton(self.footer_frame, text='Compute', command=self.compute_power_values)
        self.button_compute.pack(side='left', padx=6)
        self.button_clear = ctk.CTkButton(self.footer_frame, text='Clear', command=self.clear_all_fields)
        self.button_clear.pack(side='left', padx=6)
        self.button_example = ctk.CTkButton(self.footer_frame, text='Example', command=self.fill_example_values)
        self.button_example.pack(side='left', padx=6)
        self.checkbox_auto_compute = ctk.CTkCheckBox(
            self.footer_frame,
            text='Auto-compute',
            variable=self.auto_compute_enabled,
            command=lambda: self.compute_power_values() if self.auto_compute_enabled.get() else None
        )
        self.checkbox_auto_compute.pack(side='right', padx=6)
        self.button_copy = ctk.CTkButton(self.footer_frame, text='Copy results', command=self.copy_results_to_clipboard)
        self.button_copy.pack(side='right', padx=6)
        
        self.button_save_plot = ctk.CTkButton(self.footer_frame, text='Save Plot', command=self.save_plot_image)
        self.button_save_plot.pack(side='right', padx=6)

        # results
        self.result_label = ctk.CTkLabel(self.content_frame, text='Result: ')
        self.result_label.grid(row=8, column=0, columnspan=2, sticky='w', padx=6, pady=(6, 4))

        self.details_textbox = ctk.CTkTextbox(self.content_frame, height=160)
        self.details_textbox.grid(row=9, column=0, columnspan=2, sticky='nsew', padx=6, pady=(0, 6))

        self.breaker_label = ctk.CTkLabel(self.content_frame, text='')
        self.breaker_label.grid(row=10, column=0, columnspan=2, sticky='w', padx=6, pady=(0, 4))

        self.note_label = ctk.CTkLabel(
            self.content_frame,
            text='Notes: AC 3φ assumes line-to-line voltage (√3 V I). Efficiency (if < 1) inflates input power: Pin = P/η.'
        )
        self.note_label.grid(row=11, column=0, columnspan=2, sticky='w', padx=6, pady=(0, 4))

        # binds
        try:
            self.bind('<Return>', lambda e: self.compute_power_values())
            self.bind('<Escape>', lambda e: self.clear_all_fields())
        except Exception:
            pass

        # initial state
        self._on_type_changed()

    def _on_type_changed(self):
        try:
            if self.power_type_text.get() == 'DC':
                self.entry_power_factor.configure(placeholder_text='1.0 (ignored for DC)')
            else:
                self.entry_power_factor.configure(placeholder_text='e.g., 0.85')
        except Exception:
            pass

    def _get_pf(self):
        try:
            pf = parse_value(self.power_factor_text.get())
        except Exception:
            pf = 1.0
        return max(0.0, min(1.0, pf))

    def _get_eff(self):
        try:
            eff = parse_value(self.efficiency_text.get())
        except Exception:
            eff = 1.0
        if eff <= 0:
            return 1.0
        return min(eff, 1.0)

    def compute_power_values(self):
        self.details_textbox.delete('1.0', 'end')

        try:
            voltage_value = parse_value(self.voltage_value_text.get())
        except Exception:
            voltage_value = None
        
        try:
            current_value = parse_value(self.current_value_text.get())
        except Exception:
            current_value = None
            
        pf_value = self._get_pf()
        eff_value = self._get_eff()

        try:
            real_power_input = parse_value(self.real_power_text.get())
        except Exception:
            real_power_input = None
            
        try:
            apparent_power_input = parse_value(self.apparent_power_text.get())
        except Exception:
            apparent_power_input = None

        if voltage_value is None and current_value is None and real_power_input is None and apparent_power_input is None:
            show_error_dialog('Enter at least Voltage & Current, or provide Power with PF.')
            return

        power_type_name = self.power_type_text.get()

        try:
            if (voltage_value is None or current_value is None) and power_type_name != 'DC':
                if real_power_input is not None and pf_value > 0:
                    if voltage_value is not None and current_value is None:
                        current_value = real_power_input / (voltage_value * pf_value)
                    elif current_value is not None and voltage_value is None:
                        voltage_value = real_power_input / (current_value * pf_value)
                if (voltage_value is None or current_value is None) and apparent_power_input is not None:
                    if voltage_value is not None and current_value is None:
                        current_value = apparent_power_input / voltage_value
                    elif current_value is not None and voltage_value is None:
                        voltage_value = apparent_power_input / current_value
        except Exception:
            pass

        if voltage_value is None or current_value is None:
            if power_type_name == 'DC' and real_power_input is not None:
                if voltage_value is not None:
                    current_value = real_power_input / voltage_value
                elif current_value is not None:
                    voltage_value = real_power_input / current_value
                    
        if voltage_value is None or current_value is None:
            show_error_dialog('Provide enough inputs: typically Voltage and Current, or Power + PF + one of Voltage/Current.')
            return

        # Compute base S and P
        if power_type_name == 'DC':
            apparent_va = voltage_value * current_value
            real_watts = apparent_va
            reactive_var = 0.0
        elif power_type_name == 'AC Single-phase':
            apparent_va = voltage_value * current_value
            real_watts = apparent_va * pf_value
            reactive_squared = max(apparent_va * apparent_va - real_watts * real_watts, 0.0)
            reactive_var = math.sqrt(reactive_squared)
        else:
            apparent_va = 1.732 * voltage_value * current_value
            real_watts = apparent_va * pf_value
            reactive_squared = max(apparent_va * apparent_va - real_watts * real_watts, 0.0)
            reactive_var = math.sqrt(reactive_squared)

        input_power_watts = real_watts / eff_value if eff_value > 0 else real_watts

        p_text = format_value(real_watts, "W")
        s_text = format_value(apparent_va, "VA")
        q_text = format_value(reactive_var, "var")
        pin_text = format_value(input_power_watts, "W")

        self.result_label.configure(text='Result: P = ' + p_text + ', S = ' + s_text + ', Q = ' + q_text + ', PF = ' + f'{pf_value:.3f}')

        try:
            rate = float(self.rate_text.get())
            hours = float(self.hours_text.get())
        except:
            rate = 0.15
            hours = 24.0
            
        kw_load = input_power_watts / 1000.0
        can_calc_cost = kw_load > 0 and rate > 0
        
        lines = []
        lines.append('Details')
        lines.append('-------')
        lines.append('Type: ' + power_type_name)
        lines.append('Voltage: ' + (f'{voltage_value:.6g}' if voltage_value is not None else '—') + ' V')
        lines.append('Current: ' + (f'{current_value:.6g}' if current_value is not None else '—') + ' A')
        lines.append('Power factor: ' + f'{pf_value:.3f}')
        lines.append('Efficiency: ' + (f'{eff_value:.3f}' if eff_value is not None else '—'))
        
        if can_calc_cost:
            cost_h = kw_load * rate
            cost_d = cost_h * hours
            cost_m = cost_d * 30
            cost_y = cost_d * 365
            lines.append('')
            lines.append('Energy Cost Est. (Pin):')
            lines.append(f'  Rate: ${rate:.2f}/kWh, Usage: {hours}h/day')
            lines.append(f'  Hourly: ${cost_h:.4f}')
            lines.append(f'  Daily:  ${cost_d:.2f}')
            lines.append(f'  Monthly:${cost_m:.2f}')
            lines.append(f'  Yearly: ${cost_y:.2f}')
            
        lines.append('')
        if real_power_input is not None:
            lines.append('P input: ' + format_value(real_power_input, "W"))
        if apparent_power_input is not None:
            lines.append('S input: ' + format_value(apparent_power_input, "VA"))
        lines.append('Computed P: ' + p_text)
        lines.append('Computed S: ' + s_text)
        lines.append('Computed Q: ' + q_text)
        if eff_value < 1.0:
            lines.append('Estimated input P (with efficiency): ' + pin_text)

        self.details_textbox.insert('end', '\n'.join(lines))

        try:
            continuous_current_estimate = (current_value or 0) * 1.25
            breaker_suggestion = round_up_breaker_amps(continuous_current_estimate)
            self.breaker_label.configure(text='Breaker suggestion: ~' + str(breaker_suggestion) + ' A (est.)')
        except Exception:
            self.breaker_label.configure(text='')

        self._draw_power_triangle(real_watts, reactive_var, apparent_va, pf_value)

    def _draw_power_triangle(self, P, Q, S, pf):
        if not hasattr(self, 'canvas'):
            self.canvas_frame = ctk.CTkFrame(self.content_frame)
            self.canvas_frame.grid(row=9, column=0, columnspan=2, sticky='nsew', padx=6, pady=6)
            
            self.details_textbox.grid(row=10, column=0, columnspan=2)
            self.breaker_label.grid(row=11, column=0, columnspan=2)
            self.note_label.grid(row=12, column=0, columnspan=2)
            
            self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#1e1e1e", highlightthickness=0, height=200)
            self.canvas.pack(fill="both", expand=True)
            
            self.content_frame.grid_rowconfigure(9, weight=1)
            self.content_frame.grid_rowconfigure(10, weight=0)
        
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50: return

        mode = self.power_type_text.get()
        if mode == 'DC':
            self.canvas.create_text(w/2, h/2, text="Power Triangle is for AC modes", fill="#666666")
            return
            
        if P is None or Q is None:
            return

        max_val = max(P, Q, S, 1.0)
        pad = 40
        avail_w = w - 2*pad
        avail_h = h - 2*pad
        
        scale = min(avail_w, avail_h) / max_val if max_val > 0 else 1
        
        ox = pad
        oy = h - pad
        
        px = ox + P * scale
        qy = oy - Q * scale
        
        c_p = "#2ecc71"
        c_q = "#e74c3c"
        c_s = "#f1c40f"
        
        # Draw P vector
        self.canvas.create_line(ox, oy, px, oy, fill=c_p, width=3, arrow="last")
        self.canvas.create_text((ox+px)/2, oy+15, text=f"P={format_value(P,'W')}", fill=c_p)
        
        # Draw Q vector
        self.canvas.create_line(px, oy, px, qy, fill=c_q, width=3, arrow="last")
        self.canvas.create_text(px+10, (oy+qy)/2, text=f"Q={format_value(Q,'var')}", fill=c_q, anchor="w")
        
        # Draw S vector
        self.canvas.create_line(ox, oy, px, qy, fill=c_s, width=3, arrow="last")
        self.canvas.create_text((ox+px)/2 - 10, (oy+qy)/2 - 10, text=f"S={format_value(S,'VA')}", fill=c_s, anchor="se")
        
        # Angle phi
        if S > 0:
            phi_deg = math.acos(min(1.0, max(-1.0, P/S))) * 180.0 / math.pi
            self.canvas.create_text(ox+30, oy-10, text=f"φ={phi_deg:.1f}°", fill="#aaaaaa", anchor="w")
            self.canvas.create_arc(ox-20, oy-20, ox+20, oy+20, start=0, extent=phi_deg, style="arc", outline="#aaaaaa")

    def clear_all_fields(self):
        self.voltage_value_text.set('')
        self.current_value_text.set('')
        self.power_factor_text.set('1.0')
        self.efficiency_text.set('1.0')
        self.real_power_text.set('')
        self.apparent_power_text.set('')
        self.result_label.configure(text='Result: ')
        self.breaker_label.configure(text='')
        try:
            self.details_textbox.delete('1.0', 'end')
            if hasattr(self, 'canvas'):
                self.canvas.delete("all")
        except Exception:
            pass

    def fill_example_values(self):
        self.power_type_text.set('AC Three-phase')
        self.voltage_value_text.set('400')
        self.current_value_text.set('32')
        self.power_factor_text.set('0.9')
        self.efficiency_text.set('0.95')
        self.real_power_text.set('')
        self.apparent_power_text.set('')
        self.compute_power_values()

    def copy_results_to_clipboard(self):
        try:
            header_text = self.result_label.cget('text') or ''
            details_text = self.details_textbox.get('1.0', 'end').strip()
            final_text = header_text.strip()
            if details_text:
                final_text = final_text + '\n' + details_text
            self.clipboard_clear()
            self.clipboard_append(final_text)
        except Exception as copy_error:
            show_error_dialog(str(copy_error))

    def save_plot_image(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "PIL (Pillow) library is required to save images.")
            return

        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            messagebox.showwarning("Warning", "No Power Triangle to save. Perform an AC calculation first.")
            return

        if self.power_type_text.get() == 'DC':
             messagebox.showwarning("Warning", "Power Triangle is not available in DC mode.")
             return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Power Triangle"
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
            messagebox.showinfo("Success", f"Plot saved to {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save plot: {e}")
