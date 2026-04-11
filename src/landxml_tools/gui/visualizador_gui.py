"""
Interfaz gráfica del Visualizador LandXML (PySide6).

Port completo de LandXMLImageGUI desde Tkinter a QWidget.
Genera imágenes rasterizadas (PNG, JPG, GeoTIFF) a partir de
superficies TIN en formato LandXML.
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


# =============================================================================
# Worker
# =============================================================================

class _VisualizadorWorker(QObject):
    """Hilo de procesamiento para el Visualizador."""

    progress = Signal(str, int)   # (mensaje, porcentaje)
    done     = Signal(bool, str)  # (éxito, mensaje)

    def __init__(self, params: dict):
        super().__init__()
        self._p = params

    def run(self):
        try:
            from ..io.landxml import parse_landxml_surface
            from ..processing.raster import rasterize_surface_tin
            from ..viz.plotting import create_colormap_legend, save_colored_map
            from ..io.export import save_geotiff, save_world_file

            p = self._p
            self.progress.emit("Leyendo LandXML...", 10)
            points, triangles = parse_landxml_surface(p['xml_file'])

            self.progress.emit("Rasterizando TIN...", 30)
            grid_z, extent = rasterize_surface_tin(points, triangles, resolution=p['resolution'])

            out_dir = p['out_dir']
            out_name = p['out_name']

            if p['save_tiff']:
                self.progress.emit("Guardando GeoTIFF...", 55)
                save_geotiff(grid_z, extent, os.path.join(out_dir, out_name + ".tif"),
                             epsg_code=p['epsg'])

            if p['save_png'] or p['save_jpg']:
                self.progress.emit("Generando imágenes...", 75)
                class_interval = p['class_interval'] if p['classify'] else None
                hillshade_intensity = p['hillshade'] / 100.0
                save_colored_map(
                    grid_z, out_name,
                    colormap=p['colormap'], output_dir=out_dir,
                    class_interval=class_interval,
                    whitening=p['whitening'] / 100.0,
                    save_png=p['save_png'], save_jpg=p['save_jpg'],
                    rotate_90=True,
                    hillshade=(hillshade_intensity > 0),
                    hillshade_intensity=hillshade_intensity,
                    resolution=p['resolution']
                )
                if p['save_png']:
                    save_world_file(extent, grid_z.shape, os.path.join(out_dir, out_name + ".pgw"))
                if p['save_jpg']:
                    save_world_file(extent, grid_z.shape, os.path.join(out_dir, out_name + ".jgw"))

            if p['save_legend']:
                self.progress.emit("Generando leyenda...", 90)
                create_colormap_legend(
                    grid_z, colormap=p['colormap'],
                    output_path=os.path.join(out_dir, out_name + "_legend.png"),
                    class_interval=p['class_interval'] if p['classify'] else None,
                    whitening=p['whitening'] / 100.0
                )

            self.done.emit(True, "Proceso completado exitosamente.")
        except Exception as exc:
            import traceback
            self.done.emit(False, traceback.format_exc())


# =============================================================================
# GUI principal del Visualizador
# =============================================================================

class LandXMLVisualizadorGUI(QWidget):
    """
    Pestaña de visualización de superficies LandXML.

    Hereda de QWidget para integrarse en QTabWidget de la suite.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        from ..config import get_section
        cfg = get_section('visualizador')
        self._cfg = cfg
        self._xml_file = ""
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

        # --- Archivo ---
        card_file = Card(self, "Archivo de Entrada")
        self._file_sel = FileSelector("Superficie LandXML (.xml)", parent=self)
        self._file_sel.fileSelected.connect(self._on_file_selected)
        card_file.content_layout().addWidget(self._file_sel)
        layout.addWidget(card_file)

        # --- Parámetros ---
        card_params = Card(self, "Parámetros")
        pl = card_params.content_layout()

        # Resolución + EPSG
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

        # Nombre de salida
        row_name = _HRow()
        row_name.add(QLabel("Nombre salida:"), fixed_width=130)
        self._name_edit = QLineEdit(self._cfg.get('output_name', 'superficie'))
        row_name.add(self._name_edit)
        pl.addWidget(row_name)

        # Directorio salida
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
        self._cmap_combo.addItems(['terrain', 'gist_earth', 'YlOrBr', 'copper',
                                   'viridis', 'plasma', 'inferno', 'magma', 'cividis'])
        self._cmap_combo.setCurrentText(self._cfg.get('colormap', 'gist_earth'))
        self._cmap_combo.currentTextChanged.connect(self._update_preview)
        row_cmap.add(self._cmap_combo)
        self._preview_lbl = QLabel()
        self._preview_lbl.setFixedSize(160, 22)
        self._preview_lbl.setStyleSheet("border: 1px solid #cccccc; border-radius: 3px;")
        row_cmap.add(self._preview_lbl)
        row_cmap.addStretch()
        pl.addWidget(row_cmap)

        # Blanqueamiento
        pl.addWidget(self._make_slider_row("Blanqueamiento (%):", 'whitening',
                                           self._cfg.get('whitening', 75)))
        # Hillshade
        pl.addWidget(self._make_slider_row("Hillshade (%):", 'hillshade',
                                           self._cfg.get('hillshade', 50)))
        layout.addWidget(card_params)

        # --- Opciones de salida ---
        card_out = Card(self, "Opciones de Salida")
        ol = card_out.content_layout()

        fmt_row = _HRow()
        self._chk_png  = QCheckBox("PNG");            self._chk_png.setChecked(self._cfg.get('save_png', True))
        self._chk_jpg  = QCheckBox("JPG");            self._chk_jpg.setChecked(self._cfg.get('save_jpg', True))
        self._chk_tiff = QCheckBox("GeoTIFF");        self._chk_tiff.setChecked(self._cfg.get('save_tiff', True))
        self._chk_leg  = QCheckBox("Leyenda");        self._chk_leg.setChecked(self._cfg.get('save_legend', True))
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
        self._interval_spin.setValue(self._cfg.get('class_interval', 1.0))
        self._interval_spin.setFixedWidth(80)
        class_row.add(self._interval_spin)
        class_row.add(QLabel("m"))
        class_row.addStretch()
        ol.addWidget(class_row)
        layout.addWidget(card_out)

        # --- Botón procesar ---
        self._btn_run = QPushButton("▶  Procesar")
        self._btn_run.setObjectName("PrimaryButton")
        self._btn_run.setEnabled(False)
        self._btn_run.setCursor(Qt.PointingHandCursor)
        self._btn_run.clicked.connect(self._run)
        layout.addWidget(self._btn_run)

        # ---Progreso + estado ---
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status = QLabel("Seleccione un archivo para comenzar")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_small']}pt;")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll)

        # Inicializar preview
        self._update_preview()

    # -------------------------------------------------------------------------
    # Helpers de construcción
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
        if attr_name == 'whitening':
            slider.valueChanged.connect(lambda _: self._update_preview())

        row.add(slider)
        row.add(spinbox)

        setattr(self, f'_{attr_name}_slider', slider)
        setattr(self, f'_{attr_name}_spin', spinbox)
        return row

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------

    def _on_file_selected(self, path: str):
        self._xml_file = path
        basename = os.path.splitext(os.path.basename(path))[0]
        self._name_edit.setText(basename)
        if not self._out_dir:
            self._dir_edit.setText(os.path.dirname(path))
            self._out_dir = os.path.dirname(path)
        self._btn_run.setEnabled(True)
        self._status.setText("✓ Listo para procesar")
        self._status.setStyleSheet(f"color: {COLORS['success']}; font-size: {FONTS['size_small']}pt;")

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar directorio de salida",
                                             self._out_dir)
        if d:
            self._out_dir = d
            self._dir_edit.setText(d)

    def _update_preview(self):
        """Dibuja el gradiente del colormap seleccionado en el label de preview."""
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
        xml = self._xml_file
        if not xml or not os.path.isfile(xml):
            QMessageBox.critical(self, "Error", "Archivo LandXML no válido.")
            return

        out_dir = self._out_dir or os.path.dirname(xml)
        params = {
            'xml_file':      xml,
            'resolution':    self._res_spin.value(),
            'epsg':          self._epsg_spin.value(),
            'out_name':      self._name_edit.text().strip() or 'superficie',
            'out_dir':       out_dir,
            'colormap':      self._cmap_combo.currentText(),
            'whitening':     self._whitening_slider.value(),
            'hillshade':     self._hillshade_slider.value(),
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
        self._worker = _VisualizadorWorker(params)
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
            QMessageBox.information(self, "Éxito", msg)
        else:
            self._status.setText("✗ Error")
            self._status.setStyleSheet(f"color: {COLORS['danger']}; font-size: {FONTS['size_small']}pt;")
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n\n{msg[:600]}")
        self._progress.setVisible(False)


# =============================================================================
# Helper de layout horizontal
# =============================================================================

class _HRow(QWidget):
    """Fila horizontal de widgets con espaciado estándar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING['sm'])

    def add(self, widget: QWidget, fixed_width: int = None):
        if fixed_width:
            widget.setFixedWidth(fixed_width)
        self._layout.addWidget(widget)

    def addStretch(self):
        self._layout.addStretch()
