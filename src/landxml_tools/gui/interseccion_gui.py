"""
Interfaz gráfica de la herramienta de Intersección 3D de LandXML (PySide6).

Características:
  - Zona de Drag & Drop para 2 archivos LandXML
  - Configuración de epsilon y ruta de salida DXF
  - EPSG: autodetección con posibilidad de override manual
  - Procesamiento en hilo separado (QThread + Signal) — sin redirigir sys.stdout
  - Consola de log en tiempo real con estilo dark
"""

import os
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDoubleSpinBox, QSpinBox, QTextEdit,
    QListWidget, QCheckBox, QFileDialog, QMessageBox,
    QSizePolicy, QFrame, QScrollArea, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QCursor

from .theme import COLORS, FONTS, SPACING
from .widgets import Card, DropZone


# =============================================================================
# Worker (hilo de procesamiento)
# =============================================================================

class _Worker(QObject):
    """Ejecuta el motor de intersección en un hilo separado."""

    log    = Signal(str)      # Línea de texto para la consola
    done   = Signal(dict)     # Resumen al finalizar
    error  = Signal(str)      # Mensaje de error

    def __init__(self, file_a: str, file_b: str, output: str, epsilon: float):
        super().__init__()
        self._file_a  = file_a
        self._file_b  = file_b
        self._output  = output
        self._epsilon = epsilon

    def run(self):
        try:
            from ..processing.intersection import resolver_interseccion
            res = resolver_interseccion(
                self._file_a, self._file_b, self._output, self._epsilon,
                log_fn=lambda msg: self.log.emit(msg)
            )
            self.done.emit(res)
        except Exception as exc:
            import traceback
            self.error.emit(traceback.format_exc())


# =============================================================================
# GUI principal de la pestaña de Intersección
# =============================================================================

