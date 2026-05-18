import re
from typing import Union, Any

# Sentinel object to detect if default was provided
_NO_DEFAULT = object()

def parse_value(val: Union[str, int, float], default: Any = _NO_DEFAULT) -> float:
    """
    Parse a value string with optional SI suffixes or resistor notation into a float.
    
    Args:
        val: The value to parse (string, int, or float).
        default: If provided, this value is returned on parsing failure or empty input.
    
    Examples:
    - "1k" -> 1000.0
    - "4R7" -> 4.7
    - "2.2u" -> 2.2e-6
    - "1e-9" -> 1.0e-9
    """
    if isinstance(val, (int, float)):
        return float(val)
        
    s = str(val).strip()
    
    if not s:
        if default is not _NO_DEFAULT:
            return default
        raise ValueError("Empty value")
        
    # Unicode normalizations for Units
    s = s.replace('ω', 'Ω').replace('OHM', 'Ω').replace('ohm', 'Ω').replace('Ohm', 'Ω')
    
    # --- Unit Stripping ---
    full_units = ['farad', 'henry', 'volt', 'amp', 'hertz', 'ohm', 'sec', 'second']
    s_lower = s.lower()
    for unit in full_units:
        if s_lower.endswith(unit):
            s = s[:-len(unit)].strip()
            s_lower = s_lower[:-len(unit)].strip()
            break
            
    if s.endswith('Hz'): 
        s = s[:-2].strip()
        
    s = re.sub(r'\s*[VAFHΩsW]$', '', s)
    s = s.strip()
    
    if not s:
        if default is not _NO_DEFAULT: return default
        raise ValueError("Value contained only units")
    
    # Strategy 1: Scientific Notation / Simple Float
    try:
        return float(s)
    except ValueError:
        pass
        
    # Strategy 2: Resistor Notation (e.g. 4R7, 1k2)
    match_res = re.fullmatch(r'([+-]?\d*)([RrKkMmGgTt])(\d+)([uUµnNmMkKgG]?)', s)
    if match_res:
        int_part, mid_letter, frac_part, suffix_end = match_res.groups()
        val_str = f"{int_part or '0'}.{frac_part}"
        try:
            base = float(val_str)
        except ValueError:
            if default is not _NO_DEFAULT: return default
            raise ValueError(f"Invalid resistor format construction '{val_str}'")
            
        mid_upper = mid_letter.upper()
        scale = 1.0
        
        if mid_letter == 'm': scale = 1e-3
        elif mid_upper == 'R': scale = 1.0
        elif mid_upper == 'K': scale = 1e3
        elif mid_upper == 'M': scale = 1e6
        elif mid_upper == 'G': scale = 1e9
        elif mid_upper == 'T': scale = 1e12
        
        return base * scale
        
    # Strategy 3: Standard Suffixes (e.g. 100k, 10u)
    match_sf = re.match(r'([+-]?\d*(?:\.\d+)?)(.*)', s)
    if match_sf:
        num_str = match_sf.group(1)
        suffix = match_sf.group(2).strip()
        
        if not num_str:
            if default is not _NO_DEFAULT: return default
            raise ValueError(f"No numeric part in '{val}'")
            
        try:
            val_float = float(num_str)
        except ValueError:
            if default is not _NO_DEFAULT: return default
            raise ValueError(f"Invalid number format '{num_str}'")
            
        if not suffix:
            return val_float
            
        first = suffix[0]
        
        if suffix.lower().startswith("meg"):
            return val_float * 1e6
            
        if first in ('k', 'K'): return val_float * 1e3
        if first == 'M': return val_float * 1e6
        if first == 'G': return val_float * 1e9
        if first == 'T': return val_float * 1e12
        if first == 'm': return val_float * 1e-3
        if first in ('u', 'µ', 'U'): return val_float * 1e-6
        if first in ('n', 'N'): return val_float * 1e-9
        if first in ('p', 'P'): return val_float * 1e-12
        if first == 'f': return val_float * 1e-15
        
        if first in ('R', 'r') and len(suffix) == 1: 
            return val_float
            
    if default is not _NO_DEFAULT:
        return default
        
    raise ValueError(f"Could not parse value '{val}'")

def format_value(value: float, unit: str = '', precision: int = 4) -> str:
    """
    Format a float into a string with SI suffix.
    e.g. 1500, "Hz" -> "1.5 kHz"
    """
    try:
        val_abs = abs(value)
        if val_abs == 0:
            return f"0 {unit}".strip()
            
        suffixes = [
            ('T', 1e12), ('G', 1e9), ('M', 1e6), ('k', 1e3), 
            ('', 1.0), 
            ('m', 1e-3), ('µ', 1e-6), ('n', 1e-9), ('p', 1e-12), ('f', 1e-15)
        ]
        
        selected_suffix = ''
        divisor = 1.0
        
        if val_abs >= 1.0:
            for s, mult in suffixes[:5]:
                if val_abs >= mult:
                    selected_suffix = s
                    divisor = mult
                    break
        else:
            for s, mult in suffixes[5:]:
                if val_abs >= mult:
                    selected_suffix = s
                    divisor = mult
                    break
            if val_abs < 1e-15:
                selected_suffix = 'f'
                divisor = 1e-15
                
        scaled = value / divisor
        fmt = f"{{:.{precision}g}}"
        formatted_num = fmt.format(scaled)
        
        if unit:
            return f"{formatted_num} {selected_suffix}{unit}"
        else:
            return f"{formatted_num}{selected_suffix}"
            
    except Exception:
        return f"{value} {unit}".strip()

format_si_unit = format_value
