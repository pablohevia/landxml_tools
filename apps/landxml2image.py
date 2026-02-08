"""
VISUALIZADOR DE SUPERFICIE LANDXML
===================================

Este script lanza la interfaz del visualizador de superficies LandXML.
"""

import sys
import os
import tkinter as tk

# Configurar path para importar landxml_tools
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_path = os.path.abspath(os.path.join(_current_dir, '..', 'src'))
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

try:
    from landxml_tools.gui.apps import LandXMLImageGUI
except ImportError as e:
    print(f"Error crítico: No se puede importar 'landxml_tools': {e}")
    sys.exit(1)

def main():
    root = tk.Tk()
    app = LandXMLImageGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
