# LandXML Tools

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)

Suite de herramientas para procesamiento y visualización de archivos LandXML.

## Herramientas Incluidas

- **Visualizador** (`landxml2image`): Genera imágenes rasterizadas a partir de superficies TIN.
- **Comparador** (`landxml_diff`): Compara dos superficies y genera mapas de diferencia.

## Características Destacadas

*   **Visualización Topográfica Avanzada** (Opciones configurables):
    *   **Clasificación por Elevación**: Genera mapas de colores basados en rangos de altura definidos por el usuario.
    *   **Sombreado (Hillshade)**: Aplica efectos de relieve personalizables para resaltar la topografía del terreno.
    *   **Control de Intensidad**: Ajuste de blanqueo (*whitening*) variable para suavizar la visualización y mejorar la legibilidad.
*   **Georreferenciación Completa**:
    *   Salida directa en formato **GeoTIFF**, manteniendo la información espacial precisa.
    *   Generación automática de archivos **World File** (`.pgw`, `.jgw`) para formatos de imagen estándar (PNG, JPG), asegurando compatibilidad total con software CAD y GIS.
    *   **Integración con AutoCAD**: Las imágenes georreferenciadas se pueden situar automáticamente en su posición correcta utilizando la herramienta [ImageGeoRef](https://github.com/pablohevia/ImageGeoRef).

## Requisitos

- Python 3.9+
- Librerías: `numpy`, `matplotlib`, `scipy`, `lxml`, `pillow`, `rasterio`

*Se recomienda usar Conda para instalar `rasterio` en Windows.*

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/pablohevia/landxml_tools.git
   cd landxml_tools
   ```

2. Crear un entorno virtual (recomendado):
   ```bash
   # Opción A: Conda
   conda create -n landxml_env python=3.9 rasterio
   conda activate landxml_env
   pip install .

   # Opción B: venv + pip
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install .
   ```

## Uso

### Suite Completa (GUI Unificada)

Ejecuta la aplicación principal que integra todas las herramientas:

```bash
python landxml_suite.py
```

### Herramientas Individuales

Puedes ejecutar cada herramienta por separado o usar la línea de comandos para automatización:

```bash
# Visualizador (GUI)
python -m apps.landxml2image

# Comparador (CLI)
python -m apps.landxml_diff --file1 base.xml --file2 comparacion.xml
```

## Configuración Personalizada

El comportamiento por defecto de las herramientas se controla mediante el archivo `config.json` en la raíz del proyecto. Puedes modificarlo para ajustar tus preferencias:

```json
{
    "visualizador": {
        "colormap": "gist_earth",
        "whitening": 75,
        "hillshade": 50,
        "resolution": 0.05
    },
    "comparador": {
        "colormap": "coolwarm_r",
        "resolution": 0.05
    }
}
```

## Estructura del Proyecto

```
landxml_tools/
├── config.json             # Archivo de configuración
├── landxml_suite.py        # Lanzador principal
├── apps/                   # Scripts de aplicación
│   ├── landxml2image.py
│   └── landxml_diff.py
├── src/
│   └── landxml_tools/      # Librería compartida
│       ├── config.py       # Gestor de configuración
│       ├── gui/            # Interfaz gráfica
│       ├── io/             # Lectura/escritura (LandXML, GeoTIFF)
│       ├── processing/     # Algoritmos (TIN, Raster, Hillshade)
│       └── viz/            # Visualización
└── test/                   # Tests
```

## 👤 Autor

**Pablo Hevia · Hedra Topografía**  
📧 [pablo@hedrasl.com](mailto:pablo@hedrasl.com)

## Licencia

Este proyecto está bajo la licencia **GPL v3**.
