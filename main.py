# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import aiofiles
import re
import json
import uuid

# Importar módulos especializados
from pdf_extractor_filename import build_filename_index
from pdf_extractor_content import build_content_index  
from pdf_extractor_hybrid import build_hybrid_index

# ========= CONFIG =========
STORAGE_DIR = Path("./storage").resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Cambia estos orígenes por TU GitHub Pages y/o tu dominio
ALLOWED_ORIGINS = [
    "https://aaleddy.app",             # Dominio principal
    "https://www.aaleddy.app",         # Con www
    "https://*.aaleddy.app",           # Subdominios
    "http://localhost:5173",           # útil si haces pruebas locales de front
    "http://localhost:3000",           # útil para pruebas
    "*"                                # Temporal para debugging
]

# Patrón por defecto para compatibilidad con requests antiguos (genérico)
DEFAULT_CODE_REGEX = r"\b[A-Za-z]{2,}[-_ ]?\d{1,}[A-Za-z0-9]*\b"

# ========= APP =========
app = FastAPI(title="PDF Organizer API - Genérico", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporal para debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= MODELOS =========
class IndexRequest(BaseModel):
    pattern: str = Field(DEFAULT_CODE_REGEX, description="Regex para contenido (captura códigos alfanuméricos).")
    scan_mode: Literal["content", "filename", "both"] = Field("both", description="Dónde buscar los códigos.")
    max_pages: int = Field(10000, description="Límite de páginas a escanear por archivo.")

class MergeByCodeRequest(BaseModel):
    order: List[str] = Field(..., description="Ej.: ['ABC123456','XYZ789012','MIA000043525233']")
    output_name: str = Field("resultado_por_codigo.pdf")
    pages_per_code: Literal["first", "all"] = Field("first", description="Si el hit es por contenido: 1ª página o todas.")
    on_missing: Literal["skip", "error"] = Field("skip", description="Qué hacer si no aparece un código en el índice.")
    source_filter: Literal["any", "content", "filename"] = Field("any", description="Filtrar por fuente del match.")
    filename_behavior: Literal["first_page", "entire_pdf"] = Field(
        "first_page",
        description="Si el hit viene del NOMBRE: tomar 1ª página o TODO el PDF."
    )

class MergeByBaseRequest(BaseModel):
    bases: List[str] = Field(..., description="Bases tipo 'ABC123456' o 'MIA000044043205' (busca _0.pdf, _1.pdf...).")
    output_name: str = Field("resultado_por_bases.pdf")

# ========= UTIL =========
def _ws_dir(ws_id: str) -> Path:
    d = STORAGE_DIR / ws_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def _uploads_dir(ws_id: str) -> Path:
    d = _ws_dir(ws_id) / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _index_path(ws_id: str) -> Path:
    return _ws_dir(ws_id) / "index.json"

def _load_index(ws_id: str) -> Dict:
    p = _index_path(ws_id)
    if not p.exists():
        return {"by_code": {}, "files": []}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_index(ws_id: str, index: Dict):
    with _index_path(ws_id).open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def _safe_pdf_name(name: str) -> str:
    name = name.strip().replace("\\", "_").replace("/", "_")
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name

def _find_parts(base: str, folder: Path) -> List[Path]:
    """
    Busca archivos base_N.pdf y los ordena por N (0,1,2,...).
    """
    patron = re.compile(rf"^{re.escape(base)}_(\d+)\.pdf$", re.IGNORECASE)
    candidatos = []
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() == ".pdf":
            m = patron.match(p.name)
            if m:
                try:
                    idx = int(m.group(1))
                    candidatos.append((idx, p))
                except ValueError:
                    pass
    candidatos.sort(key=lambda t: t[0])
    return [p for _, p in candidatos]

# ========= ENDPOINTS =========
@app.get("/")
def serve_main_page():
    """Sirve la página principal del organizador."""
    try:
        with open("organizador.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return {"message": "Organizador de PDFs por Código - API Genérica", "version": "2.0", "endpoints": ["/workspaces", "/health"]}

@app.get("/debug")
def serve_debug_page():
    """Sirve la página de debug del organizador."""
    try:
        with open("index_mejorado.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página de debug no encontrada")

@app.get("/health")
def health():
    return {"ok": True, "version": "2.0", "modules": ["filename", "content", "hybrid"]}

@app.post("/workspaces")
def create_workspace():
    ws_id = uuid.uuid4().hex[:10]
    _ws_dir(ws_id)
    return {"workspace_id": ws_id}

@app.get("/workspaces")
def list_workspaces():
    lst = []
    for d in STORAGE_DIR.iterdir():
        if d.is_dir():
            idx = _index_path(d.name)
            lst.append({"workspace_id": d.name, "has_index": idx.exists()})
    return {"workspaces": lst}

@app.post("/workspaces/{ws_id}/upload")
async def upload_pdfs(ws_id: str, files: List[UploadFile] = File(...)):
    up_dir = _uploads_dir(ws_id)
    saved = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Solo PDFs. Rechazado: {f.filename}")
        target = up_dir / _safe_pdf_name(f.filename)
        async with aiofiles.open(target, "wb") as out:
            while True:
                chunk = await f.read(1024 * 1024)
                if not chunk:
                    break
                await out.write(chunk)
        saved.append(target.name)
    return {"saved": saved, "count": len(saved)}

@app.get("/workspaces/{ws_id}/files")
def list_files(ws_id: str):
    up_dir = _uploads_dir(ws_id)
    files = [p.name for p in up_dir.glob("*.pdf")]
    return {"files": files}

@app.post("/workspaces/{ws_id}/index")
def build_index(ws_id: str, req: IndexRequest):
    """
    Construye índice según scan_mode usando módulos especializados:
    - content: busca con regex dentro de páginas (TEXTO embebido)
    - filename: detecta códigos en el NOMBRE del archivo
    - both: combina ambas estrategias
    """
    up_dir = _uploads_dir(ws_id)
    files = sorted([p for p in up_dir.glob("*.pdf")], key=lambda p: p.name.lower())
    if not files:
        raise HTTPException(status_code=400, detail="No hay PDFs subidos.")

    index = {"by_code": {}, "files": [p.name for p in files]}
    
    try:
        # Usar módulos especializados según el modo seleccionado
        if req.scan_mode == "filename":
            by_code, debug_log = build_filename_index(files, req.max_pages)
        elif req.scan_mode == "content":
            by_code, debug_log = build_content_index(files, req.pattern, req.max_pages)
        elif req.scan_mode == "both":
            by_code, debug_log = build_hybrid_index(files, req.pattern, req.max_pages)
        else:
            raise HTTPException(status_code=400, detail=f"scan_mode no válido: {req.scan_mode}")
        
        index["by_code"] = by_code
        
        # Guardar el índice
        _save_index(ws_id, index)
        
        # Opcional: guardar log de depuración
        log_path = _ws_dir(ws_id) / "debug_log.txt"
        with log_path.open("w", encoding="utf-8") as f:
            f.write(f"Modo: {req.scan_mode}\n")
            f.write(f"Patrón: {req.pattern}\n")
            f.write("="*50 + "\n")
            f.write("\n".join(debug_log))
        
        return {
            "ok": True,
            "scan_mode": req.scan_mode,
            "files_processed": len(files),
            "total_files": len(files),
            "codes_found": len(by_code),
            "index_sample": dict(list(by_code.items())[:5]),
            "debug_log": debug_log[:10]  # Primeras 10 líneas del log
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al construir el índice: {str(e)}")

@app.get("/workspaces/{ws_id}/index")
def get_index(ws_id: str):
    return _load_index(ws_id)

@app.post("/workspaces/{ws_id}/merge-by-code")
def merge_by_code(ws_id: str, req: MergeByCodeRequest):
    index = _load_index(ws_id)
    by_code: Dict[str, List[Dict]] = index.get("by_code", {})
    up_dir = _uploads_dir(ws_id)
    out_name = _safe_pdf_name(req.output_name)
    out_path = _ws_dir(ws_id) / out_name

    writer = PdfWriter()
    total_pages = 0

    def add_page(file_name: str, page_idx: int):
        nonlocal total_pages
        src = up_dir / file_name
        reader = PdfReader(str(src))
        if 0 <= page_idx < len(reader.pages):
            writer.add_page(reader.pages[page_idx])
            total_pages += 1

    def add_entire_pdf(file_name: str):
        nonlocal total_pages
        src = up_dir / file_name
        reader = PdfReader(str(src))
        for p in reader.pages:
            writer.add_page(p)
            total_pages += 1

    for code in req.order:
        hits = by_code.get(code, [])
        if not hits:
            if req.on_missing == "error":
                raise HTTPException(status_code=404, detail=f"Código no encontrado: {code}")
            continue

        # filtrar por fuente
        if req.source_filter != "any":
            hits = [h for h in hits if h.get("source") == req.source_filter]
            if not hits:
                if req.on_missing == "error":
                    raise HTTPException(status_code=404, detail=f"Código no disponible desde '{req.source_filter}': {code}")
                continue

        # orden estable
        hits_sorted = sorted(hits, key=lambda h: (h.get("source",""), h["file"].lower(), h["page"]))

        if req.pages_per_code == "first":
            h = hits_sorted[0]
            if h.get("source") == "filename" and req.filename_behavior == "entire_pdf":
                add_entire_pdf(h["file"])
            else:
                add_page(h["file"], h["page"])
        else:  # "all"
            for h in hits_sorted:
                if h.get("source") == "filename" and req.filename_behavior == "entire_pdf":
                    add_entire_pdf(h["file"])
                else:
                    add_page(h["file"], h["page"])

    if total_pages == 0:
        raise HTTPException(status_code=400, detail="No se agregaron páginas. Revisa índice/filtros/orden.")

    with out_path.open("wb") as f:
        writer.write(f)

    return {
        "ok": True,
        "output": out_name,
        "pages": total_pages,
        "download_url": f"/workspaces/{ws_id}/download/{out_name}"
    }

@app.post("/workspaces/{ws_id}/merge-by-bases")
def merge_by_bases(ws_id: str, req: MergeByBaseRequest):
    up_dir = _uploads_dir(ws_id)
    out_name = _safe_pdf_name(req.output_name)
    out_path = _ws_dir(ws_id) / out_name

    writer = PdfWriter()
    total_pages = 0

    def add_pdf(path: Path):
        nonlocal total_pages
        reader = PdfReader(str(path))
        for p in reader.pages:
            writer.add_page(p)
            total_pages += 1

    for base in req.bases:
        parts = _find_parts(base, up_dir)
        if not parts:
            simple = up_dir / f"{base}.pdf"
            if simple.exists():
                add_pdf(simple)
            continue
        for p in parts:
            add_pdf(p)

    if total_pages == 0:
        raise HTTPException(status_code=400, detail="No se agregaron páginas (verifica 'bases' y archivos).")

    with out_path.open("wb") as f:
        writer.write(f)

    return {
        "ok": True,
        "output": out_name,
        "pages": total_pages,
        "download_url": f"/workspaces/{ws_id}/download/{out_name}"
    }

@app.get("/workspaces/{ws_id}/download/{filename}")
def download(ws_id: str, filename: str):
    path = _ws_dir(ws_id) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(path, media_type="application/pdf", filename=filename)
