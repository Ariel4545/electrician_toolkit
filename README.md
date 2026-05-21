# ⚡ Electrician Toolkit v0.03

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-indigo?style=for-the-badge&logo=python&logoColor=white)](https://github.com/tomschimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-GPL--3.0-green?style=for-the-badge)](LICENSE)

A premium, desktop-grade suite of utility tools designed for electricians, electronics engineers, students, and makers. Built with Python 3 and CustomTkinter, the toolkit provides an intuitive, high-fidelity experience featuring real-time value validation, dynamic physical calculations, interactive visual plots, and professional image exporters.

---

## ✨ Features (v0.03)

### 🖥️ Central Dashboard
* **Dynamic Sidebar**: Categorized tabs for **Simulation**, **Calculators**, and **References**.
* **Responsive Card Grid**: Hover micro-animations, color cues, and unified typography.
* **Polished Upgrade Path**: Locked advanced features (like Workbench and Oscilloscope) map to stylized upgrade modals that clearly articulate your upcoming roadmap.
* **System Settings**: Real-time Light/Dark/System theme toggles and a custom DPI scaling slider (ranging from `80%` to `200%`).

### ⚡ Ohm's Law Calculator
* Solve for **Voltage (V)**, **Current (I)**, **Resistance (Ω)**, or **Power (W)** by providing any two inputs.
* Real-time calculation feedback as you type (Auto-compute toggles).
* **Ohm's Wheel Plotter**: Generates a dynamic, interactive quad-formula arc chart highlighting the exact formulas used for your output.
* **Image Export**: Save vector PostScript and PNG diagrams to disk.

### 🔋 Power Calculator
* Computes complex **DC**, **AC Single-phase**, and **AC Three-phase** calculations.
* **Continuous Load Breaker Suggestions**: Recommends appropriate breaker amperages using typical continuous safety ratios.
* **Real-time Power Triangle Arc**: Visualizes Active Power ($P$), Reactive Power ($Q$), and Apparent Power ($S$) on a vector canvas.
* **Energy Cost Estimator**: Calculates billing costs (Hourly, Daily, Monthly, Yearly) based on usage time and unit rates.
* **Image Export**: Export and save your power triangles to share or document.

### 🎨 Resistor & SMD Decoder
* **Through-Hole Resistors (THT)**: Decodes **4-band**, **5-band**, and **6-band** color bands.
* **Reverse Band Finder**: Enter a target resistance (e.g., `4k7`) and tolerance to instantly compute the corresponding band sequence.
* **SMD Chip Resistor Decoder**: Decodes **3-digit** (standard), **4-digit** (precision), and **EIA-96** (1% precision) chip codes, drawing a visual representation of the chip resistor with terminals.
* **Image Export**: Export THT and SMD visual previews directly as images.

---

## 🛠️ Tech Stack & Directory Architecture

* **GUI Engine**: CustomTkinter (high-fidelity Tkinter wrappers).
* **Scientific Computing**: NumPy & Matplotlib (physics calculations and plots).
* **Image Processing**: Pillow (rendering and exporting vector drawings to PNGs).

```text
mvp/
├── main_menu.py              # Root launcher and sys.path injector
├── requirements.txt          # Python dependencies
├── LICENSE                   # Open-source MIT License
├── README.md                 # Project documentation
├── .gitignore                # Production-grade git excludes
└── toolkit/                  # Core package directory
    ├── __init__.py           # Package marker
    ├── utils/                # Calculation and parsing algorithms
    │   ├── __init__.py       # Package marker
    │   ├── parsing.py        # Real-time SI Suffix parsing (e.g. "1k2", "4u7")
    │   └── electric_utils.py # Formulas, breaker charts, and clipboard helpers
    └── windows/              # GUI top-level frames and windows
        ├── __init__.py       # Package marker
        ├── smart_entry.py    # Custom real-time input validator field
        ├── tool_window.py    # Abstract base class for calculators
        ├── dashboard_window.py# Central sidebar dashboard
        ├── ohms_law_window.py # Ohm's Law Calculator & Wheel
        ├── power_calculator_window.py # Power Calculator & Triangle
        └── resistor_colors_window.py # Color Decoder & SMD code solver
```

---

## 🚀 Installation & Running

Ensure you have **Python 3.10+** installed.

### Option A: Standard Setup (Pip)

1. Clone or copy this directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python3 main_menu.py
   ```

### Option B: High-Performance Setup (uv)

If you are using the modern, ultra-fast Python package manager **`uv`**, run the application directly in a fully-compliant sandbox:
```bash
uv run main_menu.py
```

---

## 🖥️ Platform-Specific Tips (Linux Mint / Ubuntu Cinnamon)

On Linux distributions using fractional scaling (such as Linux Mint Cinnamon), Tkinter auto-scaling can sometimes read broken scale factors. 
* **Scaling Reset**: The toolkit automatically resets default scaling to a razor-sharp standard `1.0` (100%) at launch to prevent text distortions.
* **Custom Zoom**: If widgets look too small on high-resolution screens (like 4K), navigate to **Settings** in the sidebar and increase **UI Scaling** to a clean, crisp factor (e.g., `120%`, `150%`, or `200%`).

