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
    QScrollArea, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor

from .theme import COLORS, FONTS, SPACING
from .widgets import Card, FileSelector
from .visualizador_gui import _HRow   # helper compartido


# =============================================================================
# Worker
# =============================================================================

class _ComparadorWorker(QObject):
    """Hilo de procesamiento para el Comparador."""

    progress = Signal(str, int)
    done     = Signal(bool, str)

    def __init__(self, params: dict):
        super().__init__()
        self._p = params

    def run(self):
        try:
            from apps.landxml_diff import main as process_diff

            p = self._p

            def cb(msg, pct=None):
                self.progress.emit(msg, pct or 0)

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
            self.done.emit(success, message)
        except Exception as exc:
            import traceback
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
        root.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        root.setSpacing(SPACING['md'])

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(SPACING['md'])
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Archivos ---
        card_files = Card(self, "Archivos de Entrada")
        fl = card_files.content_layout()
        self._file1_sel = FileSelector("Superficie Base (1)", parent=self)
        self._file1_sel.fileSelected.connect(lambda _: self._check_ready())
        fl.addWidget(self._file1_sel)
        self._file2_sel = FileSelector("Superficie a Comparar (2)", parent=self)
        self._file2_sel.fileSelected.connect(self._on_file2_selected)
        fl.addWidget(self._file2_sel)
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
        row1.add(self._epsg_spin)
        row1.addStretch()
        pl.addWidget(row1)

        row_name = _HRow()
        row_name.add(QLabel("Nombre salida:"), fixed_width=130)
        self._name_edit = QLineEdit(self._cfg.get('output_name', 'diferencia'))
        row_name.add(self._name_edit)
        pl.addWidget(row_name)

        row_dir = _HRow()
        row_dir.add(QLabel("Directorio salida:"), fixed_width=130)
        self._dir_edit = QLineEdit()
        self._dir_edit.setReadOnly(True)
        self._dir_edit.setPlaceholderText("(mismo que el archivo por defecto)")
        row_dir.add(self._dir_edit)
        btn_dir = QPushButton("Browse")
        btn_dir.setFixedWidth(80)
        btn_dir.setCursor(Qt.PointingHandCursor)
        btn_dir.clicked.connect(self._select_dir)
        row_dir.add(btn_dir)
        pl.addWidget(row_dir)

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
        self._preview_lbl.setStyleSheet("border: 1px solid #cccccc; border-radius: 3px;")
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
        sep.setStyleSheet(f"color: {COLORS['border']};")
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

        self._status = QLabel("Seleccione los archivos para comenzar")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_small']}pt;")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

        layout.addStretch()
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

    def _on_file2_selected(self, path: str):
        if not self._out_dir:
            self._out_dir = os.path.dirname(path)
            self._dir_edit.setText(self._out_dir)
        self._check_ready()

    def _check_ready(self):
        ready = bool(self._file1_sel.get_path()) and bool(self._file2_sel.get_path())
        self._btn_run.setEnabled(ready)
        if ready:
            self._status.setText("✓ Listo para procesar")
            self._status.setStyleSheet(f"color: {COLORS['success']}; font-size: {FONTS['size_small']}pt;")

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Directorio de salida", self._out_dir)
        if d:
            self._out_dir = d
            self._dir_edit.setText(d)

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
        f1 = self._file1_sel.get_path()
        f2 = self._file2_sel.get_path()
        if not f1 or not f2:
            QMessageBox.critical(self, "Error", "Seleccione ambos archivos LandXML.")
            return

        params = {
            'file1':         f1,
            'file2':         f2,
            'resolution':    self._res_spin.value(),
            'epsg':          self._epsg_spin.value(),
            'out_name':      self._name_edit.text().strip() or 'diferencia',
            'out_dir':       self._out_dir,
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
        self._worker.done.connect(self._on_done)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_progress(self, msg: str, pct: int):
        self._status.setText(msg)
        self._status.setStyleSheet(f"color: {COLORS['primary']}; font-size: {FONTS['size_small']}pt;")
        self._progress.setValue(pct)

    def _on_done(self, success: bool, msg: str):
        self._btn_run.setEnabled(True)
        self._progress.setValue(100)
        if success:
            self._status.setText("✓ Proceso completado")
            self._status.setStyleSheet(f"color: {COLORS['success']}; font-size: {FONTS['size_small']}pt;")
            out = self._out_dir or "(directorio del archivo)"
            QMessageBox.information(self, "Completado",
                                    f"{msg}\n\nArchivos guardados en:\n{out}")
        else:
            self._status.setText("✗ Error")
            self._status.setStyleSheet(f"color: {COLORS['danger']}; font-size: {FONTS['size_small']}pt;")
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n\n{msg[:600]}")
        self._progress.setVisible(False)
