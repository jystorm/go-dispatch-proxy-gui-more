import customtkinter as ctk

class BarGraph(ctk.CTkFrame):
    def __init__(self, master, width=120, height=16, max_value=100, bar_color="#3B8ED0", bg_color="#222", **kwargs):
        super().__init__(master, fg_color=bg_color, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self.max_value = max_value
        self.bar_color = bar_color
        self.canvas = ctk.CTkCanvas(self, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bar = None
        self.value = 0
        self._draw_bar(0)

    def set_value(self, value, max_value=None):
        if max_value is not None:
            self.max_value = max_value
        self.value = max(0, min(value, self.max_value))
        self._draw_bar(self.value)

    def _draw_bar(self, value):
        self.canvas.delete("all")
        if self.max_value == 0:
            fill_width = 0
        else:
            fill_width = int(self.width * value / self.max_value)
        self.canvas.create_rectangle(0, 0, fill_width, self.height, fill=self.bar_color, width=0)
        # Draw border
        self.canvas.create_rectangle(0, 0, self.width, self.height, outline="#555", width=1)
        # Draw value text
        self.canvas.create_text(self.width-4, self.height//2, anchor="e", fill="#fff", font=("Arial", 10), text=f"{value:.1f}")
