"""
Script para limpiar archivos duplicados y organizar estructura del proyecto
"""
import os
import shutil
from pathlib import Path

def cleanup_duplicates():
    """Elimina archivos duplicados según el análisis del repositorio"""
    
    base_path = Path(__file__).parent
    
    # Archivos duplicados identificados
    duplicates_to_remove = [
        # Si ANALISIS_LIMPIEZA.md está en raíz y también en docs/, eliminar el de raíz
        base_path / "ANALISIS_LIMPIEZA.md",
    ]
    
    # Archivos que deben moverse a docs/
    files_to_move = [
        ("CORRECCIONES_APLICADAS.md", "docs/"),
        ("CORRECCIONES_FINALES.md", "docs/"),
        ("ESTADO_FINAL.txt", "docs/"),
        ("ESTRUCTURA.txt", "docs/"),
        ("RESUMEN_ACTUALIZACION.txt", "docs/"),
        ("INICIO_RAPIDO.md", "docs/"),
        ("LEEME_PRIMERO.txt", "docs/"),
    ]
    
    print("🧹 Iniciando limpieza de archivos duplicados...\n")
    
    # Eliminar duplicados
    removed_count = 0
    for file_path in duplicates_to_remove:
        if file_path.exists():
            # Verificar que existe en docs/ antes de eliminar
            docs_version = base_path / "docs" / file_path.name
            if docs_version.exists():
                print(f"❌ Eliminando duplicado: {file_path.name}")
                file_path.unlink()
                removed_count += 1
            else:
                print(f"⚠️  {file_path.name} no tiene versión en docs/, manteniendo en raíz")
    
    # Mover archivos a docs/
    moved_count = 0
    docs_dir = base_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    for filename, target_dir in files_to_move:
        source = base_path / filename
        target = base_path / target_dir / filename
        
        if source.exists() and not target.exists():
            print(f"📦 Moviendo {filename} a {target_dir}")
            shutil.move(str(source), str(target))
            moved_count += 1
        elif source.exists() and target.exists():
            print(f"⚠️  {filename} ya existe en {target_dir}, eliminando de raíz")
            source.unlink()
            removed_count += 1
    
    print(f"\n✅ Limpieza completada:")
    print(f"   - {removed_count} archivo(s) eliminado(s)")
    print(f"   - {moved_count} archivo(s) movido(s)")

if __name__ == "__main__":
    cleanup_duplicates()

