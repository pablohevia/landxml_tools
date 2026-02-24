"""
Módulo para validación y limpieza de Triangulated Irregular Networks (TIN).
"""

import numpy as np

def validate_and_clean_triangulation(points, triangles):
    """
    Valida y limpia los triángulos para evitar errores de triangulación.
    
    Elimina triángulos con índices fuera de rango, índices duplicados
    (triángulos degenerados) y triángulos con área muy pequeña.
    
    Args:
        points (ndarray): Array de forma (n, 3) con coordenadas [X, Y, Z].
        triangles (ndarray | None): Array de forma (m, 3) con índices de
            triángulos (base 0).
    
    Returns:
        ndarray | None: Array de triángulos válidos con forma (k, 3) donde
            k <= m, o None si no quedan triángulos válidos.
    
    Note:
        Los triángulos con área menor a 1e-10 unidades² se consideran
        degenerados y son eliminados.
    """
    if triangles is None:
        return None
    
    n_points = len(points)
    valid_triangles = []
    
    for i, tri in enumerate(triangles):
        # Verificar índices dentro de rango
        if np.any(tri < 0) or np.any(tri >= n_points):
            continue
        
        # Verificar que no hay índices duplicados
        if len(set(tri)) != 3:
            continue
        
        # Obtener coordenadas de los 3 vértices
        p0 = points[tri[0], :2]
        p1 = points[tri[1], :2]
        p2 = points[tri[2], :2]
        
        # Calcular área del triángulo usando producto cruzado
        # Área = 0.5 * |det([[x1-x0, y1-y0], [x2-x0, y2-y0]])|
        v1 = p1 - p0
        v2 = p2 - p0
        area = abs(v1[0] * v2[1] - v1[1] * v2[0]) / 2.0
        
        # Descartar triángulos con área muy pequeña (degenerados)
        if area > 1e-10:
            valid_triangles.append(tri)
    
    triangles_clean = np.array(valid_triangles) if valid_triangles else None
    
    n_removed = len(triangles) - len(valid_triangles)
    if n_removed > 0:
        print(f"    [!] Triángulos degenerados removidos: {n_removed}/{len(triangles)}")
    
    return triangles_clean
