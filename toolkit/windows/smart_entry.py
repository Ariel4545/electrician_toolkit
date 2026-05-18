import customtkinter as ctk
from toolkit.utils.parsing import parse_value

class SmartEntry(ctk.CTkEntry):
    def __init__(self, master, min_val=None, max_val=None, si=True, command=None, **kwargs):
        """
        A smart entry widget that handles validation and SI parsing.
        
        Args:
            master: The parent widget.
            min_val (float, optional): Minimum allowed value.
            max_val (float, optional): Maximum allowed value.
            si (bool): If True, accepts SI suffixes (k, m, u, etc.). Default True.
            command (callable, optional): Callback for when valid input is confirmed (Enter key).
            **kwargs: Standard CTkEntry arguments.
        """
        super().__init__(master, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.si = si
        self.command = command
        
        try:
            self._default_border_color = self._border_color
        except AttributeError:
            self._default_border_color = "gray"
            
        self._error_border_color = "#FF5555" # Light red
        
        # Bindings for real-time validation
        self.bind('<FocusOut>', self._validate_event)
        self.bind('<KeyRelease>', self._validate_event)
        self.bind('<Return>', self._on_return)

    def _validate_event(self, event=None):
        self.validate()

    def _on_return(self, event):
        if self.validate():
            if self.command:
                self.command()

    def validate(self):
        """
        Checks the current text against rules. 
        Updates visual state (border color).
        Returns True if valid (or empty), False otherwise.
        """
        text = self.get().strip()
        
        if not text:
            self.configure(border_color=self._default_border_color)
            return True
            
        try:
            val = parse_value(text) if self.si else float(text)
            
            if self.min_val is not None and val < self.min_val:
                raise ValueError("Below min")
            if self.max_val is not None and val > self.max_val:
                raise ValueError("Above max")
                
            self.configure(border_color=self._default_border_color)
            return True
            
        except Exception:
            self.configure(border_color=self._error_border_color)
            return False

    def get_value(self):
        """
        Returns the parsed float value if valid, None otherwise.
        """
        if self.validate():
            text = self.get().strip()
            if not text:
                return None
            try:
                return parse_value(text) if self.si else float(text)
            except:
                return None
        return None
