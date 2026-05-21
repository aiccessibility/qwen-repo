"""
DocumentAgent: Análisis y Procesamiento de Documentos Accesibles.
Responsable de:
- OCR (Reconocimiento Óptico de Caracteres)
- Detección de estructura lógica (títulos, párrafos, tablas)
- Etiquetado automático (Tagging) para PDF/UA
- Conversión a formatos accesibles (HTML, PDF Tagged)
- Validación de conformidad documental
"""

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
import json
import base64
import os

# Configuración del LLM (usamos un modelo capaz de manejar visión si es necesario, o texto)
# Asumimos llama3 o similar. Para OCR puro usaremos pytesseract en el servicio, aquí la lógica.
llm = ChatOllama(
    model="llama3",
    temperature=0.2, # Baja temperatura para precisión estructural
    format="json"
)

class DocumentState(TypedDict):
    file_path: str
    file_type: str  # 'pdf', 'image', 'docx'
    raw_text: str   # Texto extraído (por OCR o extracción directa)
    structure: Dict[str, Any] # Estructura detectada
    tags: List[Dict[str, str]] # Lista de etiquetas sugeridas
    accessibility_issues: List[str]
    converted_content: Optional[str] # Contenido convertido (ej: HTML)
    validation_score: float
    errors: List[str]

def analyze_document_structure(state: DocumentState) -> DocumentState:
    """
    Analiza el texto crudo para inferir la estructura lógica del documento.
    Detecta títulos, listas, tablas y párrafos basándose en patrones.
    """
    prompt = f"""
    Actúa como un experto en estructuración de documentos y PDF/UA.
    
    Tienes el siguiente texto extraído de un documento:
    "--- INICIO TEXTO ---
    {state['raw_text'][:3000]} ... [truncado si es muy largo]
    --- FIN TEXTO ---
    
    Tu tarea es inferir la estructura lógica y devolver un JSON que represente el árbol del documento.
    
    ELEMENTOS A DETECTAR:
    - Títulos (h1, h2, h3...)
    - Párrafos (p)
    - Listas (ul, ol, li)
    - Tablas (table, tr, td) - intenta inferir filas/columnas si hay patrones de texto alineado.
    - Imágenes (si se mencionan como "Figura 1", etc.)
    
    Devuelve un JSON con esta estructura:
    {{
        "detected_elements": [
            {{"type": "h1", "content": "Texto del título", "level": 1}},
            {{"type": "p", "content": "Texto del párrafo"}}
        ],
        "has_logical_order": true/false,
        "suggestions": ["Sugerencias de mejora estructural"]
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
            
        result = json.loads(content.strip())
        
        return {
            **state,
            "structure": result,
            "accessibility_issues": [], # Se llenará en validación
            "errors": []
        }
    except Exception as e:
        return {
            **state,
            "structure": {},
            "accessibility_issues": ["No se pudo analizar la estructura."],
            "errors": [str(e)]
        }

def generate_tags(state: DocumentState) -> DocumentState:
    """
    Genera las etiquetas de accesibilidad necesarias (rol, nombre, valor).
    Esencial para PDF Tagged.
    """
    structure = state.get('structure', {})
    elements = structure.get('detected_elements', [])
    
    # Convertimos elementos a una descripción textual para el LLM
    elements_desc = "\n".join([f"- {el.get('type')}: {el.get('content')[:50]}" for el in elements])
    
    prompt = f"""
    Basado en la siguiente estructura detectada en un documento:
    {elements_desc}
    
    Genera una lista de etiquetas (tags) en formato JSON que cumplirían con PDF/UA o WCAG para documentos.
    Para cada elemento importante, define:
    - role: (ej: heading, paragraph, list, table, figure)
    - label: (texto alternativo o resumen si es una imagen/gráfico)
    - level: (si es heading, 1-6)
    
    Devuelve JSON:
    {{
        "tags": [
            {{"element_index": 0, "role": "heading", "label": "...", "level": 1}},
            ...
        ],
        "missing_alt_texts": ["Descripción de elementos que parecen imágenes sin texto alternativo"]
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
            
        result = json.loads(content.strip())
        
        issues = []
        if result.get('missing_alt_texts'):
            issues = [f"Falta texto alternativo para: {item}" for item in result['missing_alt_texts']]
            
        return {
            **state,
            "tags": result.get('tags', []),
            "accessibility_issues": state.get('accessibility_issues', []) + issues,
            "errors": []
        }
    except Exception as e:
        return {
            **state,
            "tags": [],
            "errors": [str(e)]
        }

def convert_to_accessible_html(state: DocumentState) -> DocumentState:
    """
    Convierte la estructura detectada a HTML semántico accesible.
    """
    structure = state.get('structure', {})
    elements = structure.get('detected_elements', [])
    
    # Pedimos al LLM que genere el HTML
    elements_json = json.dumps(elements, ensure_ascii=False)
    
    prompt = f"""
    Convierte la siguiente lista de elementos estructurales a HTML5 semántico y accesible.
    
    ELEMENTOS:
    {elements_json}
    
    REQUISITOS:
    - Usa etiquetas correctas (<h1>, <p>, <ul>, <table>, etc.).
    - Añade atributos ARIA si son necesarios (ej: role, aria-label).
    - Si hay tablas, usa <thead>, <tbody>, <th scope="col/row">.
    - Asegura que el orden de lectura sea lógico.
    
    Devuelve ÚNICAMENTE el código HTML dentro de un string en el JSON:
    {{
        "html_content": "<!DOCTYPE html><html>...</html>"
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
            
        result = json.loads(content.strip())
        
        return {
            **state,
            "converted_content": result.get('html_content', ''),
            "errors": []
        }
    except Exception as e:
        return {
            **state,
            "converted_content": '<p>Error en la conversión.</p>',
            "errors": [str(e)]
        }

def validate_document_accessibility(state: DocumentState) -> DocumentState:
    """
    Realiza una validación final y asigna un score de accesibilidad.
    """
    issues = state.get('accessibility_issues', [])
    tags = state.get('tags', [])
    has_structure = bool(state.get('structure', {}).get('detected_elements'))
    
    # Lógica simple de scoring
    score = 100.0
    
    if not has_structure:
        score -= 40
        issues.append("No se detectó estructura lógica.")
    
    if len(tags) == 0 and has_structure:
        score -= 30
        issues.append("Faltan etiquetas de rol/nombre.")
        
    # Penalización por problemas detectados
    score -= (len(issues) * 5)
    score = max(0, min(100, score)) # Clamp entre 0 y 100
    
    return {
        **state,
        "validation_score": score,
        "accessibility_issues": issues,
        "errors": state.get('errors', [])
    }

# Grafo del Agente
from langgraph.graph import StateGraph, END

def create_document_agent_graph():
    workflow = StateGraph(DocumentState)
    
    # Nodos
    workflow.add_node("analyze_structure", analyze_document_structure)
    workflow.add_node("generate_tags", generate_tags)
    workflow.add_node("convert_html", convert_to_accessible_html)
    workflow.add_node("validate", validate_document_accessibility)
    
    # Flujo secuencial
    workflow.set_entry_point("analyze_structure")
    workflow.add_edge("analyze_structure", "generate_tags")
    workflow.add_edge("generate_tags", "convert_html")
    workflow.add_edge("convert_html", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()

document_agent = create_document_agent_graph()
