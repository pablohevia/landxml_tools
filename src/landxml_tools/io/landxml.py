"""
Módulo para el parseo de archivos LandXML.
"""

import os
import numpy as np
from lxml import etree

def parse_landxml_surface(xml_file):
    """
    Parsea un archivo LandXML y extrae los puntos y triángulos de la superficie TIN.
    
    Soporta versiones 1.0, 1.1 y 1.2 de LandXML. Los puntos se extraen del
    elemento <Pnts> y los triángulos del elemento <Faces>. Las coordenadas
    se convierten del formato Y,X,Z de LandXML a X,Y,Z.
    
    Args:
        xml_file (str): Ruta al archivo LandXML a parsear.
    
    Returns:
        tuple: Una tupla (points, triangles) donde:
            - points (ndarray): Array de forma (n, 3) con coordenadas [X, Y, Z]
            - triangles (ndarray | None): Array de forma (m, 3) con índices de
              vértices (base 0), o None si no hay triángulos definidos.
    
    Raises:
        ValueError: Si no se encuentra el elemento <Surface> o <Pnts> en el
            archivo, o si no hay puntos definidos.
    """
    tree = etree.parse(xml_file)
    root = tree.getroot()
    
    namespaces = [
        {'landxml': 'http://www.landxml.org/schema/LandXML-1.2'},
        {'landxml': 'http://www.landxml.org/schema/LandXML-1.1'},
        {'landxml': 'http://www.landxml.org/schema/LandXML-1.0'},
    ]
    
    # Buscar <Surface>
    surface = None
    for ns in namespaces:
        surfaces = root.findall('.//landxml:Surface', namespaces=ns)
        if surfaces:
            surface = surfaces[0]
            break
    if surface is None:
        surfaces = root.findall('.//Surface')
        if surfaces:
            surface = surfaces[0]
    if surface is None:
        raise ValueError(f"No se encontró <Surface> en {xml_file}")
    
    # Buscar <Pnts>
    pnts_container = None
    for ns in namespaces:
        pnts_container = surface.find('.//landxml:Pnts', namespaces=ns)
        if pnts_container is not None:
            break
    if pnts_container is None:
        pnts_container = surface.find('.//Pnts')
    if pnts_container is None:
        raise ValueError("No se encontró <Pnts>")
    
    # Extraer puntos
    points_list = []
    p_elements = []
    for ns in namespaces:
        p_elements = pnts_container.findall('landxml:P', namespaces=ns)
        if p_elements:
            break
    if not p_elements:
        p_elements = pnts_container.findall('P')
    
    if p_elements:
        point_dict = {}
        for p in p_elements:
            try:
                p_id = int(p.get('id'))
                coords = p.text.strip().split()
                if len(coords) >= 3:
                    # Intercambiar Y,X,Z → X,Y,Z
                    point_dict[p_id] = [float(coords[1]), float(coords[0]), float(coords[2])]
            except (ValueError, AttributeError):
                continue
        for p_id in sorted(point_dict.keys()):
            points_list.append(point_dict[p_id])
    elif pnts_container.text and pnts_container.text.strip():
        for line in pnts_container.text.strip().split('\n'):
            coords = line.strip().split()
            if len(coords) >= 3:
                # Intercambiar Y,X,Z → X,Y,Z
                points_list.append([float(coords[1]), float(coords[0]), float(coords[2])])
    
    if not points_list:
        raise ValueError("No se encontraron puntos")
    
    points = np.array(points_list)
    
    # Extraer triángulos
    faces_container = None
    for ns in namespaces:
        faces_container = surface.find('.//landxml:Faces', namespaces=ns)
        if faces_container is not None:
            break
    if faces_container is None:
        faces_container = surface.find('.//Faces')
    
    triangles_list = []
    if faces_container is not None:
        f_elements = []
        for ns in namespaces:
            f_elements = faces_container.findall('landxml:F', namespaces=ns)
            if f_elements:
                break
        if not f_elements:
            f_elements = faces_container.findall('F')
        
        if f_elements:
            for f in f_elements:
                try:
                    indices = f.text.strip().split()
                    if len(indices) >= 3:
                        # 1-based → 0-based
                        triangles_list.append([int(indices[0])-1, int(indices[1])-1, int(indices[2])-1])
                except (ValueError, AttributeError):
                    continue
        elif faces_container.text and faces_container.text.strip():
            for line in faces_container.text.strip().split('\n'):
                indices = line.strip().split()
                if len(indices) >= 3:
                    try:
                        triangles_list.append([int(indices[0])-1, int(indices[1])-1, int(indices[2])-1])
                    except ValueError:
                        continue
    
    triangles = np.array(triangles_list) if triangles_list else None
    
    print(f"  {os.path.basename(xml_file)}: {len(points)} puntos, {len(triangles) if triangles is not None else 0} triángulos")
    
    return points, triangles
