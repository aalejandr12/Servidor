#!/usr/bin/env python3
"""
Script de prueba para los módulos de extracción de PDFs.
"""

import sys
from pathlib import Path

# Importar módulos
from pdf_extractor_filename import build_filename_index, extract_codes_from_filename
from pdf_extractor_content import build_content_index
from pdf_extractor_hybrid import build_hybrid_index

def test_filename_extraction():
    """Prueba la extracción de códigos desde nombres de archivo."""
    print("=== Prueba de extracción por nombre de archivo ===")
    
    test_files = [
        "MIA000044043205_0.pdf",
        "MIA000043525233.pdf", 
        "MIA-784587451.pdf",
        "MIA_000123456.pdf",
        "documento_sin_mia.pdf",
        "OTRO000123.pdf"
    ]
    
    for filename in test_files:
        codes = extract_codes_from_filename(filename)
        print(f"{filename:<25} -> {codes}")

def test_with_existing_pdfs():
    """Prueba con PDFs existentes en el storage."""
    storage_dir = Path("./storage")
    
    # Buscar directorios con PDFs
    for workspace_dir in storage_dir.iterdir():
        if workspace_dir.is_dir():
            uploads_dir = workspace_dir / "uploads"
            if uploads_dir.exists():
                pdfs = list(uploads_dir.glob("*.pdf"))
                if pdfs:
                    print(f"\n=== Probando workspace: {workspace_dir.name} ===")
                    print(f"PDFs encontrados: {len(pdfs)}")
                    
                    # Probar solo con el primer PDF para no saturar
                    test_pdf = pdfs[0]
                    print(f"Probando con: {test_pdf.name}")
                    
                    # Probar extracción por nombre
                    print("\n--- Por nombre de archivo ---")
                    by_code_name, log_name = build_filename_index([test_pdf])
                    for code, entries in list(by_code_name.items())[:3]:  # Solo primeros 3
                        print(f"  {code}: {len(entries)} entradas")
                    
                    # Probar extracción por contenido  
                    print("\n--- Por contenido ---")
                    pattern = r"\bMIA[-_ ]?\d{1,}[A-Za-z0-9]*\b"
                    by_code_content, log_content = build_content_index([test_pdf], pattern, 5)
                    for code, entries in list(by_code_content.items())[:3]:  # Solo primeros 3
                        print(f"  {code}: {len(entries)} entradas")
                    
                    return  # Solo probar el primer workspace encontrado

if __name__ == "__main__":
    test_filename_extraction()
    test_with_existing_pdfs()