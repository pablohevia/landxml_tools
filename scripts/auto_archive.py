"""
Script de archivado automático para LandXML Tools.

Detecta planes marcados como "COMPLETADO" en AGENTS.md
y los mueve a CHANGELOG.md automáticamente.

Uso:
    python scripts/auto_archive.py [--dry-run]
"""

import os
import re
import sys
from datetime import datetime

# Rutas
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_PATH = os.path.join(PROJECT_ROOT, "AGENTS.md")
CHANGELOG_PATH = os.path.join(PROJECT_ROOT, "CHANGELOG.md")


def read_file(path: str) -> str:
    """Lee el contenido de un archivo."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    """Escribe contenido a un archivo."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def extract_completed_plans(agents_content: str) -> list[dict]:
    """
    Extrae secciones de planes activos marcados como COMPLETADO.
    
    Returns:
        list: Lista de diccionarios con 'titulo', 'contenido', 'inicio', 'fin'
    """
    planes = []
    
    # Buscar secciones "## Plan activo" con "COMPLETADO"
    # El patrón busca desde "## Plan activo" hasta el siguiente "##" o fin de archivo
    pattern = r'(## Plan activo[^\n]*\n.*?)(?=##\s+[A-Z]|$)'
    matches = re.finditer(pattern, agents_content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        section = match.group(0)
        
        # Verificar si tiene COMPLETADO
        if 'COMPLETADO' in section.upper():
            # Extraer título
            titulo_match = re.search(r'## Plan activo.*?(?=\n)', section)
            titulo = titulo_match.group(0) if titulo_match else "Plan activo"
            
            planes.append({
                'titulo': titulo,
                'contenido': section,
                'inicio': match.start(),
                'fin': match.end()
            })
    
    return planes


def archive_plans(dry_run: bool = True) -> None:
    """
    Archiva los planes completados.
    
    Args:
        dry_run: Si True, solo muestra lo que haría sin hacer cambios.
    """
    if not os.path.exists(AGENTS_PATH):
        print(f"ERROR: No se encontró {AGENTS_PATH}")
        sys.exit(1)
    
    print("=" * 60)
    print("AUTO-ARCHIVE - LandXML Tools")
    print("=" * 60)
    
    # Leer archivos
    agents_content = read_file(AGENTS_PATH)
    changelog_content = read_file(CHANGELOG_PATH) if os.path.exists(CHANGELOG_PATH) else ""
    
    # Extraer planes completados
    planes = extract_completed_plans(agents_content)
    
    if not planes:
        print("\nNo se encontraron planes completados para archivar.")
        return
    
    print(f"\nSe encontraron {len(planes)} plan(es) completados:")
    for i, plan in enumerate(planes, 1):
        print(f"  {i}. {plan['titulo']}")
    
    if dry_run:
        print("\n[MODO DRY-RUN - No se realizarán cambios]")
        print("\nPlanes que se moverían a CHANGELOG.md:")
        for plan in planes:
            print(f"\n--- {plan['titulo']} ---")
            print(plan['contenido'][:200] + "..." if len(plan['contenido']) > 200 else plan['contenido'])
        return
    
    # Ejecutar archivado
    fecha = datetime.now().strftime("%Y-%m-%d")
    
    # Construir nuevas entradas para CHANGELOG
    nuevas_entradas = []
    for plan in planes:
        entrada = f"\n---\n\n## {fecha}\n\n### {plan['titulo'].replace('## Plan activo ', '').strip()}\n"
        # Limpiar el contenido (quitar marcar de COMPLETADO, etc.)
        contenido = plan['contenido']
        contenido = re.sub(r'\*\*Estado:\*\*.*?COMPLETADO', '**Estado:** archivado', contenido)
        nuevas_entradas.append(entrada + contenido)
    
    # Actualizar CHANGELOG
    nuevo_changelog = f"# CHANGELOG.md - Historial de cambios de LandXML Tools\n"
    nuevo_changelog += "\n".join(nuevas_entradas)
    if changelog_content:
        # Añadir contenido original después de las nuevas entradas
        nuevo_changelog += "\n\n---\n\n" + changelog_content
    
    # Actualizar AGENTS.md (quitar las secciones archivadas)
    nuevo_agents = agents_content
    # Ordenar por posición inversa para no descalcular índices al borrar
    for plan in sorted(planes, key=lambda p: p['inicio'], reverse=True):
        nuevo_agents = nuevo_agents[:plan['inicio']] + nuevo_agents[plan['fin']:]
    
    # Limpiar líneas vacías consecutivas extras
    nuevo_agents = re.sub(r'\n{3,}', '\n\n', nuevo_agents)
    
    # Escribir archivos
    write_file(CHANGELOG_PATH, nuevo_changelog)
    write_file(AGENTS_PATH, nuevo_agents)
    
    print("\n[OK] Archiv completed!")
    print(f"  - CHANGELOG.md actualizado con {len(planes)} entrada(s)")
    print(f"  - AGENTS.md limpiado de planes completados")


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    archive_plans(dry_run=dry_run)


if __name__ == "__main__":
    main()