"""
Módulo de configuración para LandXML Tools.
Carga y gestiona los valores por defecto desde config.json.
"""

import json
import os

_config = None
_config_path = None

def _find_config_path():
    """Busca config.json en ubicaciones estándar."""
    # 1. Directorio del proyecto (junto a landxml_suite.py)
    current = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current, '..', '..'))
    config_in_root = os.path.join(project_root, 'config.json')
    if os.path.exists(config_in_root):
        return config_in_root
    
    # 2. Directorio src/landxml_tools
    config_in_src = os.path.join(current, '..', 'config.json')
    if os.path.exists(config_in_src):
        return config_in_src
    
    return None

def load_config():
    """Carga la configuración desde config.json."""
    global _config, _config_path
    
    if _config is not None:
        return _config
    
    _config_path = _find_config_path()
    
    if _config_path and os.path.exists(_config_path):
        try:
            with open(_config_path, 'r', encoding='utf-8') as f:
                _config = json.load(f)
            return _config
        except Exception as e:
            print(f"Advertencia: No se pudo cargar config.json: {e}")
    
    # Valores por defecto si no existe config.json
    _config = {
        "visualizador": {
            "colormap": "gist_earth",
            "whitening": 75,
            "hillshade": 50,
            "resolution": 0.05,
            "epsg": 25830,
            "output_name": "superficie",
            "classify": True,
            "class_interval": 1.0,
            "save_png": True,
            "save_jpg": True,
            "save_tiff": True,
            "save_legend": True
        },
        "comparador": {
            "colormap": "coolwarm_r",
            "whitening": 70,
            "hillshade": 0,
            "resolution": 0.05,
            "epsg": 25830,
            "output_name": "diferencia",
            "classify": True,
            "class_interval": 0.25,
            "save_png": True,
            "save_jpg": True,
            "save_tiff": True,
            "save_legend": True
        }
    }
    return _config

def get(section, key, default=None):
    """Obtiene un valor de configuración."""
    config = load_config()
    return config.get(section, {}).get(key, default)

def get_section(section):
    """Obtiene una sección completa de configuración."""
    config = load_config()
    return config.get(section, {})
