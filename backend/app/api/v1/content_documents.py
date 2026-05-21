"""
API endpoints para ContentAgent y DocumentAgent.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Imports de servicios y agentes
from app.services.document_service import process_document_upload
from app.agents.content_agent import content_agent, ContentState
# from app.services.content_service import generate_content # (Opcional si hubiera servicio separado)

router = APIRouter()

# --- Modelos Pydantic ---

class ContentRequest(BaseModel):
    content: str
    type: str  # 'text', 'image_description', 'complex_language'
    audience: Optional[str] = "general"

class ContentResponse(BaseModel):
    original: str
    processed: str
    suggestions: List[str]
    score: float
    type: str

# --- Endpoints ContentAgent ---

@router.post("/content/process", response_model=ContentResponse, tags=["Content Accessibility"])
async def process_content(request: ContentRequest):
    """
    Procesa texto para hacerlo accesible:
    - Lectura Fácil
    - Alt Text
    - Adaptación cognitiva
    """
    try:
        initial_state: ContentState = {
            "original_content": request.content,
            "content_type": request.type,
            "target_audience": request.audience,
            "processed_content": "",
            "suggestions": [],
            "confidence_score": 0.0,
            "errors": []
        }
        
        # Ejecutar agente
        result = await content_agent.ainvoke(initial_state)
        
        return ContentResponse(
            original=request.content,
            processed=result['processed_content'],
            suggestions=result['suggestions'],
            score=result['confidence_score'],
            type=request.type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando contenido: {str(e)}")

# --- Endpoints DocumentAgent ---

@router.post("/documents/analyze", tags=["Document Accessibility"])
async def analyze_document(
    file: UploadFile = File(..., description="Archivo PDF o Imagen a analizar")
):
    """
    Sube un documento (PDF, PNG, JPG) para:
    - Extracción de texto (OCR si es imagen)
    - Análisis estructural
    - Generación de tags
    - Conversión a HTML accesible
    - Validación de accesibilidad
    """
    
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido. Tipos: {allowed_types}")
    
    try:
        # Leer bytes
        contents = await file.read()
        
        # Determinar extensión
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "pdf"
        if file.content_type == "application/pdf":
            file_type = "pdf"
        elif file.content_type in ["image/png", "image/jpeg", "image/jpg"]:
            file_type = ext # png, jpg, etc
        
        # Procesar con el servicio
        result = await process_document_upload(contents, file.filename, file_type)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando documento: {str(e)}")

@router.get("/documents/{doc_id}/tags", tags=["Document Accessibility"])
async def get_document_tags(doc_id: str):
    """
    Obtiene las etiquetas generadas para un documento previamente analizado.
    (Placeholder: en producción esto consultaría la DB por el ID de auditoría de documento)
    """
    # Simulación de respuesta
    return {
        "document_id": doc_id,
        "tags": [
            {"role": "heading", "level": 1, "text": "Informe Anual"},
            {"role": "paragraph", "text": "Este es el resumen..."},
            {"role": "table", "rows": 5, "cols": 3}
        ],
        "status": "success"
    }
