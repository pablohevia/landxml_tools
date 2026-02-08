"""
LANDXML_DIFF - COMPARADOR DE SUPERFICIES LANDXML
=================================================

Este script compara dos superficies LandXML (TIN) de la misma zona y calcula
las diferencias de elevación.

Uso:
    conda activate geo_interp
    python apps/landxml_diff.py --file1 superficie1.xml --file2 superficie2.xml
"""

import sys
import os
import time

# Configurar path para importar landxml_tools
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_path = os.path.abspath(os.path.join(_current_dir, '..', 'src'))
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

try:
    from landxml_tools.io.landxml import parse_landxml_surface
    from landxml_tools.processing.diff import calculate_difference
    from landxml_tools.viz.plotting import create_colormap_legend, save_colored_map
    from landxml_tools.io.export import save_geotiff, save_world_file
except ImportError as e:
    print(f"Error crítico: No se puede importar 'landxml_tools': {e}")
    sys.exit(1)


def main(surface_file1=None, surface_file2=None, output_name='landxml_diff',
         resolution=0.05, epsg_code=25830, colormap='coolwarm_r',
         save_jpg=True, save_png=True, save_tiff=True, save_legend=True,
         output_dir=None, class_interval=None, whitening=0.0, progress_callback=None):
    """
    Compara dos superficies LandXML y genera imágenes de diferencia.
    
    Args:
        surface_file1: Ruta al archivo LandXML de la superficie base.
        surface_file2: Ruta al archivo LandXML de la superficie a comparar.
        output_name: Nombre base para los archivos de salida.
        resolution: Resolución del grid en metros.
        epsg_code: Código EPSG del sistema de coordenadas.
        colormap: Nombre del mapa de colores de matplotlib.
        save_jpg: Si True, guarda imagen JPG.
        save_png: Si True, guarda imagen PNG con transparencia.
        save_tiff: Si True, guarda GeoTIFF.
        save_legend: Si True, genera imagen de leyenda.
        output_dir: Directorio de salida. Si None, usa el directorio del archivo 2.
        class_interval: Intervalo para clasificar elevaciones. None para continuo.
        whitening: Porcentaje de blanqueamiento (0.0 a 1.0).
        progress_callback: Función callback(msg, percent) para reportar progreso.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    def report_progress(msg, percent=None):
        if progress_callback:
            progress_callback(msg, percent)
    
    try:
        # 1. Cargar superficies
        report_progress("Cargando superficie 1...", 5)
        points1, triangles1 = parse_landxml_surface(surface_file1)
        
        report_progress("Cargando superficie 2...", 15)
        points2, triangles2 = parse_landxml_surface(surface_file2)
        
        # 2. Calcular diferencias
        report_progress("Calculando diferencias (esto puede tardar)...", 30)
        print(f"\n{'=' * 60}\nCALCULANDO DIFERENCIAS\n{'=' * 60}")
        diff_grid, extent = calculate_difference(points1, triangles1, points2, triangles2, resolution)
        
        # Determinar directorio de salida
        if output_dir is None:
            output_dir = os.path.dirname(surface_file2)
        
        # 3. Generar imágenes
        if save_jpg or save_png:
            report_progress("Generando imágenes...", 70)
            print(f"\n{'=' * 60}\nGENERANDO IMÁGENES\n{'=' * 60}")
            
            save_colored_map(
                diff_grid, output_name,
                colormap=colormap,
                output_dir=output_dir,
                class_interval=class_interval,
                whitening=whitening,
                center_zero=True,
                save_png=save_png,
                save_jpg=save_jpg,
                rotate_90=True
            )
            
            # World Files
            if save_png:
                save_world_file(extent, diff_grid.shape, os.path.join(output_dir, output_name + ".pgw"))
            if save_jpg:
                save_world_file(extent, diff_grid.shape, os.path.join(output_dir, output_name + ".jgw"))

        # 4. GeoTIFF
        if save_tiff:
            report_progress("Generando GeoTIFF...", 85)
            print(f"\n{'=' * 60}\nGENERANDO GEOTIFF\n{'=' * 60}")
            tiff_path = os.path.join(output_dir, output_name + ".tif")
            save_geotiff(diff_grid, extent, tiff_path, epsg_code=epsg_code)
            
        # 5. Leyenda
        if save_legend and (save_png or save_jpg):
            report_progress("Generando leyenda...", 95)
            print(f"\n{'=' * 60}\nGENERANDO LEYENDA\n{'=' * 60}")
            legend_path = os.path.join(output_dir, output_name + "_legend.png")
            create_colormap_legend(
                diff_grid, colormap=colormap,
                output_path=legend_path,
                class_interval=class_interval,
                whitening=whitening,
                center_zero=True
            )
            
        report_progress("Proceso completado", 100)
        print(f"\n{'=' * 60}\nPROCESO COMPLETADO\n{'=' * 60}")
        return True, "Proceso completado exitosamente"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


if __name__ == "__main__":
    main()
