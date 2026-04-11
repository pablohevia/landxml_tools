"""
LANDXML TOOLS SUITE — PySide6
==============================

Suite unificada de herramientas LandXML.

Pestañas disponibles:
  1. Visualizador   — Genera imágenes rasterizadas a partir de TIN LandXML
  2. Comparador     — Compara dos superficies y genera mapas de diferencia
  3. Intersección   — Calcula curvas de intersección 3D entre dos superficies

Uso:
    conda activate geo_interp
    python landxml_suite.py
"""

import sys
import os

# --- Path setup ---
_dir = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_dir, 'src')
_apps = os.path.join(_dir, 'apps')
for _p in (_src, _apps):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PySide6.QtCore import Qt


def _load_gui_modules():
    """Importa los módulos GUI y lanza un error informativo si falta alguno."""
    try:
        from landxml_tools.gui.theme import get_stylesheet
        from landxml_tools.gui.visualizador_gui import LandXMLVisualizadorGUI
        from landxml_tools.gui.comparador_gui import LandXMLComparadorGUI
        from landxml_tools.gui.interseccion_gui import LandXMLIntersectionGUI
        return get_stylesheet, LandXMLVisualizadorGUI, LandXMLComparadorGUI, LandXMLIntersectionGUI
    except ImportError as exc:
        # Mostrar error con QApplication mínima si aún no hay una activa
        _app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None, "Error de Dependencia",
            f"No se pudieron cargar los módulos requeridos.\n\nDetalle: {exc}\n\n"
            "Asegúrate de que el entorno 'geo_interp' está activo y el paquete está instalado."
        )
        sys.exit(1)


class LandXMLSuite(QMainWindow):
    """
    Suite principal de LandXML Tools.

    Organiza las herramientas en un QTabWidget.
    """

    def __init__(self,
                 visualizador_cls,
                 comparador_cls,
                 interseccion_cls):
        super().__init__()
        self.setWindowTitle("LandXML Tools")
        self.resize(680, 860)
        self._center()

        tabs = QTabWidget()
        tabs.setDocumentMode(False)

        # Pestaña 1: Visualizador
        self._vis = visualizador_cls()
        tabs.addTab(self._vis, "🗺  Visualizador")

        # Pestaña 2: Comparador
        self._cmp = comparador_cls()
        tabs.addTab(self._cmp, "📊  Comparador")

        # Pestaña 3: Intersección
        self._isec = interseccion_cls()
        tabs.addTab(self._isec, "🔀  Intersección 3D")

        self.setCentralWidget(tabs)

    def _center(self):
        """Centra la ventana en la pantalla principal."""
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(screen.center())
        self.move(geo.topLeft())


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling if hasattr(Qt, 'AA_EnableHighDpiScaling') else Qt.ApplicationAttribute(0))

    get_stylesheet, VisualizadorGUI, ComparadorGUI, InterseccionGUI = _load_gui_modules()

    # Aplicar stylesheet global
    app.setStyleSheet(get_stylesheet())

    window = LandXMLSuite(VisualizadorGUI, ComparadorGUI, InterseccionGUI)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
