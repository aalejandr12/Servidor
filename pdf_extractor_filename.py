#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de códigos alfanuméricos basado en nombres de archivo.
Módulo separado para mantener el código organizado.
Versión genérica que funciona con cualquier tipo de código.
"""

import re
from typing import List, Dict
from pathlib import Path
from pypdf import PdfReader


def extract_codes_from_filename(filename: str) -> List[str]:
    """
    Extrae códigos alfanuméricos del NOMBRE de un archivo.
    Versión genérica que busca cualquier patrón alfanumérico.
    """
    # Patrón genérico para códigos alfanuméricos en nombres de archivo
    # Busca: 2+ letras seguidas de números y opcionalmente más caracteres alfanuméricos
    GENERIC_PATTERN = r"[A-Za-z]{2,}[-_ ]?\d{1,}[A-Za-z0-9]*"
    
    codes = []
    for match in re.finditer(GENERIC_PATTERN, filename, flags=re.IGNORECASE):
        code = match.group(0)
        # Normalizar: mayúsculas, quitar espacios/guiones/guiones bajos
        code = re.sub(r"[\s_-]", "", code.upper())
        codes.append(code)
    
    return list(dict.fromkeys(codes))  # únicos preservando orden


def build_filename_index(files: List[Path], max_pages: int = 10000) -> Dict[str, List[Dict]]:
    """
    Construye un índice basado en nombres de archivo.
    
    Args:
        files: Lista de archivos PDF
        max_pages: Límite de páginas (no usado en este modo, pero mantenido por compatibilidad)
    
    Returns:
        Diccionario con códigos como claves y lista de archivos como valores
    """
    by_code = {}
    debug_log = []
    
    for pdf_path in files:
        try:
            codes_in_name = extract_codes_from_filename(pdf_path.name)
            
            for code in codes_in_name:
                by_code.setdefault(code, [])
                
                # Evitar duplicados del mismo archivo
                if not any(h["file"] == pdf_path.name for h in by_code[code]):
                    by_code[code].append({
                        "file": pdf_path.name,
                        "page": 0,  # Marcador: se interpreta como archivo completo
                        "source": "filename"
                    })
            
            if codes_in_name:
                debug_log.append(f"Archivo {pdf_path.name}: {len(codes_in_name)} códigos encontrados en nombre")
                
        except Exception as e:
            debug_log.append(f"Error procesando nombre de archivo {pdf_path.name}: {str(e)}")
    
    return by_code, debug_log


if __name__ == "__main__":
    # Prueba del módulo
    test_files = ["ABC123456_0.pdf", "MIA000043525233.pdf", "SAC-2022-VII.pdf", "XYZ789012.pdf", "documento_sin_codigo.pdf"]
    
    for filename in test_files:
        codes = extract_codes_from_filename(filename)
        print(f"{filename} -> {codes}")