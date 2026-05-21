"""
Servicios para el procesamiento de documentos.
Maneja la extracción de texto (OCR/PDF) y coordina con el DocumentAgent.
"""

import os
import tempfile
from typing import Dict, Any, List
import fitz  # PyMuPDF para PDFs
# import pytesseract # Descomentar si se instala tesseract en Docker
# from PIL import Image

from app.agents.document_agent import document_agent, DocumentState

def extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto de un archivo PDF."""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"Error leyendo PDF: {str(e)}")

def extract_text_from_image(file_path: str) -> str:
    """Extrae texto de una imagen usando OCR."""
    # Implementación básica. Requiere tesseract instalado en el contenedor.
    # Si no está disponible, retornamos un string vacío o lanzamos error controlado.
    try:
        # img = Image.open(file_path)
        # text = pytesseract.image_to_string(img, lang='spa')
        # return text
        return "[OCR No disponible en esta demo sin Tesseract instalado]"
    except Exception as e:
        return f"Error OCR: {str(e)}"

async def process_document_upload(file_bytes: bytes, filename: str, file_type: str) -> Dict[str, Any]:
    """
    Proceso principal:
    1. Guarda temporalmente el archivo.
    2. Extrae texto crudo.
    3. Ejecuta el DocumentAgent.
    4. Retorna resultados.
    """
    
    # 1. Guardar temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name
    
    try:
        # 2. Extracción de texto
        raw_text = ""
        if file_type == "pdf":
            raw_text = extract_text_from_pdf(tmp_path)
        elif file_type in ["png", "jpg", "jpeg"]:
            raw_text = extract_text_from_image(tmp_path)
        else:
            raw_text = "Formato no soportado para extracción directa."
            
        if not raw_text or len(raw_text.strip()) == 0:
            raw_text = "No se pudo extraer texto del documento."
        
        # 3. Ejecutar Agente
        initial_state: DocumentState = {
            "file_path": tmp_path,
            "file_type": file_type,
            "raw_text": raw_text,
            "structure": {},
            "tags": [],
            "accessibility_issues": [],
            "converted_content": None,
            "validation_score": 0.0,
            "errors": []
        }
        
        result = await document_agent.ainvoke(initial_state)
        
        # Limpieza
        os.unlink(tmp_path)
        
        return {
            "filename": filename,
            "type": file_type,
            "extracted_text_length": len(result['raw_text']),
            "structure": result['structure'],
            "tags": result['tags'],
            "issues": result['accessibility_issues'],
            "html_preview": result['converted_content'],
            "score": result['validation_score'],
            "status": "completed" if not result['errors'] else "failed",
            "errors": result['errors']
        }
        
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {
            "filename": filename,
            "status": "error",
            "error_message": str(e),
            "score": 0
        }
