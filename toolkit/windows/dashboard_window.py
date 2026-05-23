import customtkinter as ctk
import tkinter as tk
import os
import time

# Import active tools
from windows.ohms_law_window import ohms_law_window
from windows.power_calculator_window import power_calculator_window
from windows.resistor_colors_window import resistor_colors_window
from windows.voltage_drop_window import voltage_drop_window
from windows.equivalent_resistance_window import equivalent_resistance_window

class ToolCard(ctk.CTkFrame):
    def __init__(self, master, title, desc, icon, command):
        super().__init__(master, corner_radius=12, fg_color=("white", "gray17"), border_width=0)
        self.command = command
        
        # Hover effect handling
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
        self.icon_label = ctk.CTkLabel(self, text=icon, font=("Segoe UI Emoji", 32))
        self.icon_label.pack(padx=15, pady=(15, 5))
        
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        self.title_label.pack(padx=10, pady=(0, 2))
        
        self.desc_label = ctk.CTkLabel(self, text=desc, font=ctk.CTkFont(size=11), text_color="gray60", wraplength=140)
        self.desc_label.pack(padx=10, pady=(0, 15))
        
        # Bind children to click
        for w in [self.icon_label, self.title_label, self.desc_label]:
            w.bind("<Button-1>", self.on_click)
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.configure(fg_color=("gray95", "gray22"))
    
    def on_leave(self, e):
        self.configure(fg_color=("white", "gray17"))

    def on_click(self, e):
        if self.command:
            self.command()

class DashboardWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Electrician Toolkit MVP 1.0")
        self.geometry("1100x720")
        
        # Solve Linux Mint / Cinnamon window distortion by forcing standard crisp 1:1 scaling
        # and letting the user customize it cleanly in the Settings tab
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_sidebar()
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color=("gray95", "gray10"))
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.show_dashboard()

    def _init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self.sidebar, text="⚡ Toolkit", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self._add_sidebar_btn("Dashboard", self.show_dashboard, 1)
        self._add_sidebar_btn("Workbench", self.open_workbench, 2)
        self._add_sidebar_btn("Settings", self.show_settings, 3)

        # Bottom info
        ctk.CTkLabel(self.sidebar, text="v1.0 MVP", text_color="gray50").grid(row=5, column=0, pady=20)

    def _add_sidebar_btn(self, text, cmd, row):
        btn = ctk.CTkButton(self.sidebar, text=text, command=cmd, fg_color="transparent", 
                          text_color=("gray10", "gray90"), anchor="w", height=40,
                          hover_color=("gray80", "gray25"))
        btn.grid(row=row, column=0, padx=10, pady=2, sticky="ew")

    def show_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Hero Banner
        hero = ctk.CTkFrame(self.main_frame, fg_color=("#3B8ED0", "#1F6AA5"), corner_radius=10)
        hero.grid(row=0, column=0, padx=30, pady=30, sticky="ew")
        
        ctk.CTkLabel(hero, text="Welcome to Electrician Toolkit MVP", font=ctk.CTkFont(size=26, weight="bold"), text_color="white").pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(hero, text="Design, Simulate, and Calculate. Start with our core stable tools.", font=ctk.CTkFont(size=14), text_color="#E0E0E0").pack(anchor="w", padx=30, pady=(0, 30))

        # Content Grid
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.grid(row=1, column=0, padx=30, sticky="nsew")
        
        # Tools Tabs
        tabview = ctk.CTkTabview(content, width=800)
        tabview.pack(fill="both", expand=True)
        tabview.add("Simulation")
        tabview.add("Calculators")
        tabview.add("Reference")

        # Tool Definitions
        self.tools_sim = [
            ("Workbench", "Circuit Simulator & PCB Design", "🔬", "electronics_workbench"),
            ("Oscilloscope", "4-Channel Scope Data Viewer", "📈", "oscilloscope"),
            ("Logic Analyzer", "Digital Protocol Analyzer", "📊", "logic_analyzer"),
            ("RLC Analyzer", "Impedance & Network Analysis", "🌀", "rlc_analyzer"),
        ]
        
        self.tools_calc = [
            ("Ohm's Law", "V, I, R, P Relationships", "⚡", ohms_law_window),
            ("Power Calc", "DC Power Dissipation", "🔋", power_calculator_window),
            ("Volt Drop", "Wire Voltage Loss Estimator", "📉", voltage_drop_window),
            ("555 Timer", "Astable & Monostable Design", "⏲️", "timer_555"),
            ("Battery Life", "Runtime Estimator", "🔋", "battery_life"),
            ("LED Resistor", "Series Limiting Resistor", "💡", "led_resistor"),
            ("Volt Divider", "Resistive Division", "➗", "voltage_divider"),
            ("Filters", "Active/Passive Filter Design", "〰️", "filter_design"),
            ("Equiv. Res", "Series/Parallel/Star-Delta", "🕸️", equivalent_resistance_window),
        ]
        
        self.tools_ref = [
            ("Resistor Colors", "Band Code Decoder", "🎨", resistor_colors_window),
            ("Wire Gauge", "AWG Ampacity Table", "📏", "wire_gauge"),
            ("Pinouts", "Common Connector Maps", "🔌", "pinouts"),
        ]

        self._populate_grid(tabview.tab("Simulation"), self.tools_sim)
        self._populate_grid(tabview.tab("Calculators"), self.tools_calc)
        self._populate_grid(tabview.tab("Reference"), self.tools_ref)

    def _populate_grid(self, parent, items):
        cols = 4
        for i, (title, desc, icon, cls) in enumerate(items):
            card = ToolCard(parent, title, desc, icon, lambda t=title, c=cls: self.open_tool(t, c))
            card.grid(row=i//cols, column=i%cols, padx=10, pady=10, sticky="nsew")
            parent.grid_columnconfigure(i%cols, weight=1)

    def show_feature_coming_soon(self, tool_name):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Feature Coming Soon")
        dialog.geometry("420x210")
        dialog.resizable(False, False)
        dialog.transient(self)
        
        # Center the dialog nicely on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (420 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (210 // 2)
        dialog.geometry(f"420x210+{x}+{y}")
        
        # Safely set grab lock to handle X11 mapping lag gracefully
        try:
            dialog.grab_set()
        except Exception:
            pass
        
        label_icon = ctk.CTkLabel(dialog, text="🚀", font=("Segoe UI Emoji", 48))
        label_icon.pack(pady=(20, 5))
        
        label_title = ctk.CTkLabel(dialog, text=f"{tool_name} is coming soon!", font=ctk.CTkFont(size=16, weight="bold"))
        label_title.pack(pady=5)
        
        label_desc = ctk.CTkLabel(dialog, text="This advanced tool is planned for a subsequent Phase of our MVP rollout.", font=ctk.CTkFont(size=11), text_color="gray60")
        label_desc.pack(pady=2)
        
        btn_ok = ctk.CTkButton(dialog, text="Looking Forward to It", width=160, command=dialog.destroy)
        btn_ok.pack(pady=(15, 15))

    def open_tool(self, title, tool_cls):
        if isinstance(tool_cls, str):
            self.show_feature_coming_soon(title)
            return
            
        try:
            win = tool_cls(self)
            win.focus()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to open tool: {e}")
            
    def open_workbench(self):
        self.show_feature_coming_soon("Workbench Simulator")

    def show_settings(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        ctk.CTkLabel(self.main_frame, text="Settings", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=30, pady=30)
        
        frame = ctk.CTkFrame(self.main_frame, fg_color=("white", "gray17"))
        frame.pack(fill="x", padx=30)
        
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(row1, text="Appearance Mode").pack(side="left")
        ctk.CTkOptionMenu(row1, values=["Dark", "Light", "System"], command=ctk.set_appearance_mode).pack(side="right")
        
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(row2, text="UI Scaling").pack(side="left")
        
        # Added broader values for scaling to handle High-DPI screens beautifully
        ctk.CTkOptionMenu(row2, values=["80%", "95%", "100%", "110%", "120%", "130%", "140%", "150%", "175%", "200%"], 
                        command=lambda s: self.update_scaling(int(s.replace("%",""))/100)).pack(side="right")

    def update_scaling(self, factor):
        ctk.set_widget_scaling(factor)
        ctk.set_window_scaling(factor)

if __name__ == "__main__":
    app = DashboardWindow()
    app.mainloop()

