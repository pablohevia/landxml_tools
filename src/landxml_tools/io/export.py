"""
Módulo para exportación de archivos (GeoTIFF, World Files).
"""

import os
import numpy as np
import rasterio
from rasterio.transform import from_origin

def save_geotiff(grid, extent, output_path, epsg_code=25830, nodata=np.nan):
    """
    Guarda un grid (elevaciones o diferencias) como archivo GeoTIFF georreferenciado.
    
    Args:
        grid (ndarray): Array 2D con valores.
        extent (list): [xmin, xmax, ymin, ymax] de la extensión geográfica.
        output_path (str): Ruta completa al archivo de salida (.tif).
        epsg_code (int): Código EPSG del sistema de coordenadas.
        nodata (float): Valor para nodata.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    xmin, xmax, ymin, ymax = extent
    nrows, ncols = grid.shape
    pixel_size_x = (xmax - xmin) / ncols
    pixel_size_y = (ymax - ymin) / nrows
    
    transform = from_origin(xmin, ymax, pixel_size_x, pixel_size_y)
    
    # Invertir verticalmente y redondear a 3 decimales (estándar en topografía)
    grid_corrected = np.round(np.flipud(grid), 3)
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=nrows,
        width=ncols,
        count=1,
        dtype='float32',
        crs=f'EPSG:{epsg_code}',
        transform=transform,
        nodata=nodata
    ) as dst:
        dst.write(grid_corrected.astype('float32'), 1)
    
    print(f"  GeoTIFF → {output_path} (EPSG:{epsg_code})")

def save_world_file(extent, grid_shape, output_path):
    """
    Guarda un archivo World (.pgw, .jgw) para georreferenciación de imágenes.
    
    Args:
        extent (list): [xmin, xmax, ymin, ymax].
        grid_shape (tuple): (rows, cols) del grid ORIGINAL (antes de rotación).
                            Normalmente grid_z.shape.
        output_path (str): Ruta completa al archivo de salida.
    """
    xmin, xmax, ymin, ymax = extent
    num_rows_y, num_cols_x = grid_shape
    
    pixel_size_x = (xmax - xmin) / num_cols_x
    pixel_size_y = (ymax - ymin) / num_rows_y
    
    x_upper_left = xmin + pixel_size_x / 2
    # El world file asume origen en esquina superior izquierda, pero Y crece hacia abajo
    # En coordenadas geográficas Y crece hacia arriba.
    # El standard world file tiene pixel size Y negativo.
    y_upper_left = ymax - pixel_size_y / 2
    
    with open(output_path, "w") as f:
        f.write(f"{pixel_size_x:.10f}\n")
        f.write("0.0\n")
        f.write("0.0\n")
        f.write(f"{-pixel_size_y:.10f}\n")
        f.write(f"{x_upper_left:.10f}\n")
        f.write(f"{y_upper_left:.10f}\n")
    
    print(f"  World File → {output_path}")
