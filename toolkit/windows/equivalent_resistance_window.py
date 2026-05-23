import re
import customtkinter as ctk
from utils.electric_utils import format_si_unit, copy_text_to_clipboard, show_error_dialog
from windows.tool_window import tool_window


class equivalent_resistance_window(tool_window):
    def __init__(self, master_root):
        super().__init__(master_root, 'Equivalent Resistance')

        # layout
        self.content_frame = ctk.CTkFrame(self, corner_radius=8)
        self.content_frame.grid(row=0, column=0, sticky='nsew', padx=12, pady=12)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(10, weight=1)

        # state
        self.mode_text = ctk.StringVar(value='Series')
        self.resistances_text = ctk.StringVar()
        self.auto_compute_enabled = ctk.BooleanVar(value=False)

        # values list builder state
        self.values_list = []
        self.single_value_text = ctk.StringVar()

        # header
        self.header_label = ctk.CTkLabel(self.content_frame, text='Compute equivalent resistance from a list')
        self.header_label.grid(row=0, column=0, sticky='w', padx=6, pady=(0, 6))

        # entry prompt
        self.label_prompt = ctk.CTkLabel(self.content_frame, text='Resistances list (Ω) - comma or space separated')
        self.label_prompt.grid(row=1, column=0, sticky='w', padx=6, pady=(2, 2))
        self.entry_values = ctk.CTkEntry(
            self.content_frame,
            textvariable=self.resistances_text,
            placeholder_text='Examples: 10, 20, 47k   or   2.2k 330 1M   or   4R7 1k 220'
        )
        self.entry_values.grid(row=2, column=0, sticky='we', padx=6, pady=(0, 6))

        # mode + actions row
        self.controls_row = ctk.CTkFrame(self.content_frame)
        self.controls_row.grid(row=3, column=0, sticky='we', padx=6, pady=(0, 6))
        self.controls_row.grid_columnconfigure(0, weight=1)
        self.segmented_mode = ctk.CTkSegmentedButton(self.controls_row, values=['Series', 'Parallel'], variable=self.mode_text)
        self.segmented_mode.grid(row=0, column=0, sticky='w', padx=0, pady=0)

        self.button_compute = ctk.CTkButton(self.controls_row, text='Compute', command=self.compute_equivalent_resistance)
        self.button_compute.grid(row=0, column=1, padx=(8, 0))
        self.button_reset = ctk.CTkButton(self.controls_row, text='Reset', command=self.reset_form)
        self.button_reset.grid(row=0, column=2, padx=8)
        self.checkbox_auto_compute = ctk.CTkCheckBox(
            self.controls_row,
            text='Auto-compute',
            variable=self.auto_compute_enabled,
            command=self._maybe_auto_compute
        )
        self.checkbox_auto_compute.grid(row=0, column=3, padx=8, sticky='e')

        # list builder (optional, friendlier UI)
        self.list_builder_frame = ctk.CTkFrame(self.content_frame)
        self.list_builder_frame.grid(row=4, column=0, sticky='we', padx=6, pady=(2, 6))
        self.list_builder_frame.grid_columnconfigure(1, weight=1)

        self.label_add_single = ctk.CTkLabel(self.list_builder_frame, text='Add single value (supports k/M/R):')
        self.label_add_single.grid(row=0, column=0, padx=(0, 6), pady=(0, 4), sticky='w')
        self.entry_single_value = ctk.CTkEntry(self.list_builder_frame, textvariable=self.single_value_text, placeholder_text='e.g., 4R7 or 330 or 2.2k or 1M')
        self.entry_single_value.grid(row=0, column=1, sticky='we', padx=(0, 6), pady=(0, 4))
        self.button_add_single = ctk.CTkButton(self.list_builder_frame, text='Add', width=80, command=self.add_single_value_to_list)
        self.button_add_single.grid(row=0, column=2, padx=(0, 6), pady=(0, 4))

        self.values_toolbar_row = ctk.CTkFrame(self.list_builder_frame)
        self.values_toolbar_row.grid(row=1, column=0, columnspan=3, sticky='we', pady=(0, 4))
        self.button_remove_last = ctk.CTkButton(self.values_toolbar_row, text='Remove last', command=self.remove_last_value)
        self.button_remove_last.pack(side='left', padx=4)
        self.button_clear_list = ctk.CTkButton(self.values_toolbar_row, text='Clear list', command=self.clear_values_list)
        self.button_clear_list.pack(side='left', padx=4)
        self.button_sort_asc = ctk.CTkButton(self.values_toolbar_row, text='Sort ↑', command=lambda: self.sort_values_list(True))
        self.button_sort_asc.pack(side='left', padx=4)
        self.button_sort_desc = ctk.CTkButton(self.values_toolbar_row, text='Sort ↓', command=lambda: self.sort_values_list(False))
        self.button_sort_desc.pack(side='left', padx=4)
        self.button_apply_list_to_entry = ctk.CTkButton(self.values_toolbar_row, text='Apply to input', command=self.apply_list_to_main_entry)
        self.button_apply_list_to_entry.pack(side='right', padx=4)

        self.values_preview_textbox = ctk.CTkTextbox(self.list_builder_frame, height=70)
        self.values_preview_textbox.grid(row=2, column=0, columnspan=3, sticky='we', padx=(0, 6))

        # status/result
        self.result_label = ctk.CTkLabel(self.content_frame, text='Result: ')
        self.result_label.grid(row=5, column=0, sticky='w', padx=6, pady=(2, 2))

        self.status_label = ctk.CTkLabel(self.content_frame, text='', text_color='orange')
        self.status_label.grid(row=6, column=0, sticky='w', padx=6, pady=(0, 4))

        # quick stats
        self.stats_row = ctk.CTkFrame(self.content_frame)
        self.stats_row.grid(row=7, column=0, sticky='we', padx=6, pady=(0, 6))
        self.label_count = ctk.CTkLabel(self.stats_row, text='Count: 0')
        self.label_count.pack(side='left', padx=6)
        self.label_min = ctk.CTkLabel(self.stats_row, text='Min: —')
        self.label_min.pack(side='left', padx=6)
        self.label_max = ctk.CTkLabel(self.stats_row, text='Max: —')
        self.label_max.pack(side='left', padx=6)

        # details output
        self.output_textbox = ctk.CTkTextbox(self.content_frame, height=220)
        self.output_textbox.grid(row=10, column=0, sticky='nsew', padx=6, pady=(0, 6))

        # footer
        self.footer_row = ctk.CTkFrame(self.content_frame)
        self.footer_row.grid(row=11, column=0, sticky='we', padx=6, pady=(0, 6))
        self.button_copy = ctk.CTkButton(self.footer_row, text='Copy Results', command=self.copy_result_to_clipboard)
        self.button_copy.pack(side='right', padx=6)

        # keybinds
        try:
            self.bind('<Return>', lambda event: self.compute_equivalent_resistance())
            self.bind('<Escape>', lambda event: self.reset_form())
        except Exception:
            pass

    def _maybe_auto_compute(self):
        if self.auto_compute_enabled.get():
            self.compute_equivalent_resistance()

    # ---------- list builder helpers ----------
    def add_single_value_to_list(self):
        token = (self.single_value_text.get() or '').strip()
        if not token:
            return
        try:
            value_ohms = self.parse_one_resistance(token)
            self.values_list.append(value_ohms)
            self.single_value_text.set('')
            self.refresh_values_preview()
            self._maybe_auto_compute()
        except Exception as parse_error:
            show_error_dialog(str(parse_error))

    def remove_last_value(self):
        if self.values_list:
            self.values_list.pop()
            self.refresh_values_preview()
            self._maybe_auto_compute()

    def clear_values_list(self):
        self.values_list = []
        self.refresh_values_preview()
        self._maybe_auto_compute()

    def sort_values_list(self, ascending: bool = True):
        try:
            self.values_list = sorted(self.values_list, reverse=(not ascending))
            self.refresh_values_preview()
            self._maybe_auto_compute()
        except Exception:
            pass

    def refresh_values_preview(self):
        try:
            self.values_preview_textbox.delete('1.0', 'end')
            if not self.values_list:
                return
            lines = [format_si_unit(v, 'Ω') for v in self.values_list]
            self.values_preview_textbox.insert('end', ', '.join(lines))
            # update quick stats
            self.label_count.configure(text=f'Count: {len(self.values_list)}')
            self.label_min.configure(text=f'Min: {format_si_unit(min(self.values_list), "Ω")}')
            self.label_max.configure(text=f'Max: {format_si_unit(max(self.values_list), "Ω")}')
        except Exception:
            pass

    def apply_list_to_main_entry(self):
        try:
            if not self.values_list:
                return
            join_text = ', '.join([format_si_unit(v, 'Ω').replace(' Ω', '') for v in self.values_list])
            self.resistances_text.set(join_text)
            self._maybe_auto_compute()
        except Exception:
            pass

    # ---------- parsing ----------
    def parse_resistances(self, raw_text: str):
        """
        Parse a list of resistances with optional SI suffixes into floats (ohms).
        Supports: G, M, k, (none), m, u/µ, n
        Also supports resistor notation: 4R7 => 4.7Ω, 1K2 => 1.2kΩ, 2M2 => 2.2MΩ
        Accepts both commas and spaces as separators.
        """
        if not raw_text or not raw_text.strip():
            return []

        normalized = raw_text.replace(',', ' ')
        tokens = [t for t in normalized.split(' ') if t.strip()]

        values = []
        for token in tokens:
            values.append(self.parse_one_resistance(token))
        return values

    def parse_one_resistance(self, token: str) -> float:
        piece = (token or '').strip()
        if not piece:
            raise ValueError('Empty resistance token.')
        # Normalize unicode ohm and micro
        piece = piece.replace('ω', 'Ω').replace('OHM', 'Ω').replace('ohm', 'Ω').replace('Ohm', 'Ω')
        # Handle resistor letter decimal (R/K/M inside number): e.g., 4R7, 1K2, 2M2
        match = re.fullmatch(r'([+-]?\d*)([RrKkMmGg])?(\d*)([uUµnNmMkKgG]?)', piece)
        if match:
            int_part, mid_letter, frac_part, suffix_letter = match.groups()
            if mid_letter:
                # R/K/M inside number acts as decimal point with implicit suffix from the letter if it's K/M/G
                decimal_point_value = (int_part or '0') + '.' + (frac_part or '0')
                base_value = float(decimal_point_value)
                implicit_suffix = mid_letter.upper()
                if implicit_suffix == 'R':
                    factor = 1.0
                elif implicit_suffix == 'K':
                    factor = 1e3
                elif implicit_suffix == 'M':
                    factor = 1e6
                elif implicit_suffix == 'G':
                    factor = 1e9
                else:
                    factor = 1.0
                return base_value * factor
        # Otherwise: standard number with optional suffix at end (case sensitive for M vs m)
        # Extract numeric part (with optional decimal) and suffix
        num_match = re.fullmatch(r'([+-]?\d+(?:\.\d+)?)([uUµnNmMkKgG]?)', piece)
        if not num_match:
            raise ValueError(f'Invalid resistance: "{token}"')
        number_str, suffix = num_match.groups()
        base = float(number_str)
        # Suffix map: honor case: M=mega, m=milli
        suffix_map = {
            '': 1.0,
            'R': 1.0, 'r': 1.0,
            'k': 1e3, 'K': 1e3,
            'M': 1e6,
            'G': 1e9, 'g': 1e9,
            'm': 1e-3,
            'u': 1e-6, 'U': 1e-6, 'µ': 1e-6,
            'n': 1e-9, 'N': 1e-9,
        }
        factor = suffix_map.get(suffix, None)
        if factor is None:
            # If we had 'Ω' or other trailing symbols, strip and retry quickly
            cleaned = piece.replace('Ω', '')
            if cleaned != piece:
                return self.parse_one_resistance(cleaned)
            raise ValueError(f'Invalid suffix in: "{token}"')
        return base * factor

    # ---------- compute ----------
    def compute_equivalent_resistance(self):
        self.status_label.configure(text='')
        self.output_textbox.delete('1.0', 'end')

        raw_values_text = (self.resistances_text.get() or '').strip()
        values_from_entry = []
        if raw_values_text:
            try:
                values_from_entry = self.parse_resistances(raw_values_text)
            except Exception as parse_error:
                self.status_label.configure(text=str(parse_error))
                show_error_dialog(str(parse_error))
                return

        # Merge with list-builder values if present
        values_all = []
        if self.values_list:
            values_all.extend(self.values_list)
        if values_from_entry:
            values_all.extend(values_from_entry)

        if not values_all:
            self.result_label.configure(text='Result: ')
            self.status_label.configure(text='Enter or add one or more resistances to compute.')
            return

        try:
            calculation_mode = self.mode_text.get().strip().lower()
            details_lines = []
            details_lines.append('Details')
            details_lines.append('-------')

            # Pretty list of inputs
            values_formatted = [format_si_unit(v, 'Ω') for v in values_all]
            details_lines.append('Input values: ' + ', '.join(values_formatted))
            details_lines.append('Mode: ' + ('Series' if calculation_mode.startswith('s') else 'Parallel'))

            if calculation_mode.startswith('s'):
                equivalent_value = sum(values_all)
                details_lines.append('Computation: R_eq = Σ R_i')
            else:
                inverse_sum = 0.0
                for resistance_value in values_all:
                    if resistance_value <= 0:
                        raise ValueError('All resistances must be > 0 for parallel calculation.')
                    inverse_sum += 1.0 / resistance_value
                equivalent_value = float('inf') if inverse_sum == 0 else (1.0 / inverse_sum)
                details_lines.append('Computation: 1/R_eq = Σ (1/R_i)')

            formatted_result = format_si_unit(equivalent_value, 'Ω')
            self.result_label.configure(text='Result: ' + formatted_result)

            # Quick stats block
            count_value = len(values_all)
            min_value = min(values_all)
            max_value = max(values_all)
            self.label_count.configure(text=f'Count: {count_value}')
            self.label_min.configure(text=f'Min: {format_si_unit(min_value, "Ω")}')
            self.label_max.configure(text=f'Max: {format_si_unit(max_value, "Ω")}')

            # Hints
            if not calculation_mode.startswith('s') and count_value >= 2:
                smallest = min_value
                if equivalent_value < smallest * 0.9:
                    details_lines.append('Tip: Parallel equivalent is notably lower than the smallest resistor.')

            # Write details
            self.output_textbox.insert('end', '\n'.join(details_lines))

        except Exception as compute_error:
            error_text = str(compute_error)
            self.status_label.configure(text=error_text)
            show_error_dialog(error_text)

    # ---------- misc UI ----------
    def reset_form(self):
        self.resistances_text.set('')
        self.mode_text.set('Series')
        self.values_list = []
        self.refresh_values_preview()
        self.result_label.configure(text='Result: ')
        self.status_label.configure(text='')
        try:
            self.output_textbox.delete('1.0', 'end')
        except Exception:
            pass
        # reset quick stats
        self.label_count.configure(text='Count: 0')
        self.label_min.configure(text='Min: —')
        self.label_max.configure(text='Max: —')

    def fill_example_values(self, mode_name: str = 'Series'):
        # Provide curated examples for both modes (entry + list builder)
        if str(mode_name).lower().startswith('p'):
            self.mode_text.set('Parallel')
            self.values_list = [self.parse_one_resistance(x) for x in ['220', '330', '470']]
            self.resistances_text.set('220, 330, 470')
        else:
            self.mode_text.set('Series')
            self.values_list = [self.parse_one_resistance(x) for x in ['1k', '2.2k', '330']]
            self.resistances_text.set('1k, 2.2k, 330')
        self.refresh_values_preview()
        self.compute_equivalent_resistance()

    def copy_result_to_clipboard(self):
        try:
            header_text = self.result_label.cget('text') or ''
            details_text = self.output_textbox.get('1.0', 'end').strip()
            preview_text = self.values_preview_textbox.get('1.0', 'end').strip()
            final_text = header_text.strip()
            if preview_text:
                final_text += '\nList: ' + preview_text
            if details_text:
                final_text = final_text + '\n' + details_text
            copy_text_to_clipboard(self, final_text)
        except Exception as copy_error:
            show_error_dialog(str(copy_error))