class LandXMLIntersectionGUI(QWidget):
    """
    Widget (pestaña) para la herramienta de Intersección 3D de LandXML.

    Diseñada para integrarse en QTabWidget de la suite, hereda de QWidget.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        from ..config import get_section
        cfg = get_section('interseccion')

        self._loaded_files: list[str] = []
        self._cfg = cfg

        self._build_ui()

    # -------------------------------------------------------------------------
    # Construcción de la UI
    # -------------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        root.setSpacing(SPACING['md'])

        # Scroll area para acomodar el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(SPACING['md'])
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Archivos fuente ---
        card_files = Card(self, "Archivos de Entrada")
        files_layout = card_files.content_layout()

        self._drop_zone = DropZone()
        self._drop_zone.filesDropped.connect(self._on_files_dropped)
        files_layout.addWidget(self._drop_zone)

        # Lista de archivos cargados
        self._file_list = QListWidget()
        self._file_list.setMaximumHeight(80)
        self._file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._file_list.customContextMenuRequested.connect(self._show_ctx_menu)
        files_layout.addWidget(self._file_list)

        layout.addWidget(card_files)

        # --- Configuración ---
        card_cfg = Card(self, "Configuración")
        cfg_layout = card_cfg.content_layout()

        # Ruta de salida
        out_row = QWidget()
        out_row.setStyleSheet("background: transparent; border: none;")
        out_hl = QHBoxLayout(out_row)
        out_hl.setContentsMargins(0, 0, 0, 0)
        out_hl.addWidget(QLabel("Salida DXF:"))
        self._out_path = QLineEdit()
        self._out_path.setPlaceholderText("Ruta del archivo DXF de salida...")
        out_hl.addWidget(self._out_path)
        btn_browse = QPushButton("Browse")
        btn_browse.setFixedWidth(80)
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._select_output)
        out_hl.addWidget(btn_browse)
        cfg_layout.addWidget(out_row)

        # Epsilon + EPSG
        params_row = QWidget()
        params_row.setStyleSheet("background: transparent; border: none;")
        params_hl = QHBoxLayout(params_row)
        params_hl.setContentsMargins(0, 0, 0, 0)
        params_hl.setSpacing(SPACING['lg'])

        # Epsilon
        eps_col = QVBoxLayout()
        eps_col.addWidget(QLabel("Epsilon (tolerancia):"))
        self._eps_spin = QDoubleSpinBox()
        self._eps_spin.setRange(0.0001, 1.0)
        self._eps_spin.setSingleStep(0.001)
        self._eps_spin.setDecimals(4)
        self._eps_spin.setValue(self._cfg.get('epsilon', 0.001))
        eps_col.addWidget(self._eps_spin)
        params_hl.addLayout(eps_col)

        # EPSG
        epsg_col = QVBoxLayout()
        self._epsg_auto = QCheckBox("Autodetectar EPSG")
        self._epsg_auto.setChecked(self._cfg.get('epsg_autodetect', True))
        self._epsg_auto.stateChanged.connect(self._toggle_epsg)
        epsg_col.addWidget(self._epsg_auto)
        self._epsg_spin = QSpinBox()
        self._epsg_spin.setRange(1024, 99999)
        self._epsg_spin.setValue(self._cfg.get('epsg', 25830))
        self._epsg_spin.setEnabled(not self._epsg_auto.isChecked())
        epsg_col.addWidget(self._epsg_spin)
        params_hl.addLayout(epsg_col)

        params_hl.addStretch()
        cfg_layout.addWidget(params_row)

        layout.addWidget(card_cfg)

        # --- Botón ejecutar ---
        self._btn_run = QPushButton("▶  Ejecutar Intersección")
        self._btn_run.setObjectName("PrimaryButton")
        self._btn_run.setEnabled(False)
        self._btn_run.setCursor(Qt.PointingHandCursor)
        self._btn_run.clicked.connect(self._run)
        layout.addWidget(self._btn_run)

        # --- Consola de log ---
        card_log = Card(self, "Console Log")
        log_layout = card_log.content_layout()
        self._console = QTextEdit()
        self._console.setObjectName("ConsoleLog")
        self._console.setReadOnly(True)
        self._console.setMinimumHeight(200)
        log_layout.addWidget(self._console)
        layout.addWidget(card_log)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll)

    # -------------------------------------------------------------------------
    # Handlers de archivos
    # -------------------------------------------------------------------------

    def _on_files_dropped(self, files: list):
        """Gestiona los archivos soltados o seleccionados en la DropZone."""
        self._loaded_files.extend(files)
        if len(self._loaded_files) > 2:
            QMessageBox.warning(self, "Aviso", "Solo se aceptan 2 archivos. Se usarán los dos primeros.")
            self._loaded_files = self._loaded_files[:2]

        self._file_list.clear()
        for f in self._loaded_files:
            self._file_list.addItem(os.path.basename(f))

        # Sugerir ruta de salida
        if self._loaded_files:
            base = os.path.splitext(self._loaded_files[-1])[0]
            if not self._out_path.text():
                self._out_path.setText(f"{base}_interseccion.dxf")

        self._update_run_btn()

    def _show_ctx_menu(self, pos):
        menu = QMenu(self)
        remove_act = menu.addAction("Eliminar archivo")
        remove_act.triggered.connect(self._remove_selected)
        menu.exec(self._file_list.mapToGlobal(pos))

    def _remove_selected(self):
        rows = sorted([self._file_list.row(i) for i in self._file_list.selectedItems()], reverse=True)
        for r in rows:
            self._file_list.takeItem(r)
            self._loaded_files.pop(r)
        self._update_run_btn()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self._file_list.hasFocus():
            self._remove_selected()
        else:
            super().keyPressEvent(event)

    # -------------------------------------------------------------------------
    # Handlers de configuración
    # -------------------------------------------------------------------------

    def _select_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar DXF", self._out_path.text(), "DXF Files (*.dxf)"
        )
        if path:
            self._out_path.setText(os.path.normpath(path))

    def _toggle_epsg(self, state):
        self._epsg_spin.setEnabled(not self._epsg_auto.isChecked())

    def _update_run_btn(self):
        ready = len(self._loaded_files) == 2 and bool(self._out_path.text().strip())
        self._btn_run.setEnabled(ready)

    # -------------------------------------------------------------------------
    # Ejecución en hilo
    # -------------------------------------------------------------------------

    def _run(self):
        if len(self._loaded_files) < 2:
            QMessageBox.critical(self, "Error", "Se necesitan exactamente 2 archivos LandXML.")
            return
        output = self._out_path.text().strip()
        if not output:
            QMessageBox.critical(self, "Error", "Debe especificar una ruta de salida.")
            return

        self._btn_run.setEnabled(False)
        self._console.clear()
        self._log("Iniciando proceso...\n")

        self._thread = QThread()
        self._worker = _Worker(
            self._loaded_files[0], self._loaded_files[1],
            output, self._eps_spin.value()
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _log(self, text: str):
        """Añade texto a la consola de forma segura desde cualquier hilo."""
        self._console.moveCursor(self._console.textCursor().End)
        self._console.insertPlainText(text + "\n")
        self._console.ensureCursorVisible()

    def _on_done(self, resumen: dict):
        self._btn_run.setEnabled(True)
        QMessageBox.information(
            self, "Éxito",
            f"Proceso completado.\n"
            f"Polilíneas generadas: {resumen['polilineas']}\n"
            f"Archivo: {resumen['output']}"
        )

    def _on_error(self, msg: str):
        self._btn_run.setEnabled(True)
        self._log(f"\n[ERROR]\n{msg}")
        QMessageBox.critical(self, "Error crítico", f"Ocurrió un error durante el cálculo:\n\n{msg[:400]}")
