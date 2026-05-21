import math
import customtkinter as ctk
from tkinter import messagebox
from utils.electric_utils import (
    awg_reference_map, awg_order_desc, get_awg_label, parse_awg_label,
    safe_float, copy_text_to_clipboard, show_error_dialog
)
from windows.tool_window import tool_window


class voltage_drop_window(tool_window):
    def __init__(self, master_root):
        super().__init__(master_root, 'Voltage Drop Calculator')
        self.content_frame = ctk.CTkFrame(self, corner_radius=8)
        self.content_frame.grid(row=0, column=0, sticky='nsew', padx=12, pady=12)
        for column_index in range(4):
            self.content_frame.grid_columnconfigure(column_index, weight=1)

        self.system_voltage_text = ctk.StringVar()
        self.load_current_text = ctk.StringVar()
        self.length_one_way_feet_text = ctk.StringVar()
        self.power_factor_text = ctk.StringVar(value='1.0')
        self.material_text = ctk.StringVar(value='Copper')
        self.phase_text = ctk.StringVar(value='Single-phase')
        self.awg_choice_text = ctk.StringVar(value=get_awg_label(awg_order_desc[3]))
        self.target_drop_percent_text = ctk.StringVar(value='3.0')

        self.label_system_voltage = ctk.CTkLabel(self.content_frame, text='System Voltage (V)')
        self.label_system_voltage.grid(row=0, column=0, sticky='e', padx=6, pady=6)
        self.entry_system_voltage = ctk.CTkEntry(self.content_frame, textvariable=self.system_voltage_text)
        self.entry_system_voltage.grid(row=0, column=1, sticky='we', padx=6, pady=6)

        self.label_load_current = ctk.CTkLabel(self.content_frame, text='Load Current (A)')
        self.label_load_current.grid(row=1, column=0, sticky='e', padx=6, pady=6)
        self.entry_load_current = ctk.CTkEntry(self.content_frame, textvariable=self.load_current_text)
        self.entry_load_current.grid(row=1, column=1, sticky='we', padx=6, pady=6)

        self.label_length_feet = ctk.CTkLabel(self.content_frame, text='One-way Length (ft)')
        self.label_length_feet.grid(row=2, column=0, sticky='e', padx=6, pady=6)
        self.entry_length_feet = ctk.CTkEntry(self.content_frame, textvariable=self.length_one_way_feet_text)
        self.entry_length_feet.grid(row=2, column=1, sticky='we', padx=6, pady=6)

        self.label_material = ctk.CTkLabel(self.content_frame, text='Material')
        self.label_material.grid(row=0, column=2, sticky='e', padx=6, pady=6)
        self.option_material = ctk.CTkOptionMenu(
            self.content_frame,
            variable=self.material_text,
            values=['Copper', 'Aluminum'],
            command=lambda _v: self._maybe_compute()
        )
        self.option_material.grid(row=0, column=3, sticky='we', padx=6, pady=6)

        self.label_phase = ctk.CTkLabel(self.content_frame, text='Phase')
        self.label_phase.grid(row=1, column=2, sticky='e', padx=6, pady=6)
        self.option_phase = ctk.CTkOptionMenu(
            self.content_frame,
            variable=self.phase_text,
            values=['Single-phase', 'Three-phase'],
            command=lambda _v: self._maybe_compute()
        )
        self.option_phase.grid(row=1, column=3, sticky='we', padx=6, pady=6)

        self.label_power_factor = ctk.CTkLabel(self.content_frame, text='Power Factor')
        self.label_power_factor.grid(row=2, column=2, sticky='e', padx=6, pady=6)
        self.entry_power_factor = ctk.CTkEntry(self.content_frame, textvariable=self.power_factor_text)
        self.entry_power_factor.grid(row=2, column=3, sticky='we', padx=6, pady=6)

        self.label_awg = ctk.CTkLabel(self.content_frame, text='AWG')
        self.label_awg.grid(row=3, column=0, sticky='e', padx=6, pady=6)
        self.option_awg = ctk.CTkOptionMenu(
            self.content_frame,
            variable=self.awg_choice_text,
            values=[get_awg_label(x) for x in awg_order_desc],
            command=lambda _v: self._maybe_compute()
        )
        self.option_awg.grid(row=3, column=1, sticky='we', padx=6, pady=6)

        self.actions_frame = ctk.CTkFrame(self.content_frame)
        self.actions_frame.grid(row=3, column=2, columnspan=2, sticky='we', padx=6, pady=6)
        self.button_compute = ctk.CTkButton(self.actions_frame, text='Compute', command=self.compute_voltage_drop)
        self.button_compute.pack(side='left', padx=6)
        self.button_suggest_awg = ctk.CTkButton(self.actions_frame, text='Suggest AWG', command=self.suggest_awg_for_target_drop)
        self.button_suggest_awg.pack(side='left', padx=6)

        self.label_target_drop = ctk.CTkLabel(self.content_frame, text='Target Drop (%)')
        self.label_target_drop.grid(row=4, column=0, sticky='e', padx=6, pady=6)
        self.entry_target_drop = ctk.CTkEntry(self.content_frame, textvariable=self.target_drop_percent_text)
        self.entry_target_drop.grid(row=4, column=1, sticky='we', padx=6, pady=6)

        self.output_textbox = ctk.CTkTextbox(self.content_frame, height=260)
        self.output_textbox.grid(row=5, column=0, columnspan=4, sticky='nsew', padx=6, pady=(6, 6))
        self.button_copy_results = ctk.CTkButton(
            self.content_frame,
            text='Copy Results',
            command=lambda: copy_text_to_clipboard(self, self.output_textbox.get('1.0', 'end').strip())
        )
        self.button_copy_results.grid(row=6, column=3, sticky='e', padx=6, pady=(0, 6))
        self.content_frame.grid_rowconfigure(5, weight=1)

        # Quick keyboard bindings for smoother UX
        try:
            for widget in (
                self.entry_system_voltage, self.entry_load_current, self.entry_length_feet,
                self.entry_power_factor
            ):
                widget.bind('<Return>', lambda _e: self.compute_voltage_drop())
            self.entry_target_drop.bind('<Return>', lambda _e: self.suggest_awg_for_target_drop())
            # Recompute as user types when essential inputs are present
            for widget in (self.entry_system_voltage, self.entry_load_current, self.entry_length_feet, self.entry_power_factor):
                widget.bind('<KeyRelease>', lambda _e: self._maybe_compute())
        except Exception:
            pass

    def get_ohms_per_1000ft(self, awg_value: int, material_name: str) -> float:
        row = awg_reference_map[awg_value]
        return row['ohms_per_1000ft_cu'] if material_name == 'Copper' else row['ohms_per_1000ft_al']

    def _phase_multiplier(self, phase_name: str) -> float:
        # 2 for single-phase 2-wire (out-and-back), sqrt(3) for 3φ line-to-line
        return 2.0 if phase_name == 'Single-phase' else math.sqrt(3.0)

    def compute_drop_values(self, system_voltage_v: float, load_current_a: float, length_one_way_ft: float,
                            awg_value: int, material_name: str, phase_name: str, power_factor_value: float):
        ohm_per_1000ft_value = self.get_ohms_per_1000ft(awg_value, material_name)
        resistance_one_way_ohm = (ohm_per_1000ft_value / 1000.0) * length_one_way_ft
        k_phase = self._phase_multiplier(phase_name)
        drop_volts_value = k_phase * load_current_a * resistance_one_way_ohm
        # Note: Proper drop includes reactance; if unavailable, PF scaling is a rough proxy.
        drop_volts_value *= max(0.0, min(1.0, power_factor_value or 1.0))
        drop_percent_value = (drop_volts_value / system_voltage_v) * 100.0 if system_voltage_v else 0.0
        return drop_volts_value, drop_percent_value, resistance_one_way_ohm

    def _parse_and_validate(self):
        """
        Parse inputs, validate ranges, and return a dict or raise ValueError with a friendly message.
        """
        system_voltage_v = safe_float(self.system_voltage_text.get())
        load_current_a = safe_float(self.load_current_text.get())
        length_one_way_ft = safe_float(self.length_one_way_feet_text.get())
        power_factor_value = safe_float(self.power_factor_text.get())
        if system_voltage_v is None or load_current_a is None or length_one_way_ft is None:
            raise ValueError('Please fill System Voltage, Load Current, and Length.')
        if system_voltage_v <= 0:
            raise ValueError('System Voltage must be greater than zero.')
        if load_current_a < 0:
            raise ValueError('Load Current cannot be negative.')
        if length_one_way_ft < 0:
            raise ValueError('Length cannot be negative.')
        # PF handling: clamp and warn once per compute if out-of-range
        pf = 1.0 if power_factor_value is None else power_factor_value
        clamped_pf = max(0.0, min(1.0, pf))
        if pf != clamped_pf:
            try:
                messagebox.showwarning('Power Factor', 'Power factor must be in [0, 1]. It was clamped to the nearest bound.')
            except Exception:
                pass
        return {
            'V': float(system_voltage_v),
            'I': float(load_current_a),
            'L1': float(length_one_way_ft),
            'pf': float(clamped_pf),
            'material': self.material_text.get(),
            'phase': self.phase_text.get(),
        }

    def _maybe_compute(self):
        """
        Best-effort live recompute without modal errors; only updates when inputs are valid.
        """
        try:
            vals = self._parse_and_validate()
            awg_value = parse_awg_label(self.awg_choice_text.get())
            drop_volts_value, drop_percent_value, resistance_one_way_ohm = self.compute_drop_values(
                vals['V'], vals['I'], vals['L1'], awg_value, vals['material'], vals['phase'], vals['pf']
            )
            two_way_length_ft = self._phase_multiplier(vals['phase']) * vals['L1']
            lines_list = [
                f'Material: {vals["material"]}',
                f'AWG: {get_awg_label(awg_value)}',
                f'Phase: {vals["phase"]}, PF: {vals["pf"]:.3f}',
                f'One-way length: {vals["L1"]:.3f} ft (effective path ≈ {two_way_length_ft:.3f} ft)',
                f'Line R (one-way): {resistance_one_way_ohm:.6f} Ω',
                f'Voltage drop: {drop_volts_value:.3f} V ({drop_percent_value:.2f} %)',
                f'Estimated load voltage: {vals["V"] - drop_volts_value:.3f} V',
            ]
            # Also show max allowable length for current AWG at target %, if target is set
            target_drop_percent = safe_float(self.target_drop_percent_text.get())
            if target_drop_percent and target_drop_percent > 0:
                max_len = self.compute_max_one_way_length_for_target(
                    vals['V'], vals['I'], awg_value, vals['material'], vals['phase'], vals['pf'], target_drop_percent
                )
                if max_len is not None:
                    lines_list.append(f'Max one-way length for {target_drop_percent:.2f}% target with this AWG: {max_len:.2f} ft')
            self.output_textbox.delete('1.0', 'end')
            self.output_textbox.insert('end', '\n'.join(lines_list))
        except Exception:
            # silent for live updates
            pass

    def compute_voltage_drop(self):
        try:
            vals = self._parse_and_validate()
        except ValueError as ve:
            show_error_dialog(str(ve))
            return
        try:
            awg_value = parse_awg_label(self.awg_choice_text.get())
            drop_volts_value, drop_percent_value, resistance_one_way_ohm = self.compute_drop_values(
                vals['V'], vals['I'], vals['L1'], awg_value, vals['material'], vals['phase'], vals['pf']
            )
            two_way_length_ft = self._phase_multiplier(vals['phase']) * vals['L1']
            lines_list = [
                f'Material: {vals["material"]}',
                f'AWG: {get_awg_label(awg_value)}',
                f'Phase: {vals["phase"]}, PF: {vals["pf"]:.3f}',
                f'One-way length: {vals["L1"]:.3f} ft (effective path ≈ {two_way_length_ft:.3f} ft)',
                f'Line R (one-way): {resistance_one_way_ohm:.6f} Ω',
                f'Voltage drop: {drop_volts_value:.3f} V ({drop_percent_value:.2f} %)',
                f'Estimated load voltage: {vals["V"] - drop_volts_value:.3f} V',
            ]
            if drop_volts_value > vals['V']:
                lines_list.append('Note: Computed drop exceeds system voltage; check inputs.')
            target_drop_percent = safe_float(self.target_drop_percent_text.get())
            if target_drop_percent and target_drop_percent > 0:
                max_len = self.compute_max_one_way_length_for_target(
                    vals['V'], vals['I'], awg_value, vals['material'], vals['phase'], vals['pf'], target_drop_percent
                )
                if max_len is not None:
                    lines_list.append(f'Max one-way length for {target_drop_percent:.2f}% target with this AWG: {max_len:.2f} ft')
            self.output_textbox.delete('1.0', 'end')
            self.output_textbox.insert('end', '\n'.join(lines_list))
        except Exception as compute_error:
            show_error_dialog(f'Error: {compute_error}')

    def compute_max_one_way_length_for_target(self, system_voltage_v: float, load_current_a: float, awg_value: int,
                                              material_name: str, phase_name: str, power_factor_value: float,
                                              target_drop_percent: float):
        """
        Invert the drop formula to estimate the maximum one-way length meeting a target drop percent.
        Returns None if inputs are not suitable.
        """
        try:
            if load_current_a <= 0 or target_drop_percent <= 0:
                return None
            ohm_per_1000ft_value = self.get_ohms_per_1000ft(awg_value, material_name)
            k_phase = self._phase_multiplier(phase_name)
            pf = max(0.0, min(1.0, power_factor_value or 1.0))
            # target drop volts
            vd_target_v = (target_drop_percent / 100.0) * system_voltage_v
            # vd = k * I * R_one_way * pf, with R_one_way = (ohms_per_1000ft/1000)*L1
            # Solve for L1:
            denom = k_phase * load_current_a * (ohm_per_1000ft_value / 1000.0) * (pf if pf > 0 else 1e-12)
            if denom <= 0:
                return None
            length_ft = vd_target_v / denom
            # Sanity clamp to avoid absurd values if pf ~ 0
            return max(0.0, float(length_ft))
        except Exception:
            return None

    def suggest_awg_for_target_drop(self):
        try:
            vals = self._parse_and_validate()
        except ValueError as ve:
            show_error_dialog(str(ve))
            return
        target_drop_percent = safe_float(self.target_drop_percent_text.get()) or 3.0
        if target_drop_percent <= 0:
            show_error_dialog('Target Drop must be greater than 0%.')
            return

        phase_name = vals['phase']
        material_name = vals['material']
        # Evaluate all available sizes and pick the smallest conductor that still meets the target (closest from below).
        candidates = []
        for awg_value in awg_order_desc:
            try:
                _, drop_percent_value, _ = self.compute_drop_values(
                    vals['V'], vals['I'], vals['L1'], awg_value, material_name, phase_name, vals['pf']
                )
            except Exception:
                continue
            if drop_percent_value <= target_drop_percent:
                candidates.append((drop_percent_value, awg_value))

        if not candidates:
            messagebox.showwarning('Suggestion', 'No AWG in table meets the target drop for given inputs.')
            return

        # Sort by percent ascending; pick the highest percent (closest to target) -> smallest acceptable conductor
        candidates.sort(key=lambda x: x[0])
        best_percent = max(p for (p, _g) in candidates)
        best_awg = [g for (p, g) in candidates if p == best_percent][0]

        # Optionally compute a "next thicker" for reference, if exists (lower drop percent)
        thicker_alternatives = [item for item in candidates if item[0] < best_percent]
        alt_line = ''
        if thicker_alternatives:
            alt_p, alt_awg = thicker_alternatives[-1]
            alt_line = f'\nAlternative (thicker): {get_awg_label(alt_awg)} ≈ {alt_p:.2f}% drop'

        self.awg_choice_text.set(get_awg_label(best_awg))
        self.compute_voltage_drop()
        try:
            # Append a brief note to the output for clarity
            current_text = self.output_textbox.get('1.0', 'end').strip()
            current_text += f'\n\nSuggested AWG for ≤ {target_drop_percent:.2f}%: {get_awg_label(best_awg)} (≈ {best_percent:.2f}%)'
            if alt_line:
                current_text += alt_line
            self.output_textbox.delete('1.0', 'end')
            self.output_textbox.insert('end', current_text)
        except Exception:
            pass