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

    def set_color(self, color):
        """Change the bar color"""
        self.bar_color = color
        self._draw_bar(self.value)

    def _draw_bar(self, value):
        self.canvas.delete("all")
        if self.max_value == 0:
            fill_width = 0
        else:
            fill_width = int(self.width * value / self.max_value)
        
        # Draw background
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#333", outline="#555", width=1)
        
        # Draw filled bar
        if fill_width > 0:
            self.canvas.create_rectangle(1, 1, fill_width-1, self.height-1, fill=self.bar_color, width=0)


class MiniLineGraph(ctk.CTkFrame):
    """Tiny rolling line graph widget for cumulative trend display."""
    def __init__(self, master, width=80, height=12, max_value=100, line_color="#3B8ED0", bg_color="#222", **kwargs):
        super().__init__(master, fg_color=bg_color, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self.max_value = max_value
        self.line_color = line_color
        self.canvas = ctk.CTkCanvas(self, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.history = []
        self.max_points = width  # one point per pixel approx

    def add_value(self, value, max_value=None):
        if max_value is not None:
            self.max_value = max_value
        value = max(0, min(value, self.max_value))
        self.history.append(value)
        if len(self.history) > self.max_points:
            self.history.pop(0)
        self._draw()

    def set_color(self, color):
        self.line_color = color
        self._draw()

    def _draw(self, *args, **kwargs):
        no_color_updates = kwargs.get('no_color_updates', False)
        if not hasattr(self, 'canvas'):
            return
        self.canvas.delete("all")
        if len(self.history) < 2 or self.max_value == 0:
            return
        scale_y = self.height / self.max_value
        step_x = self.width / (self.max_points - 1)
        for i in range(len(self.history) - 1):
            x1 = i * step_x
            y1 = self.height - self.history[i] * scale_y
            x2 = (i + 1) * step_x
            y2 = self.height - self.history[i + 1] * scale_y
            self.canvas.create_line(x1, y1, x2, y2, fill=self.line_color, width=1)
