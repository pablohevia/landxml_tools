"""
LANDXML TOOLS
=============

Aplicación unificada para herramientas LandXML.

Uso:
    conda activate geo_interp
    python landxml_suite.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Configurar paths para importar los módulos
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_path = os.path.abspath(os.path.join(_current_dir, 'src'))
_apps_path = os.path.abspath(os.path.join(_current_dir, 'apps'))

# Añadir paths al sistema
for path in [_src_path, _apps_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from landxml_tools.gui.theme import COLORS, FONTS
    from landxml_tools.gui.apps import LandXMLImageGUI, LandXMLDiffGUI
except ImportError as e:
    messagebox.showerror("Error de Dependencia", 
        f"No se pudo cargar los módulos requeridos.\n\nDetalle: {e}")
    sys.exit(1)


class LandXMLSuite:
    """
    Suite unificada que contiene todas las herramientas LandXML en pestañas.
    
    Incluye:
    - Visualizador: Genera imágenes a partir de superficies LandXML
    - Comparador: Compara dos superficies y genera mapas de diferencia
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("LandXML Tools")
        self.root.geometry("600x820")
        self.root.configure(bg=COLORS['bg_light'])
        
        # Configurar estilo del Notebook
        self._configure_styles()
        
        # Contenedor principal
        main_container = tk.Frame(root, bg=COLORS['bg_light'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Notebook con pestañas
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña 1: Visualizador
        self.tab1 = tk.Frame(self.notebook, bg=COLORS['bg_light'])
        self.notebook.add(self.tab1, text="Visualizador")
        self.app1 = LandXMLImageGUI(self.tab1)
        
        # Pestaña 2: Comparador
        self.tab2 = tk.Frame(self.notebook, bg=COLORS['bg_light'])
        self.notebook.add(self.tab2, text="Comparador")
        self.app2 = LandXMLDiffGUI(self.tab2)
        
        # Centrar ventana
        self._center_window()
    
    def _configure_styles(self):
        """Configura los estilos de ttk para el Notebook."""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TNotebook', background=COLORS['bg_light'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=COLORS['bg_white'], 
                       foreground=COLORS['text_secondary'],
                       padding=[20, 10], 
                       font=FONTS['body'], 
                       width=20, 
                       anchor='center')
        style.map('TNotebook.Tab', 
                 background=[('selected', COLORS['primary'])],
                 foreground=[('selected', 'white')],
                 expand=[('selected', [0, 0, 0, 0])],
                 padding=[('selected', [20, 10])])

    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')


if __name__ == "__main__":
    root = tk.Tk()
    
    # Configurar icono
    try:
        icon_path = os.path.join(_src_path, 'terrain.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass
        
    app = LandXMLSuite(root)
    root.mainloop()
