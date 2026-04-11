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
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from .theme import COLORS, FONTS, SPACING


# =============================================================================
# Card — Tarjeta con título y área de contenido
# =============================================================================

class Card(QFrame):
    """
    Contenedor estilizado con borde, fondo blanco y área de contenido.

    Uso:
        card = Card(parent, "Archivos de Entrada")
        label = QLabel("Archivo:", card.content())
        card.content().layout().addWidget(label)
    """

    def __init__(self, parent: QWidget = None, title: str = ""):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['bg_white']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['lg']
        )
        self._layout.setSpacing(SPACING['sm'])

        if title:
            header = QLabel(title.upper())
            header.setObjectName("SectionLabel")
            header.setStyleSheet(
                f"border: none; background: transparent; "
                f"color: {COLORS['text_secondary']}; "
                f"font-size: {FONTS['size_small']}pt; font-weight: bold;"
            )
            self._layout.addWidget(header)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"border: none; background-color: {COLORS['border']}; max-height: 1px;")
            self._layout.addWidget(sep)

        self._content = QWidget()
        self._content.setStyleSheet("border: none; background: transparent;")
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
# FileSelector — Selector de archivo con label e indicador de estado
# =============================================================================

class FileSelector(QWidget):
    """
    Widget para la selección de un archivo mediante diálogo.

    Señales:
        fileSelected(str): Emitida cuando el usuario selecciona un archivo.
    """

    fileSelected = Signal(str)

    def __init__(self, label: str, parent: QWidget = None,
                 file_filter: str = "Archivos LandXML (*.xml);;Todos (*.*)"):
        super().__init__(parent)
        self._filter = file_filter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['xs'])

        # Label descriptivo
        self._label = QLabel(label)
        self._label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_small']}pt; border: none;"
        )
        layout.addWidget(self._label)

        # Fila: indicador + entrada + botón
        row = QWidget()
        row.setStyleSheet("border: none; background: transparent;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(SPACING['xs'])

        self._indicator = QLabel("○")
        self._indicator.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 14pt; border: none;"
        )
        self._indicator.setFixedWidth(20)
        row_layout.addWidget(self._indicator)

        self._entry = QLineEdit()
        self._entry.setReadOnly(True)
        self._entry.setPlaceholderText("Sin archivo seleccionado...")
        row_layout.addWidget(self._entry)

        self._btn = QPushButton("Examinar")
        self._btn.setFixedWidth(90)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['primary']}; color: white; "
            f"border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: {FONTS['size_small']}pt; }}"
            f"QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}"
        )
        self._btn.clicked.connect(self._browse)
        row_layout.addWidget(self._btn)

        layout.addWidget(row)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, f"Seleccionar {self._label.text()}", "", self._filter)
        if path:
            self.set_path(path)
            self.fileSelected.emit(path)

    def set_path(self, path: str):
        """Establece la ruta en el campo de texto y actualiza el indicador."""
        self._entry.setText(os.path.normpath(path))
        self._indicator.setText("●")
        self._indicator.setStyleSheet(
            f"color: {COLORS['success']}; font-size: 14pt; border: none;"
        )

    def get_path(self) -> str:
        """Retorna la ruta actualmente seleccionada."""
        return self._entry.text()

    def clear(self):
        """Limpia la ruta y reinicia el indicador."""
        self._entry.clear()
        self._indicator.setText("○")
        self._indicator.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 14pt; border: none;"
        )


# =============================================================================
# DropZone — Área de Drag & Drop para archivos LandXML
# =============================================================================

class DropZone(QFrame):
    """
    Zona de Drag & Drop para archivos LandXML (.xml).

    Acepta ficheros sueltos o directorios (escanea .xml en 1 nivel).
    Limita la lista a 2 archivos y avisa si hay más.

    Señales:
        filesDropped(list[str]): Lista de rutas absolutas aceptadas.
    """

    filesDropped = Signal(list)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._set_hover(False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(SPACING['xs'])

        self._icon = QLabel("📂")
        self._icon.setStyleSheet("font-size: 40px; border: none; background: transparent;")
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)

        self._title = QLabel("Arrastra aquí los 2 archivos LandXML (.xml)")
        self._title.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_body']}pt; "
            f"border: none; background: transparent;"
        )
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        self._subtitle = QLabel("O haz clic para seleccionar archivos")
        self._subtitle.setStyleSheet(
            f"color: {COLORS['primary']}; font-size: {FONTS['size_small']}pt; "
            f"border: none; background: transparent;"
        )
        self._subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._subtitle)

    # --- Estilos dinámicos ---

    def _set_hover(self, active: bool):
        if active:
            self.setStyleSheet(
                f"QFrame#DropZone {{ background-color: {COLORS['primary_light']}; "
                f"border: 2px dashed {COLORS['primary']}; border-radius: 12px; }}"
            )
        else:
            self.setStyleSheet(
                f"QFrame#DropZone {{ background-color: {COLORS['bg_white']}; "
                f"border: 2px dashed {COLORS['border']}; border-radius: 12px; }}"
            )

    # --- Eventos de Drag & Drop ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self._set_hover(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_hover(False)

    def dropEvent(self, event: QDropEvent):
        self._set_hover(False)
        files = self._extract_xml_files(event.mimeData().urls())
        if files:
            self.filesDropped.emit(files)

    def mousePressEvent(self, event):
        """Abre el diálogo al hacer clic directamente en la zona."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivos LandXML", "", "LandXML Files (*.xml);;All Files (*)"
        )
        if paths:
            self.filesDropped.emit(paths[:2])

    # --- Utilidades ---

    def _extract_xml_files(self, urls) -> list:
        """
        Extrae archivos .xml de la lista de URLs soltadas.
        Si se suelta un directorio, escanea su contenido en 1 nivel.
        """
        result = []
        for url in urls:
            path = os.path.normpath(url.toLocalFile())
            if os.path.isfile(path) and path.lower().endswith('.xml'):
                result.append(path)
            elif os.path.isdir(path):
                xml_in_dir = sorted([
                    os.path.normpath(os.path.join(path, f))
                    for f in os.listdir(path) if f.lower().endswith('.xml')
                ])
                result.extend(xml_in_dir[:2])
        return result[:2]
