<h1 align="center">⛰️ LandXML Tools</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/UI-PySide6-orange" alt="UI Framework">
  <img src="https://img.shields.io/badge/license-GPLv3-green" alt="License">
</p>

<p align="center">
  <b>Suite profesional de herramientas para procesamiento, visualización e intersección de archivos LandXML.</b>
</p>

---

## 🚀 Herramientas Incluidas (PySide6 Suite)

La aplicación principal `landxml_suite.py` integra tres potentes herramientas bajo una interfaz moderna y unificada:

1.  **🗺️ Visualizador**: Convierte superficies LandXML (TIN) en imágenes rasterizadas de alta calidad. Soporta hillshade dinámico, clasificación por cota y blanqueamiento variable.
2.  **📊 Comparador**: Compara dos superficies LandXML y genera mapas de diferencia de cota georreferenciados (GeoTIFF, PNG, JPG).
3.  **🔀 Intersección 3D**: Calcula la curva de intersección 3D entre dos superficies TIN y exporta el resultado como polilíneas 3D en formato DXF.

## ✨ Características Destacadas

*   **Interfaz Moderna**: Migración completa a **PySide6** con un sistema de temas basado en QSS (Fluent Design).
*   **Georreferenciación Completa**:
     * Exportación nativa a **GeoTIFF** con preservación de metadatos espaciales.
     * Generación de **World Files** (.pgw, .jgw) para compatibilidad total con GIS y CAD.
     * Compatible con [ImageGeoRef](https://github.com/pablohevia/ImageGeoRef) para inserción automática en AutoCAD.
*   **Motor de Intersección Robusto**: Basado en NumPy y el algoritmo de Guigue-Devillers para cálculos precisos y eficientes de intersección triángulo-triángulo.
*   **Optimización Vertical**: Interfaz diseñada para aprovechar el espacio máximo sin necesidad de scroll en pantallas de trabajo.

## 🛠️ Instalación y Requisitos

- Python 3.9+
- Librerías principales: `PySide6`, `numpy`, `matplotlib`, `scipy`, `lxml`, `ezdxf`, `rasterio`

### Instalación Rápida (Conda Recomendado)

```bash
# clonar y entrar
git clone https://github.com/pablohevia/landxml_tools.git
cd landxml_tools

# crear entorno con rasterio (mejor en conda para Windows)
conda create -n geo_interp python=3.9 rasterio
conda activate geo_interp

# instalar dependencias restantes y paquete
pip install -e .
```

## 🖥️ Uso

### Suite Completa (Recomendado)
Lanza la interfaz unificada que contiene todas las herramientas:
```bash
python landxml_suite.py
```

### Herramienta de Comparación (CLI)
Para procesos automatizados, el motor del comparador puede ejecutarse desde terminal:
```bash
python -m apps.landxml_diff --file1 base.xml --file2 comparacion.xml
```

## 📁 Estructura del Proyecto

```
landxml_tools/
├── landxml_suite.py        # Lanzador de la Suite (PySide6)
├── apps/                   # Motores de aplicación (Business Logic)
│   └── landxml_diff.py     # Lógica del comparador
├── src/landxml_tools/
│   ├── gui/                # Componentes PySide6 y sistema de temas
│   ├── processing/         # Motores de cálculo (TIN, Raster, Intersección)
│   ├── io/                 # Lectores/Escritores (LandXML, DXF, GeoTIFF)
│   └── viz/                # Generación de mapas y leyendas
└── assets/                 # Iconos y recursos visuales
```

## 👤 Autor

**Pablo Hevia · Hedra Topografía**  
📧 [pablo@hedrasl.com](mailto:pablo@hedrasl.com)

## 📄 Licencia

Este proyecto está bajo la licencia **GPL v3**.
