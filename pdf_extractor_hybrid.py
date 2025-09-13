#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor híbrido de códigos alfanuméricos (combinando filename y content).
Módulo separado para mantener el código organizado.
Versión genérica que funciona con cualquier tipo de código.
"""

from typing import List, Dict
from pathlib import Path
from pdf_extractor_filename import build_filename_index
from pdf_extractor_content import build_content_index


def build_hybrid_index(files: List[Path], pattern_str: str, max_pages: int = 10000) -> tuple:
    """
    Construye un índice combinando búsqueda por nombre de archivo y contenido.
    
    Args:
        files: Lista de archivos PDF
        pattern_str: Patrón regex para búsqueda en contenido
        max_pages: Límite de páginas a escanear por archivo
    
    Returns:
        Tupla (by_code, debug_log) donde:
        - by_code: Diccionario con códigos como claves
        - debug_log: Lista de mensajes de depuración
    """
    debug_log = ["=== Modo híbrido: combinando filename + content ==="]
    
    # 1. Procesar nombres de archivo
    debug_log.append("1. Procesando nombres de archivo...")
    by_code_filename, log_filename = build_filename_index(files, max_pages)
    debug_log.extend(log_filename)
    
    # 2. Procesar contenido
    debug_log.append("2. Procesando contenido de PDFs...")
    by_code_content, log_content = build_content_index(files, pattern_str, max_pages)
    debug_log.extend(log_content)
    
    # 3. Combinar resultados
    debug_log.append("3. Combinando resultados...")
    by_code_combined = {}
    
    # Primero agregar todos los resultados de filename
    for code, entries in by_code_filename.items():
        by_code_combined[code] = entries.copy()
    
    # Luego agregar resultados de content, evitando duplicados del mismo archivo
    for code, entries in by_code_content.items():
        if code not in by_code_combined:
            by_code_combined[code] = []
        
        for entry in entries:
            # Verificar si ya tenemos una entrada para este archivo
            existing_files = [e["file"] for e in by_code_combined[code]]
            if entry["file"] not in existing_files:
                by_code_combined[code].append(entry)
    
    # Estadísticas finales
    total_codes = len(by_code_combined)
    filename_only = len(by_code_filename)
    content_only = len(by_code_content)
    
    debug_log.append(f"Resumen: {total_codes} códigos únicos encontrados")
    debug_log.append(f"  - Solo en nombres: {filename_only}")
    debug_log.append(f"  - Solo en contenido: {content_only}")
    debug_log.append(f"  - Total combinado: {total_codes}")
    
    return by_code_combined, debug_log


if __name__ == "__main__":
    # Prueba del módulo
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        test_pdf = Path(sys.argv[1])
        if test_pdf.exists():
            pattern = r"\b[A-Za-z]{2,}[-_ ]?\d{1,}[A-Za-z0-9]*\b"
            by_code, log = build_hybrid_index([test_pdf], pattern, 10)
            
            print("Códigos encontrados (modo híbrido):")
            for code, entries in by_code.items():
                print(f"  {code}:")
                for entry in entries:
                    source = entry['source']
                    page = entry.get('page', 'N/A')
                    print(f"    - {entry['file']} (página {page}, fuente: {source})")
            
            print("\nLog:")
            for msg in log:
                print(f"  {msg}")
        else:
            print(f"Archivo no encontrado: {test_pdf}")
    else:
        print("Uso: python pdf_extractor_hybrid.py <archivo.pdf>")