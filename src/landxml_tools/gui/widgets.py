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
            SPACING['md'], SPACING['xs'], SPACING['md'], SPACING['sm']
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
        self._content.setObjectName("CardContent")
        self._content.setStyleSheet("#CardContent { border: none; background: transparent; }")
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
        row.setObjectName("FileSelectorRow")
        row.setStyleSheet("#FileSelectorRow { border: none; background: transparent; }")
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


# =============================================================================
# FileDropBox — selector de archivos unificado con Drag & Drop
# =============================================================================

class FileDropBox(QFrame):
    """
    Widget unificado para selección de archivos con Drag & Drop integrado.

    Combina la simplicidad del FileSelector con el Drag & Drop del DropZone.
    Acepta un archivo (mode='single') o dos archivos (mode='multi').
    Muestra estados visuales con borde dashed que cambia según la interacción.

    Estados visuales:
        - default: borde dashed gris (#cccccc), fondo blanco
        - hover: borde dashed azul (#0078d4), fondo azulado (#f0f7ff)
        - drag-over: borde dashed azul (#0078d4), fondo azul claro prominente
        - file-loaded: borde dashed verde (#107c10), fondo muy claro verde

    Señales:
        - fileSelected(str): Emitida cuando se selecciona 1 archivo (modo single).
        - filesSelected(list[str]): Emitida cuando se seleccionan archivos (modo multi).
    """

    # Señales para los dos modos
    fileSelected = Signal(str)
    filesSelected = Signal(list)

    # Estados internos
    _STATE_DEFAULT = "default"
    _STATE_HOVER = "hover"
    _STATE_DRAG = "drag"
    _STATE_LOADED = "loaded"

    def __init__(self, mode: str = "single", parent: QWidget = None):
        """
        Args:
            mode: 'single' para 1 archivo, 'multi' para 2 archivos.
            parent: Widget padre opcional.
        """
        super().__init__(parent)
        self._mode = mode
        self._state = self._STATE_DEFAULT
        self._files = []

        # Configuración del widget
        self.setObjectName("FileDropBox")
        self.setAcceptDrops(True)
        self.setMinimumHeight(90) # Reducido de 120
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        # Layout interno centrado
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setSpacing(SPACING['xs'])

        # Icono central
        self._icon = QLabel("📁")
        self._icon.setStyleSheet(
            "font-size: 24px; border: none; background: transparent;"
        )
        self._icon.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._icon)

        # Título descriptivo (cambia según modo)
        if mode == "single":
            title_text = "Seleccionar archivo LandXML (.xml)"
        else:
            title_text = "Seleccionar 2 archivos LandXML (.xml)"
        self._title = QLabel(title_text)
        self._title.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_body']}pt; "
            f"border: none; background: transparent;"
        )
        self._title.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._title)

        # Subtítulo instructivo
        self._subtitle = QLabel("Haz clic o arrastra archivos")
        self._subtitle.setStyleSheet(
            f"color: {COLORS['primary']}; font-size: {FONTS['size_small']}pt; "
            f"border: none; background: transparent;"
        )
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._subtitle)

        # Aplicar estilo inicial
        self._update_style()

    # --- Property para el estado (usado en QSS) ---

    def _get_state(self) -> str:
        return self._state

    def _set_state(self, state: str):
        if self._state != state:
            self._state = state
            self._update_style()

    state = Property(str, _get_state, _set_state)

    # --- Métodos públicos ---

    def get_files(self) -> list[str]:
        """Retorna la lista de archivos seleccionados."""
        return self._files.copy()

    def get_file(self) -> str | None:
        """
        Para modo single, retorna el archivo o None.
        En modo multi retorna el primero o None.
        """
        if self._files:
            return self._files[0]
        return None

    def clear(self):
        """Limpia la selección de archivos y reinicia el estado."""
        self._files.clear()
        self._state = self._STATE_DEFAULT
        self._update_style()

    # --- Estilos dinámicos ---

    def _update_style(self):
        """Actualiza el estilo según el estado actual."""
        states = {
            self._STATE_DEFAULT: (
                f"background-color: {COLORS['bg_white']}; "
                f"border: 2px dashed {COLORS['border']}; border-radius: 12px;"
            ),
            self._STATE_HOVER: (
                f"background-color: #f0f7ff; "
                f"border: 2px dashed {COLORS['primary']}; border-radius: 12px;"
            ),
            self._STATE_DRAG: (
                f"background-color: #e6f2ff; "
                f"border: 3px dashed {COLORS['primary']}; border-radius: 12px;"
            ),
            self._STATE_LOADED: (
                f"background-color: #e8f5e9; "
                f"border: 2px dashed {COLORS['success']}; border-radius: 12px;"
            ),
        }
        self.setStyleSheet(f"QFrame#FileDropBox {{ {states[self._state]} }}")

    def _set_hover_state(self, active: bool):
        """Activa o desactiva el estado hover."""
        if self._files:
            return  # Ya tiene archivos cargados
        self._state = self._STATE_HOVER if active else self._STATE_DEFAULT
        self._update_style()

    # --- Eventos de Drag & Drop ---

    def enterEvent(self, event: QEnterEvent):
        """Evento cuando el mouse entra al widget."""
        if not self._files:
            self._set_hover_state(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Evento cuando el mouse sale del widget."""
        if not self._files:
            self._state = self._STATE_DEFAULT
            self._update_style()
        super().leaveEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Evento cuando se arrastan archivos sobre el widget."""
        if event.mimeData().hasUrls():
            event.accept()
            self._state = self._STATE_DRAG
            self._update_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Evento cuando se sale de la zona de drop."""
        if self._files:
            self._state = self._STATE_LOADED
        else:
            self._state = self._STATE_DEFAULT
        self._update_style()

    def dropEvent(self, event: QDropEvent):
        """Evento cuando se sueltan archivos."""
        files = self._extract_files(event.mimeData().urls())
        if files:
            self._set_files(files)
            if self._mode == "single":
                self.fileSelected.emit(files[0])
            else:
                self.filesSelected.emit(files)
        else:
            # Sin archivos válidos, volver al estado default
            self._state = self._STATE_DEFAULT
        self._update_style()

    def mousePressEvent(self, event):
        """Abre el diálogo de selección al hacer clic."""
        if self._mode == "single":
            path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo LandXML", "",
                "LandXML Files (*.xml);;All Files (*)"
            )
            if path:
                self._set_files([path])
                self.fileSelected.emit(path)
        else:
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Seleccionar archivos LandXML", "",
                "LandXML Files (*.xml);;All Files (*)"
            )
            if paths:
                self._set_files(paths[:2])
                self.filesSelected.emit(self._files.copy())
        super().mousePressEvent(event)

    # --- Utilidades internas ---

    def _set_files(self, files: list):
        """Establece los archivos y cambia al estado loaded."""
        self._files = files[:2] if self._mode == "multi" else [files[0]]
        self._state = self._STATE_LOADED
        self._update_style()
        self._update_labels()

    def _update_labels(self):
        """Actualiza los labels según los archivos cargados."""
        if self._files:
            self._subtitle.setText(
                os.path.basename(self._files[0])
                if len(self._files) == 1
                else f"{len(self._files)} archivos"
            )
            self._subtitle.setStyleSheet(
                f"color: {COLORS['success']}; font-size: {FONTS['size_small']}pt; "
                f"border: none; background: transparent;"
            )
        else:
            self._subtitle.setText("Haz clic o arrastra archivos")
            self._subtitle.setStyleSheet(
                f"color: {COLORS['primary']}; font-size: {FONTS['size_small']}pt; "
                f"border: none; background: transparent;"
            )

    def _extract_files(self, urls) -> list:
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
                result.extend(xml_in_dir)

        # Limitar según el modo
        if self._mode == "single":
            return result[:1]
        return result[:2]
