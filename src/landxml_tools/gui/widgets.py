"""
Widgets reutilizables para la interfaz gráfica.
"""

import tkinter as tk
from tkinter import filedialog
from .theme import COLORS, FONTS, SPACING

class ToolTip:
    """Tooltip widget que muestra ayuda contextual al pasar el mouse"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.schedule_id = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        self.schedule_id = self.widget.after(500, self._display_tooltip)
    
    def _display_tooltip(self):
        if self.tooltip_window: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, bg="#1e293b", fg="white",
                         relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 8), padx=8, pady=4, wraplength=300)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.schedule_id: self.widget.after_cancel(self.schedule_id)
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class ConfigRow(tk.Frame):
    """Fila de configuración con label y entrada"""
    def __init__(self, parent, label, variable, width=12, **kwargs):
        super().__init__(parent, bg=COLORS['bg_white'], **kwargs)
        tk.Label(self, text=label, font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        entry = tk.Entry(self, textvariable=variable, font=FONTS['body'], width=width, bg=COLORS['input_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, highlightthickness=1, highlightbackground=COLORS['border'], highlightcolor=COLORS['primary'])
        entry.pack(side=tk.LEFT, ipady=3)

class ModernButton(tk.Canvas):
    """Botón moderno con bordes redondeados"""
    
    def __init__(self, parent, text, command, bg_color, fg_color='white', 
                 hover_color=None, width=120, height=36, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=parent.cget('bg'), **kwargs)
        
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color or bg_color
        self.fg_color = fg_color
        self.text = text
        self.current_bg = bg_color
        self._enabled = True
        
        self._draw()
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
    
    def _draw(self):
        self.delete('all')
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        
        # Rectángulo (sin bordes redondeados)
        self.create_rectangle(
            0, 0, w, h,
            fill=self.current_bg, outline='', tags='bg'
        )
        
        # Texto centrado
        self.create_text(w//2, h//2, text=self.text, fill=self.fg_color,
                        font=FONTS['button'], tags='text')
    
    def _on_enter(self, event):
        if self._enabled:
            self.current_bg = self.hover_color
            self._draw()
            self.config(cursor='hand2')
    
    def _on_leave(self, event):
        if self._enabled:
            self.current_bg = self.bg_color
            self._draw()
            self.config(cursor='')
    
    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()
    
    def configure(self, **kwargs):
        if 'state' in kwargs:
            self._enabled = kwargs['state'] != tk.DISABLED
            if not self._enabled:
                self.current_bg = COLORS['text_muted']
            else:
                self.current_bg = self.bg_color
            self._draw()
        if 'bg' in kwargs:
            self.bg_color = kwargs['bg']
            self.current_bg = kwargs['bg']
            self._draw()
        super().configure(**{k: v for k, v in kwargs.items() if k not in ['state', 'bg']})
    
    config = configure


class FileSelector(tk.Frame):
    """Widget para selección de archivos con indicador de estado"""
    
    def __init__(self, parent, label, variable, on_select=None, **kwargs):
        super().__init__(parent, bg=COLORS['bg_white'], **kwargs)
        
        self.variable = variable
        self.on_select = on_select
        
        # Label
        self.label = tk.Label(self, text=label, font=FONTS['body'],
                             bg=COLORS['bg_white'], fg=COLORS['text_secondary'])
        self.label.pack(anchor=tk.W)
        
        # Frame para entry + botón
        row = tk.Frame(self, bg=COLORS['bg_white'])
        row.pack(fill=tk.X, pady=(SPACING['xs'], 0))
        
        # Indicador de estado
        self.status_indicator = tk.Label(row, text="○", font=('Segoe UI', 12),
                                         bg=COLORS['bg_white'], fg=COLORS['text_muted'])
        self.status_indicator.pack(side=tk.LEFT, padx=(0, SPACING['sm']))
        
        # Entry
        self.entry = tk.Entry(row, textvariable=variable, state='readonly',
                             font=FONTS['small'], bg=COLORS['input_bg'],
                             fg=COLORS['text_primary'], relief=tk.FLAT,
                             highlightthickness=1, highlightbackground=COLORS['border'],
                             highlightcolor=COLORS['primary'])
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        
        # Botón
        self.btn = tk.Button(row, text="Examinar", command=self._select_file,
                            font=FONTS['small'], bg=COLORS['primary'],
                            fg='white', relief=tk.FLAT, cursor='hand2',
                            activebackground=COLORS['primary_hover'],
                            activeforeground='white', padx=12, pady=4)
        self.btn.pack(side=tk.RIGHT, padx=(SPACING['sm'], 0))
        
        # Observar cambios
        variable.trace_add('write', self._on_change)
    
    def _select_file(self):
        filename = filedialog.askopenfilename(
            title=f"Seleccionar {self.label.cget('text')}",
            filetypes=[("Archivos LandXML", "*.xml *.XML"), ("Todos", "*.*")]
        )
        if filename:
            self.variable.set(filename)
            if self.on_select:
                self.on_select(filename)
    
    def _on_change(self, *args):
        if self.variable.get():
            self.status_indicator.config(text="●", fg=COLORS['success'])
        else:
            self.status_indicator.config(text="○", fg=COLORS['text_muted'])


class Card(tk.Frame):
    """
    Widget de tarjeta con borde y título para agrupar controles.
    
    Proporciona un contenedor estilizado con un encabezado y un área de contenido.
    El contenido se añade al atributo `content`.
    
    Ejemplo:
        card = Card(parent, "Configuración")
        tk.Label(card.content, text="Opción 1").pack()
    """
    
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, bg=COLORS['bg_white'], bd=0,
                        highlightthickness=1, highlightbackground=COLORS['border'], **kwargs)
        self.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        # Encabezado
        header = tk.Frame(self, bg=COLORS['bg_white'])
        header.pack(fill=tk.X, padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))
        tk.Label(header, text=title, font=FONTS['heading'],
                bg=COLORS['bg_white'], fg=COLORS['text_primary']).pack(anchor='w')
        
        # Área de contenido
        self.content = tk.Frame(self, bg=COLORS['bg_white'])
        self.content.pack(fill=tk.X, padx=SPACING['md'], pady=(0, SPACING['md']))


class StyledCheckbox(tk.Checkbutton):
    """
    Checkbox con estilos del tema de la aplicación.
    
    Aplica automáticamente los colores y fuentes definidos en el tema.
    """
    
    def __init__(self, parent, text, variable, **kwargs):
        super().__init__(
            parent, text=text, variable=variable,
            font=FONTS['body'], bg=COLORS['bg_white'],
            fg=COLORS['text_primary'], activebackground=COLORS['bg_white'],
            selectcolor=COLORS['bg_white'], **kwargs
        )


def center_window(window):
    """
    Centra una ventana Tkinter en la pantalla.
    
    Args:
        window: Ventana Tk o Toplevel a centrar.
    """
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (w // 2)
    y = (window.winfo_screenheight() // 2) - (h // 2)
    window.geometry(f'{w}x{h}+{x}+{y}')

