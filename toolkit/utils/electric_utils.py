import math
import customtkinter as ctk
from tkinter import messagebox

app_title_text = 'Electrician Toolkit (CustomTkinter)'

awg_reference_map = {
    # ohms per 1000 ft at ~20°C (approx.)
    # awg: { 'area_mm2': y, 'ohms_per_1000ft_cu': a, 'ohms_per_1000ft_al': b, 'ampacity_est_a': c }
    14: {'area_mm2': 2.08, 'ohms_per_1000ft_cu': 2.525, 'ohms_per_1000ft_al': 4.016, 'ampacity_est_a': 15},
    12: {'area_mm2': 3.31, 'ohms_per_1000ft_cu': 1.588, 'ohms_per_1000ft_al': 2.525, 'ampacity_est_a': 20},
    10: {'area_mm2': 5.26, 'ohms_per_1000ft_cu': 0.999, 'ohms_per_1000ft_al': 1.588, 'ampacity_est_a': 30},
    8:  {'area_mm2': 8.37, 'ohms_per_1000ft_cu': 0.6282, 'ohms_per_1000ft_al': 0.999, 'ampacity_est_a': 40},
    6:  {'area_mm2': 13.3, 'ohms_per_1000ft_cu': 0.3953, 'ohms_per_1000ft_al': 0.6282, 'ampacity_est_a': 55},
    4:  {'area_mm2': 21.1, 'ohms_per_1000ft_cu': 0.2485, 'ohms_per_1000ft_al': 0.3953, 'ampacity_est_a': 70},
    3:  {'area_mm2': 26.7, 'ohms_per_1000ft_cu': 0.1970, 'ohms_per_1000ft_al': 0.3133, 'ampacity_est_a': 85},
    2:  {'area_mm2': 33.6, 'ohms_per_1000ft_cu': 0.1563, 'ohms_per_1000ft_al': 0.2485, 'ampacity_est_a': 95},
    1:  {'area_mm2': 42.4, 'ohms_per_1000ft_cu': 0.1239, 'ohms_per_1000ft_al': 0.1970, 'ampacity_est_a': 110},
    0:  {'area_mm2': 53.5, 'ohms_per_1000ft_cu': 0.0983, 'ohms_per_1000ft_al': 0.1563, 'ampacity_est_a': 125},
    -1: {'area_mm2': 67.4, 'ohms_per_1000ft_cu': 0.0779, 'ohms_per_1000ft_al': 0.1239, 'ampacity_est_a': 150},  # 2/0
    -2: {'area_mm2': 85.0, 'ohms_per_1000ft_cu': 0.0618, 'ohms_per_1000ft_al': 0.0983, 'ampacity_est_a': 175},  # 3/0
    -3: {'area_mm2': 107.2,'ohms_per_1000ft_cu': 0.0490, 'ohms_per_1000ft_al': 0.0779, 'ampacity_est_a': 200},  # 4/0
}
awg_order_desc = sorted(awg_reference_map.keys(), reverse=True)

band_color_table = [
    ('Black', 0, 1, None),
    ('Brown', 1, 10, '±1%'),
    ('Red', 2, 100, '±2%'),
    ('Orange', 3, 1_000, None),
    ('Yellow', 4, 10_000, None),
    ('Green', 5, 100_000, '±0.5%'),
    ('Blue', 6, 1_000_000, '±0.25%'),
    ('Violet', 7, 10_000_000, '±0.1%'),
    ('Gray', 8, 100_000_000, '±0.05%'),
    ('White', 9, 1_000_000_000, None),
    ('Gold', None, 0.1, '±5%'),
    ('Silver', None, 0.01, '±10%'),
]

common_breakers_a = [15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200]


def get_awg_label(awg_value: int) -> str:
    label_map = {-1: '2/0', -2: '3/0', -3: '4/0'}
    return str(awg_value) if awg_value >= 0 else label_map.get(awg_value, f'?({awg_value})')


def parse_awg_label(text_value: str) -> int:
    reverse_map = {'2/0': -1, '3/0': -2, '4/0': -3}
    if text_value in reverse_map:
        return reverse_map[text_value]
    return int(text_value)


def format_si_unit(number_value: float, unit_suffix: str) -> str:
    try:
        number_abs = abs(number_value)
        if number_abs == 0:
            return f'0 {unit_suffix}'
        pairs = [('G', 1e9), ('M', 1e6), ('k', 1e3), ('', 1), ('m', 1e-3), ('µ', 1e-6), ('n', 1e-9)]
        for prefix_text, factor_value in pairs:
            if number_abs >= factor_value and factor_value >= 1:
                return f'{number_value / factor_value:.4g} {prefix_text}{unit_suffix}'
        for prefix_text, factor_value in pairs[4:]:
            if number_abs >= factor_value:
                return f'{number_value / factor_value:.4g} {prefix_text}{unit_suffix}'
        return f'{number_value:.4g} {unit_suffix}'
    except Exception:
        return f'{number_value} {unit_suffix}'


def safe_float(text_value: str):
    text_clean = (text_value or '').strip()
    if not text_clean:
        return None
    try:
        return float(text_clean)
    except Exception:
        return None


def show_error_dialog(message_text: str):
    messagebox.showerror('Input Error', message_text)


def copy_text_to_clipboard(window_root: ctk.CTk, text_value: str):
    try:
        window_root.clipboard_clear()
        window_root.clipboard_append(text_value)
        messagebox.showinfo('Copied', 'Results copied to clipboard.')
    except Exception:
        pass


def round_up_breaker_amps(requested_current_a: float) -> int:
    for breaker_value in common_breakers_a:
        if requested_current_a <= breaker_value:
            return breaker_value
    return common_breakers_a[-1]
