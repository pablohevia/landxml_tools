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
    'sm':  6,
    'md': 10,
    'lg': 14,
    'xl': 20,
}

# =============================================================================
# QSS (Qt Style Sheet) global
# =============================================================================

def get_stylesheet() -> str:
    """
    Retorna el stylesheet QSS global para la aplicación.
    """
    c = COLORS
    f = FONTS
    return f"""
/* --- Estilos base --- */
QMainWindow {{
    background-color: {c['bg_app']};
}}

QWidget {{
    font-family: '{f['family']}';
    font-size: {f['size_body']}pt;
    color: {c['text_primary']};
}}

/* Forzamos que los labels y contenedores no tengan borde por defecto */
QLabel, QFrame, QScrollArea {{
    border: none;
    background: transparent;
}}

/* --- Contenedores Especiales --- */

/* Tarjetas (Card) */
QFrame[class="Card"] {{
    background-color: {c['bg_white']};
    border: 1px solid {c['border']};
    border-radius: 8px;
}}

/* Filas Horizontales (HRow) */
QWidget[class="HRow"] {{
    background: transparent;
    border: none;
}}

/* Pestaña (Tab) */
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

/* --- Botones --- */
QPushButton {{
    background-color: #e0e0e0;
    color: {c['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #d0d0d0;
}}
QPushButton:disabled {{
    background-color: #eeeeee;
    color: {c['text_muted']};
}}

/* Botón Primario */
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
    background-color: #d1d1d1;
    color: #666666;
    border: 1px solid #bbbbbb;
}}

/* Botón de búsqueda (Browse) */
QPushButton#BrowseButton {{
    background-color: #eeeeee;
    color: #333333;
    border: 1px solid #999999;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 9pt;
}}
QPushButton#BrowseButton:hover {{
    background-color: #e0e0e0;
    border: 1px solid {c['primary']};
}}

/* --- Zona Drop --- */
QFrame[class="FileDropBox"] {{
    background-color: {c['bg_white']};
    border: 2px dashed {c['border']};
    border-radius: 12px;
}}
QFrame[class="FileDropBox"][state="hover"] {{
    border: 2px dashed {c['primary']};
    background-color: {c['primary_light']};
}}

/* --- Inputs y Controles de Edición --- */
QLineEdit, QDoubleSpinBox, QSpinBox {{
    background-color: {c['input_bg']};
    border: 1px solid #b3b3b3;
    border-radius: 4px;
    padding: 5px 8px;
    color: {c['text_primary']};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {c['primary']};
    background-color: {c['bg_white']};
}}
QLineEdit:read-only {{
    background-color: #f1f1f1;
    border: 1px solid #cccccc;
    color: {c['text_secondary']};
}}

/* --- Listas y Consolas --- */
QListWidget {{
    background-color: {c['bg_white']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 4px;
}}
QListWidget::item:selected {{
    background-color: {c['primary_light']};
    color: {c['primary']};
    border-radius: 4px;
}}

QTextEdit#ConsoleLog {{
    background-color: {c['console_bg']};
    color: {c['console_fg']};
    font-family: '{f['family_mono']}';
    font-size: {f['size_small']}pt;
    border-radius: 8px;
    padding: 8px;
}}

/* --- Miscelánea --- */
QLabel#SectionLabel {{
    color: {c['text_secondary']};
    font-size: {f['size_small']}pt;
    font-weight: bold;
    letter-spacing: 0.5px;
}}

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
"""
