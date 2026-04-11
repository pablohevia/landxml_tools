"""
Interfaz gráfica del Comparador LandXML (PySide6).

Port completo de LandXMLDiffGUI desde Tkinter a QWidget.
Compara dos superficies TIN y genera imágenes de diferencia
(PNG, JPG, GeoTIFF) y una leyenda de color.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDoubleSpinBox, QSpinBox, QComboBox, QSlider,
    QCheckBox, QFileDialog, QMessageBox, QProgressBar,
    QScrollArea, QSizePolicy, QFrame, QAbstractSpinBox,
    QListWidget, QTextEdit, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor

from .theme import COLORS, FONTS, SPACING
from .widgets import Card, FileDropBox
from .visualizador_gui import _HRow   # helper compartido


# =============================================================================
# Worker
# =============================================================================

class _ComparadorWorker(QObject):
    """Hilo de procesamiento para el Comparador."""

    progress = Signal(str, int)
    log      = Signal(str)        # mensaje de log en tiempo real
    done     = Signal(bool, str)

    def __init__(self, params: dict):
        super().__init__()
        self._p = params

    def run(self):
        try:
            from apps.landxml_diff import main as process_diff
            import os

            p = self._p
            self.log.emit(f"> Leyendo {os.path.basename(p['file1'])}...")
            self.progress.emit("Leyendo archivos LandXML...", 10)

            def cb(msg, pct=None):
                self.progress.emit(msg, pct or 0)

            self.log.emit("> Parseando superficies...")
            self.log.emit(f"> Leyendo {os.path.basename(p['file2'])}...")
            self.log.emit("> Calculando diferencias...")
            success, message = process_diff(
                surface_file1=p['file1'],
                surface_file2=p['file2'],
                output_name=p['out_name'],
                resolution=p['resolution'],
                epsg_code=p['epsg'],
                colormap=p['colormap'],
                save_jpg=p['save_jpg'],
                save_png=p['save_png'],
                save_tiff=p['save_tiff'],
                save_legend=p['save_legend'],
                output_dir=p['out_dir'] or None,
                class_interval=p['class_interval'] if p['classify'] else None,
                whitening=p['whitening'] / 100.0,
                progress_callback=cb
            )
            self.log.emit("> Generando imágenes...")
            self.done.emit(success, message)
        except Exception as exc:
            import traceback
            self.log.emit(f"✗ ERROR: {exc}")
            self.done.emit(False, traceback.format_exc())


# =============================================================================
# GUI principal del Comparador
# =============================================================================

class LandXMLComparadorGUI(QWidget):
    """
    Pestaña de comparación de superficies LandXML.

    Hereda de QWidget para integrarse en QTabWidget de la suite.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        from ..config import get_section
        cfg = get_section('comparador')
        self._cfg = cfg
        self._out_dir = ""
        self._build_ui()

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        root.setSpacing(SPACING['sm'])

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(SPACING['md'])
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Archivos ---
        card_files = Card(self, "Archivos de Entrada")
        fl = card_files.content_layout()
        self._file_drop = FileDropBox(mode='multi', parent=self)
        self._file_drop.filesSelected.connect(self._on_files_selected)
        fl.addWidget(self._file_drop)
        
        # Lista de archivos cargados
        self._file_list = QListWidget()
        self._file_list.setMaximumHeight(60)
        self._file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._file_list.customContextMenuRequested.connect(self._show_ctx_menu)
        fl.addWidget(self._file_list)
        
        layout.addWidget(card_files)

        # --- Parámetros ---
        card_params = Card(self, "Parámetros")
        pl = card_params.content_layout()

        row1 = _HRow()
        row1.add(QLabel("Resolución (m):"), fixed_width=130)
        self._res_spin = QDoubleSpinBox()
        self._res_spin.setRange(0.001, 10.0)
        self._res_spin.setDecimals(3)
        self._res_spin.setSingleStep(0.01)
        self._res_spin.setValue(self._cfg.get('resolution', 0.05))
        row1.add(self._res_spin)
        row1.add(QLabel("EPSG:"), fixed_width=50)
        self._epsg_spin = QSpinBox()
        self._epsg_spin.setRange(1024, 99999)
        self._epsg_spin.setValue(self._cfg.get('epsg', 25830))
        self._epsg_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        row1.add(self._epsg_spin)
        row1.addStretch()
        pl.addWidget(row1)

        row_out = _HRow()
        row_out.add(QLabel("Salida:"), fixed_width=130)
        self._out_edit = QLineEdit()
        self._out_edit.setPlaceholderText("Ruta completa del archivo de salida...")
        row_out.add(self._out_edit)
        btn_out = QPushButton("Examinar")
        btn_out.setObjectName("BrowseButton")
        btn_out.setFixedWidth(90)
        btn_out.setCursor(Qt.PointingHandCursor)
        btn_out.clicked.connect(self._select_output)
        row_out.add(btn_out)
        pl.addWidget(row_out)

        # Mapa de color
        row_cmap = _HRow()
        row_cmap.add(QLabel("Mapa de color:"), fixed_width=130)
        self._cmap_combo = QComboBox()
        self._cmap_combo.addItems([
            'coolwarm_r', 'coolwarm', 'RdBu_r', 'RdBu', 'seismic', 'bwr',
            'RdYlGn_r', 'terrain', 'gist_earth', 'viridis', 'plasma', 'inferno', 'magma'
        ])
        self._cmap_combo.setCurrentText(self._cfg.get('colormap', 'coolwarm_r'))
        self._cmap_combo.currentTextChanged.connect(self._update_preview)
        row_cmap.add(self._cmap_combo)
        self._preview_lbl = QLabel()
        self._preview_lbl.setFixedSize(160, 22)
        row_cmap.add(self._preview_lbl)
        row_cmap.addStretch()
        pl.addWidget(row_cmap)

        # Blanqueamiento
        pl.addWidget(self._make_slider_row("Blanqueamiento (%):",
                                           '_whitening', self._cfg.get('whitening', 0)))
        layout.addWidget(card_params)

        # --- Opciones de salida ---
        card_out = Card(self, "Opciones de Salida")
        ol = card_out.content_layout()

        fmt_row = _HRow()
        self._chk_png  = QCheckBox("PNG (transparencia)"); self._chk_png.setChecked(self._cfg.get('save_png', True))
        self._chk_jpg  = QCheckBox("JPG");                 self._chk_jpg.setChecked(self._cfg.get('save_jpg', True))
        self._chk_tiff = QCheckBox("GeoTIFF");             self._chk_tiff.setChecked(self._cfg.get('save_tiff', True))
        self._chk_leg  = QCheckBox("Leyenda");             self._chk_leg.setChecked(self._cfg.get('save_legend', True))
        for chk in (self._chk_png, self._chk_jpg, self._chk_tiff, self._chk_leg):
            fmt_row.add(chk)
        fmt_row.addStretch()
        ol.addWidget(fmt_row)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        ol.addWidget(sep)

        class_row = _HRow()
        self._chk_class = QCheckBox("Clasificar elevaciones")
        self._chk_class.setChecked(self._cfg.get('classify', True))
        class_row.add(self._chk_class)
        class_row.add(QLabel("Intervalo:"))
        self._interval_spin = QDoubleSpinBox()
        self._interval_spin.setRange(0.01, 100.0)
        self._interval_spin.setDecimals(2)
        self._interval_spin.setValue(self._cfg.get('class_interval', 0.25))
        self._interval_spin.setFixedWidth(80)
        class_row.add(self._interval_spin)
        class_row.add(QLabel("m"))
        class_row.addStretch()
        ol.addWidget(class_row)
        layout.addWidget(card_out)

        # --- Botón ---
        self._btn_run = QPushButton("▶  Procesar Diferencia")
        self._btn_run.setObjectName("PrimaryButton")
        self._btn_run.setEnabled(False)
        self._btn_run.setCursor(Qt.PointingHandCursor)
        self._btn_run.clicked.connect(self._run)
        layout.addWidget(self._btn_run)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # --- Log de proceso ---
        card_log = Card(self, "LOG DE PROCESO")
        log_layout = card_log.content_layout()
        self._console = QTextEdit()
        self._console.setObjectName("ConsoleLog")
        self._console.setReadOnly(True)
        self._console.setMinimumHeight(100)
        log_layout.addWidget(self._console)
        card_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(card_log)


        scroll.setWidget(container)
        root.addWidget(scroll)

        self._update_preview()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _make_slider_row(self, label_text: str, attr_name: str, initial: int) -> QWidget:
        row = _HRow()
        row.add(QLabel(label_text), fixed_width=170)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(initial)
        spinbox = QSpinBox()
        spinbox.setRange(0, 100)
        spinbox.setValue(initial)
        spinbox.setFixedWidth(60)
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(lambda _: self._update_preview())
        row.add(slider)
        row.add(spinbox)
        setattr(self, f'{attr_name}_slider', slider)
        setattr(self, f'{attr_name}_spin', spinbox)
        return row

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------

    def _on_files_selected(self, files: list):
        """Maneja la selección de archivos desde FileDropBox."""
        if len(files) >= 1:
            basename = os.path.splitext(os.path.basename(files[0]))[0]
            default_path = os.path.join(os.path.dirname(files[0]), f"{basename}_diff")
            self._out_edit.setText(os.path.normpath(default_path))
            # Detectar EPSG desde coordenadas
            detected = self._detect_epsg_from_coordinates(files[0])
            self._epsg_spin.setValue(detected)
        if len(files) >= 2:
            self._check_ready()
        
        # Actualizar la lista de archivos
        self._file_list.clear()
        for f in files:
            self._file_list.addItem(os.path.basename(f))

    def _check_ready(self):
        files = self._file_drop.get_files()
        ready = len(files) >= 2
        self._btn_run.setEnabled(ready)
        if ready:
            self._log("✓ Archivos cargados: Listo para procesar")

    def _select_output(self):
        current = self._out_edit.text()
        default_dir = os.path.dirname(current) if current else ""
        default_name = os.path.basename(current) if current else "diferencia.tif"
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo de salida", 
            os.path.join(default_dir, default_name),
            "GeoTIFF (*.tif);;PNG (*.png);;JPG (*.jpg);;Todos (*.*)"
        )
        if path:
            self._out_edit.setText(os.path.normpath(path))

    def _update_preview(self):
        try:
            import numpy as np
            import matplotlib.pyplot as plt
            cmap = plt.get_cmap(self._cmap_combo.currentText())
            w = self._whitening_slider.value() / 100.0 if hasattr(self, '_whitening_slider') else 0
            px = QPixmap(160, 22)
            px.fill(Qt.white)
            p = QPainter(px)
            grad = QLinearGradient(0, 0, 160, 0)
            for t in np.linspace(0, 1, 20):
                r, g, b, _ = cmap(t)
                r = r * (1 - w) + w
                g = g * (1 - w) + w
                b = b * (1 - w) + w
                grad.setColorAt(t, QColor(int(r*255), int(g*255), int(b*255)))
            p.fillRect(0, 0, 160, 22, grad)
            p.end()
            self._preview_lbl.setPixmap(px)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Ejecución
    # -------------------------------------------------------------------------

    def _run(self):
        files = self._file_drop.get_files()
        f1, f2 = files[0], files[1] if len(files) >= 2 else (None, None)
        if not f1 or not f2:
            QMessageBox.critical(self, "Error", "Seleccione ambos archivos LandXML.")
            return

        out_path = self._out_edit.text().strip()
        if not out_path:
            QMessageBox.critical(self, "Error", "Debe especificar una ruta de salida.")
            return
            
        out_dir = os.path.dirname(out_path)
        out_name = os.path.splitext(os.path.basename(out_path))[0]
        
        params = {
            'file1':         f1,
            'file2':         f2,
            'resolution':    self._res_spin.value(),
            'epsg':          self._epsg_spin.value(),
            'out_name':      out_name,
            'out_dir':       out_dir,
            'colormap':      self._cmap_combo.currentText(),
            'whitening':     self._whitening_slider.value(),
            'save_png':      self._chk_png.isChecked(),
            'save_jpg':      self._chk_jpg.isChecked(),
            'save_tiff':     self._chk_tiff.isChecked(),
            'save_legend':   self._chk_leg.isChecked(),
            'classify':      self._chk_class.isChecked(),
            'class_interval': self._interval_spin.value(),
        }

        self._btn_run.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        self._thread = QThread()
        self._worker = _ComparadorWorker(params)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._log)
        self._worker.done.connect(self._on_done)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_progress(self, msg: str, pct: int):
        self._progress.setValue(pct)
        if pct == 0: self._log(f"[INFO] {msg}")

    def _on_done(self, success: bool, msg: str):
        self._btn_run.setEnabled(True)
        self._progress.setValue(100)
        if success:
            self._log(f"✓ {msg}")
            self._log("✓ PROCESO FINALIZADO CON ÉXITO")
            out = self._out_dir or "(directorio del archivo)"
            QMessageBox.information(self, "Completado",
                                    f"{msg}\n\nArchivos guardados en:\n{out}")
        else:
            self._log(f"✗ ERROR: {msg}")
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n\n{msg[:600]}")
        self._progress.setVisible(False)

    # -------------------------------------------------------------------------
    # Console Log
    # -------------------------------------------------------------------------

    def _log(self, text: str):
        """Escribe un mensaje en la consola de log."""
        self._console.moveCursor(self._console.textCursor().End)
        self._console.insertPlainText(text + "\n")
        self._console.ensureCursorVisible()

    # -------------------------------------------------------------------------
    # Detección EPSG
    # -------------------------------------------------------------------------

    def _detect_epsg_from_coordinates(self, file_path: str) -> int:
        """Detecta CRS aproximado desde las coordenadas del archivo LandXML."""
        try:
            from lxml import etree
            tree = etree.parse(file_path)
            # Buscar coordenadas en Pnts o Surface/Definition/Pnts
            pnts = tree.findall(".//Pnt")
            if not pnts:
                return 25830
            # Tomar primeras 3 coordenadas
            xs, ys = [], []
            for p in pnts[:3]:
                coords = p.text.strip().split()
                if len(coords) >= 2:
                    xs.append(float(coords[0]))
                    ys.append(float(coords[1]))
            if not xs:
                return 25830
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
            # WGS84 geográfico
            if -180 <= x_mean <= 180 and -90 <= y_mean <= 90:
                return 4326
            # UTM 30N (España)
            if 250000 <= x_mean <= 750000 and 4000000 <= y_mean <= 4800000:
                return 25830
            return 25830
        except Exception:
            return 25830

    # -------------------------------------------------------------------------
    # Menú contextual
    # -------------------------------------------------------------------------

    def _show_ctx_menu(self, pos):
        """Muestra el menú contextual para la lista de archivos."""
        menu = QMenu(self)
        remove_act = menu.addAction("Eliminar archivo")
        remove_act.triggered.connect(self._remove_selected)
        menu.exec(self._file_list.mapToGlobal(pos))

    def _remove_selected(self):
        """Elimina los archivos seleccionados de la lista."""
        rows = sorted([self._file_list.row(i) for i in self._file_list.selectedItems()], reverse=True)
        files = self._file_drop.get_files()
        for r in rows:
            if r < len(files):
                files.pop(r)
        self._file_drop._files = files  # Actualizar FileDropBox internamente
        self._file_list.clear()
        for f in files:
            self._file_list.addItem(os.path.basename(f))
        self._check_ready()
