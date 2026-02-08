# LandXML Tools

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)

Suite de herramientas para procesamiento y visualización de archivos LandXML.

## Herramientas Incluidas

- **Visualizador** (`landxml2image`): Genera imágenes rasterizadas a partir de superficies TIN.
- **Comparador** (`landxml_diff`): Compara dos superficies y genera mapas de diferencia.

## Instalación

```bash
# Activar entorno Conda con dependencias geoespaciales
conda activate geo_interp

# Instalar en modo desarrollo (opcional)
pip install -e .
```

## Uso

### Suite Completa (Recomendado)

Ejecuta la aplicación con todas las herramientas en pestañas:

```bash
conda activate geo_interp
python landxml_suite.py
```

### Herramientas Individuales (Línea de Comandos)

```bash
# Visualizador
python apps/landxml2image.py

# Comparador (CLI)
python apps/landxml_diff.py --file1 superficie1.xml --file2 superficie2.xml
```

## Estructura del Proyecto

```
landxml_tools/
├── landxml_suite.py        # Punto de entrada principal
├── apps/                   # Aplicaciones standalone y scripts
│   ├── landxml2image.py
│   ├── landxml_diff.py
│   └── landxml_diff_gui.py
├── src/
│   └── landxml_tools/      # Librería compartida
│       ├── gui/            # Widgets y tema visual
│       ├── io/             # Lectura/escritura de archivos
│       ├── processing/     # Algoritmos (TIN, rasterización)
│       └── viz/            # Visualización (leyendas, gráficos)
└── test/                   # Archivos de prueba
```

## 👤 Autor

**Pablo Hevia · Hedra Topografía**  
📧 [pablo@hedrasl.com](mailto:pablo@hedrasl.com)

## Licencia

Este proyecto está bajo la licencia **GPL v3**.
