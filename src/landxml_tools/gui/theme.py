"""
Tema visual para LandXML Tools (PySide6).

Paleta basada en el estilo Fluent/Azure claro de InterLandXML.
Colores principales: fondo #f9f9f9, blanco #ffffff, azul #0078d4.
"""

# =============================================================================
# Paleta de colores
# =============================================================================

COLORS = {
    'bg_app':          '#f9f9f9',   # Fondo general de la aplicación
    'bg_white':        '#ffffff',   # Fondo de tarjetas y paneles
    'primary':         '#0078d4',   # Azul principal (acción)
    'primary_hover':   '#005a9e',   # Azul oscuro (hover)
    'primary_light':   '#f0f7ff',   # Fondo de zona drop en hover
    'success':         '#107c10',   # Verde éxito
    'success_hover':   '#0a5e0a',
    'danger':          '#d83b01',   # Rojo error/peligro
    'warning':         '#f59e0b',   # Naranja advertencia
    'text_primary':    '#2d2d2d',   # Texto principal
    'text_secondary':  '#555555',   # Texto secundario / labels
    'text_muted':      '#888888',   # Texto atenuado / placeholders
    'border':          '#cccccc',   # Bordes y separadores
    'border_hover':    '#0078d4',   # Borde en hover/active
    'input_bg':        '#ffffff',   # Fondo de inputs
    'console_bg':      '#1e1e1e',   # Fondo de consola de log
    'console_fg':      '#d4d4d4',   # Texto de consola de log
}

# =============================================================================
# Tipografía
# =============================================================================

FONTS = {
    'family':       'Segoe UI',
    'family_mono':  'Consolas',
    'size_title':   16,
    'size_heading': 11,
    'size_body':    10,
    'size_small':    9,
    'size_tiny':     8,
}

# =============================================================================
# Espaciado
# =============================================================================

SPACING = {
    'xs':  4,
    'sm':  8,
    'md': 12,
    'lg': 16,
    'xl': 24,
}

# =============================================================================
# QSS (Qt Style Sheet) global
# =============================================================================

def get_stylesheet() -> str:
    """
    Retorna el stylesheet QSS global para la aplicación.

    Returns:
        str: Cadena de texto con los estilos CSS de Qt.
    """
    c = COLORS
    f = FONTS
    return f"""
/* --- Ventana y fondo --- */
QMainWindow, QWidget {{
    background-color: {c['bg_app']};
    font-family: '{f['family']}';
    font-size: {f['size_body']}pt;
    color: {c['text_primary']};
}}

/* --- Pestaña (Tab) --- */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 0px;
    background-color: {c['bg_app']};
}}
QTabBar::tab {{
    background-color: {c['bg_white']};
    color: {c['text_secondary']};
    padding: 10px 24px;
    border: 1px solid {c['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: {f['size_body']}pt;
    font-family: '{f['family']}';
    min-width: 120px;
}}
QTabBar::tab:selected {{
    background-color: {c['primary']};
    color: #ffffff;
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background-color: {c['primary_light']};
    color: {c['primary']};
}}

/* --- Botón genérico --- */
QPushButton {{
    background-color: #e0e0e0;
    color: {c['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-family: '{f['family']}';
    font-size: {f['size_body']}pt;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #d0d0d0;
}}
QPushButton:disabled {{
    background-color: #eeeeee;
    color: {c['text_muted']};
}}

/* --- Botón primario de acción --- */
QPushButton#PrimaryButton {{
    background-color: {c['primary']};
    color: #ffffff;
    font-size: {f['size_heading']}pt;
    padding: 10px 20px;
}}
QPushButton#PrimaryButton:hover {{
    background-color: {c['primary_hover']};
}}
QPushButton#PrimaryButton:disabled {{
    background-color: #cccccc;
    color: #888888;
}}

/* --- Zona Drop --- */
QFrame#DropZone {{
    background-color: {c['bg_white']};
    border: 2px dashed {c['border']};
    border-radius: 12px;
}}
QFrame#DropZone[hover="true"] {{
    border: 2px dashed {c['primary']};
    background-color: {c['primary_light']};
}}

/* --- Inputs --- */
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
    background-color: {c['input_bg']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 8px;
    font-family: '{f['family']}';
    font-size: {f['size_body']}pt;
    color: {c['text_primary']};
    selection-background-color: {c['primary']};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {c['primary']};
}}
QLineEdit:read-only {{
    background-color: #f1f1f1;
    color: {c['text_secondary']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

/* --- Lista --- */
QListWidget {{
    background-color: {c['bg_white']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 4px;
    font-size: {f['size_body']}pt;
}}
QListWidget::item:selected {{
    background-color: {c['primary_light']};
    color: {c['primary']};
    border-radius: 4px;
}}

/* --- Consola de log --- */
QTextEdit#ConsoleLog {{
    background-color: {c['console_bg']};
    color: {c['console_fg']};
    font-family: '{f['family_mono']}';
    font-size: {f['size_small']}pt;
    border-radius: 8px;
    padding: 8px;
    border: none;
}}

/* --- Labels de sección --- */
QLabel#SectionLabel {{
    color: {c['text_secondary']};
    font-size: {f['size_small']}pt;
    font-weight: bold;
    letter-spacing: 0.5px;
}}

/* --- Separador --- */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {c['border']};
}}

/* --- Checkbox --- */
QCheckBox {{
    spacing: 8px;
    font-size: {f['size_body']}pt;
    color: {c['text_primary']};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {c['border']};
    border-radius: 3px;
    background-color: {c['input_bg']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['primary']};
    border-color: {c['primary']};
}}

/* --- ScrollBar --- */
QScrollBar:vertical {{
    width: 8px;
    background: transparent;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c['border']};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* --- Barra de progreso --- */
QProgressBar {{
    border: 1px solid {c['border']};
    border-radius: 6px;
    background-color: {c['bg_white']};
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {c['primary']};
    border-radius: 5px;
}}
"""
