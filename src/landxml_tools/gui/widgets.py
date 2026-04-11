"""
Widgets personalizados para LandXML Tools (PySide6).

Proporciona componentes reutilizables que siguen el sistema de diseño
definido en theme.py: paleta Fluent/Azure claro con soporte nativo para
Drag & Drop y manejo de archivos.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QSizePolicy, QFileDialog,
    QListWidget
)
from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QEnterEvent

from .theme import COLORS, FONTS, SPACING


# =============================================================================
# Card — Tarjeta con título y área de contenido
# =============================================================================

class Card(QFrame):
    """
    Contenedor estilizado con borde, fondo blanco y área de contenido.
    """

    def __init__(self, parent: QWidget = None, title: str = ""):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            SPACING['md'], SPACING['xs'], SPACING['md'], SPACING['sm']
        )
        self._layout.setSpacing(SPACING['sm'])

        if title:
            header = QLabel(title.upper())
            header.setObjectName("SectionLabel")
            self._layout.addWidget(header)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            self._layout.addWidget(sep)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(SPACING['sm'])
        self._layout.addWidget(self._content)

    def content(self) -> QWidget:
        """Retorna el widget de contenido donde se añaden los controles hijos."""
        return self._content

    def content_layout(self) -> QVBoxLayout:
        """Retorna el layout del área de contenido."""
        return self._content_layout


# =============================================================================
# FileDropBox — Selector de archivos unificado con Drag & Drop
# =============================================================================

class FileDropBox(QFrame):
    """
    Widget unificado para selección de archivos con Drag & Drop integrado.

    Acepta un archivo (mode='single') o dos archivos (mode='multi').
    Muestra estados visuales mediante la propiedad 'state' que es manejada por el QSS.
    """

    fileSelected = Signal(str)
    filesSelected = Signal(list)

    # Estados internos coinciden con los del QSS
    _STATE_DEFAULT = "default"
    _STATE_HOVER = "hover"
    _STATE_DRAG = "drag"
    _STATE_LOADED = "loaded"

    def __init__(self, mode: str = "single", parent: QWidget = None):
        super().__init__(parent)
        self._mode = mode
        self._state = self._STATE_DEFAULT
        self._files = []

        # Configuración básica
        self.setProperty("class", "FileDropBox")
        self.setProperty("state", self._state)
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        # Layout
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setSpacing(SPACING['xs'])

        # Componentes
        self._icon = QLabel("📁")
        self._icon.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._icon)

        title_text = "Seleccionar archivo LandXML (.xml)" if mode == "single" else "Seleccionar 2 archivos LandXML (.xml)"
        self._title = QLabel(title_text)
        self._title.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._title)

        self._subtitle = QLabel("Haz clic o arrastra archivos")
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._subtitle)

    # --- Propiedad Dinámica para CSS ---

    def _get_state(self): return self._state
    def _set_state(self, val):
        self._state = val
        self.setProperty("state", val)
        self.style().unpolish(self)
        self.style().polish(self)
    
    state_prop = Property(str, _get_state, _set_state)

    def _update_style(self):
        """Dispara la actualización del estilo basado en la propiedad 'state'."""
        self._set_state(self._state)

    # --- Métodos Públicos ---

    def get_files(self) -> list: return self._files.copy()
    def get_file(self) -> str: return self._files[0] if self._files else None
    
    def clear(self):
        self._files.clear()
        self._state = self._STATE_DEFAULT
        self._update_style()
        self._subtitle.setText("Haz clic o arrastra archivos")

    # --- Eventos ---

    def enterEvent(self, event: QEnterEvent):
        if not self._files:
            self._state = self._STATE_HOVER
            self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._files:
            self._state = self._STATE_DEFAULT
            self._update_style()
        super().leaveEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self._state = self._STATE_DRAG
            self._update_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._state = self._STATE_LOADED if self._files else self._STATE_DEFAULT
        self._update_style()

    def dropEvent(self, event: QDropEvent):
        files = self._extract_files(event.mimeData().urls())
        if files:
            self._files = files
            self._state = self._STATE_LOADED
            self._update_style()
            self._update_subtitle()
            if self._mode == "single":
                self.fileSelected.emit(files[0])
            else:
                self.filesSelected.emit(files)
        else:
            self._state = self._STATE_DEFAULT
            self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._browse()

    def _browse(self):
        if self._mode == "single":
            path, _ = QFileDialog.getOpenFileName(self, "Seleccionar LandXML", "", "LandXML (*.xml)")
            if path:
                self._files = [path]
                self._state = self._STATE_LOADED
                self._update_style()
                self._update_subtitle()
                self.fileSelected.emit(path)
        else:
            paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar LandXML", "", "LandXML (*.xml)")
            if paths:
                self._files = paths[:2]
                self._state = self._STATE_LOADED
                self._update_style()
                self._update_subtitle()
                self.filesSelected.emit(self._files)

    def _update_subtitle(self):
        count = len(self._files)
        text = f"{count} archivo" + ("s" if count > 1 else "")
        self._subtitle.setText(text)

    def _extract_files(self, urls) -> list:
        res = []
        for url in urls:
            path = os.path.normpath(url.toLocalFile())
            if os.path.isfile(path) and path.lower().endswith('.xml'):
                res.append(path)
            elif os.path.isdir(path):
                xmls = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.xml')]
                res.extend(xmls)
        return res[:2] if self._mode == "multi" else res[:1]
