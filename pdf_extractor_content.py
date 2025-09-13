#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de códigos alfanuméricos basado en contenido de PDFs.
Módulo separado para mantener el código organizado.
Versión genérica que funciona con cualquier tipo de código.
"""

import re
from typing import List, Dict
from pathlib import Path
from pypdf import PdfReader


def extract_codes_from_text(text: str, pattern: re.Pattern) -> List[str]:
    """
    Extrae códigos alfanuméricos del texto usando el patrón especificado.
    """
    codes = []
    for match in pattern.finditer(text):
        code = match.group(0)
        # Normalizar: mayúsculas, quitar espacios/guiones/guiones bajos
        code = re.sub(r"[\s_-]", "", code.upper())
        codes.append(code)
    
    return list(dict.fromkeys(codes))  # únicos preservando orden


def extract_codes_from_page(reader: PdfReader, page_idx: int, pattern: re.Pattern) -> List[str]:
    """
    Extrae códigos alfanuméricos del TEXTO de una página específica.
    Manejo robusto de errores basado en el proyecto GUI funcional.
    """
    try:
        text = reader.pages[page_idx].extract_text() or ""
    except Exception:
        # Algunos PDFs fallan en extracción; continuar con texto vacío
        text = ""
    
    return extract_codes_from_text(text, pattern)


def build_content_index(files: List[Path], pattern_str: str, max_pages: int = 10000) -> tuple:
    """
    Construye un índice basado en contenido de PDFs.
    
    Args:
        files: Lista de archivos PDF
        pattern_str: Patrón regex como string
        max_pages: Límite de páginas a escanear por archivo
    
    Returns:
        Tupla (by_code, debug_log) donde:
        - by_code: Diccionario con códigos como claves
        - debug_log: Lista de mensajes de depuración
    """
    by_code = {}
    debug_log = []
    
    # Compilar el patrón regex
    try:
        # Limpiar el patrón que viene del frontend (doble escape)
        clean_pattern = pattern_str.replace('\\\\', '\\')
        pattern = re.compile(clean_pattern, flags=re.IGNORECASE)
    except re.error as e:
        debug_log.append(f"Error en patrón regex: {e}")
        # Usar patrón por defecto genérico
        pattern = re.compile(r"\b[A-Za-z]{2,}[-_ ]?\d{1,}[A-Za-z0-9]*\b", re.IGNORECASE)
        debug_log.append("Usando patrón por defecto genérico para códigos alfanuméricos")
    
    files_processed = 0
    codes_found = 0
    
    for pdf_path in files:
        files_processed += 1
        file_codes = []
        
        try:
            reader = PdfReader(str(pdf_path))
            page_count = min(len(reader.pages), max_pages)
            
            debug_log.append(f"Procesando {pdf_path.name}: {len(reader.pages)} páginas total, escaneando {page_count}")
            
            for page_idx in range(page_count):
                try:
                    codes = extract_codes_from_page(reader, page_idx, pattern)
                    
                    for code in codes:
                        by_code.setdefault(code, []).append({
                            "file": pdf_path.name,
                            "page": page_idx,
                            "source": "content"
                        })
                        
                        if code not in file_codes:
                            file_codes.append(code)
                
                except Exception as e:
                    debug_log.append(f"Error en página {page_idx+1} de {pdf_path.name}: {str(e)}")
            
        except Exception as e:
            debug_log.append(f"Error procesando archivo {pdf_path.name}: {str(e)}")
        
        codes_found += len(file_codes)
        if file_codes:
            debug_log.append(f"Archivo {pdf_path.name}: {len(file_codes)} códigos encontrados en contenido")
    
    return by_code, debug_log


if __name__ == "__main__":
    # Prueba del módulo
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        test_pdf = Path(sys.argv[1])
        if test_pdf.exists():
            pattern = r"\b[A-Za-z]{2,}[-_ ]?\d{1,}[A-Za-z0-9]*\b"
            by_code, log = build_content_index([test_pdf], pattern, 10)
            
            print("Códigos encontrados:")
            for code, entries in by_code.items():
                print(f"  {code}: {len(entries)} coincidencias")
            
            print("\nLog:")
            for msg in log:
                print(f"  {msg}")
        else:
            print(f"Archivo no encontrado: {test_pdf}")
    else:
        print("Uso: python pdf_extractor_content.py <archivo.pdf>")