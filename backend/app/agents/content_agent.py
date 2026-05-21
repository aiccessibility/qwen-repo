"""
ContentAgent: Generación y Adaptación de Contenido Accesible.
Responsable de:
- Reescritura en Lectura Fácil (Easy Read)
- Generación de Alt Text para imágenes
- Simplificación de lenguaje complejo
- Adaptación cognitiva de contenidos
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
import json
import re

# Configuración del LLM
llm = ChatOllama(
    model="llama3",  # O el modelo que tengas configurado
    temperature=0.7,
    format="json"
)

class ContentState(TypedDict):
    original_content: str
    content_type: str  # 'text', 'image_description', 'complex_language'
    target_audience: str  # 'cognitive_disability', 'general', 'children'
    processed_content: str
    suggestions: List[str]
    confidence_score: float
    errors: List[str]

def simplify_for_easy_read(state: ContentState) -> ContentState:
    """
    Transforma texto complejo a formato de 'Lectura Fácil'.
    Reglas: Frases cortas, voz activa, vocabulario simple, estructura clara.
    """
    prompt = f"""
    Actúa como un experto en accesibilidad cognitiva y Lectura Fácil (Easy Read).
    
    Tu tarea es reescribir el siguiente contenido para que sea comprensible por personas con discapacidad intelectual o dificultades de lectura.
    
    REGLAS ESTRICTAS:
    1. Usa frases cortas (máximo 15 palabras por frase).
    2. Usa voz activa siempre.
    3. Evita metáforas, ironías o jerga técnica.
    4. Una idea por párrafo.
    5. Usa vocabulario común y cotidiano.
    6. Si hay números complejos, explícalos o redondéalos.
    
    CONTENIDO ORIGINAL:
    "{state['original_content']}"
    
    Devuelve ÚNICAMENTE un JSON con esta estructura:
    {{
        "simplified_text": "El texto reescrito aquí...",
        "changes_made": ["lista de cambios principales realizados"],
        "readability_score": 0-100 (donde 100 es muy fácil)
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        # Limpieza básica si el LLM devuelve markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
            
        result = json.loads(content.strip())
        
        return {
            **state,
            "processed_content": result.get("simplified_text", state['original_content']),
            "suggestions": result.get("changes_made", []),
            "confidence_score": result.get("readability_score", 0) / 100,
            "errors": []
        }
    except Exception as e:
        return {
            **state,
            "processed_content": state['original_content'], # Fallback
            "suggestions": ["Error al procesar: No se pudo simplificar automáticamente."],
            "confidence_score": 0.0,
            "errors": [str(e)]
        }

def generate_alt_text(state: ContentState) -> ContentState:
    """
    Genera descripciones de texto alternativo (Alt Text) para imágenes.
    El input 'original_content' debe ser una descripción visual o contexto de la imagen.
    """
    prompt = f"""
    Actúa como un experto en accesibilidad web (WCAG 1.1.1).
    
    Tu tarea es escribir un texto alternativo (alt text) preciso y descriptivo para una imagen.
    
    CONTEXTO DE LA IMAGEN:
    "{state['original_content']}"
    
    REGLAS:
    1. Sé conciso (idealmente menos de 125 caracteres).
    2. Describe la acción o el propósito, no solo "imagen de...".
    3. Si es un gráfico, describe la tendencia principal.
    4. Si es decorativa, sugiere dejarlo vacío ("").
    5. No repitas el texto circundante.
    
    Devuelve ÚNICAMENTE un JSON:
    {{
        "alt_text": "La descripción generada...",
        "is_decorative": false,
        "rationale": "Por qué elegiste esta descripción..."
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
            "processed_content": result.get("alt_text", ""),
            "suggestions": [result.get("rationale", "")],
            "confidence_score": 0.9, # Asumimos alta confianza si no hay error
            "errors": []
        }
    except Exception as e:
        return {
            **state,
            "processed_content": "",
            "suggestions": [],
            "confidence_score": 0.0,
            "errors": [str(e)]
        }

def adapt_cognitive_load(state: ContentState) -> ContentState:
    """
    Adapta el contenido para reducir la carga cognitiva.
    Ideal para personas con TDAH, autismo o ansiedad.
    """
    prompt = f"""
    Actúa como especialista en diseño inclusivo y carga cognitiva.
    
    Analiza y adapta el siguiente texto para reducir la carga cognitiva:
    
    TEXTO:
    "{state['original_content']}"
    
    ACCIONES:
    1. Añade conectores lógicos claros (Primero, Luego, Finalmente).
    2. Rompe bloques de texto densos en listas con viñetas.
    3. Resalta las palabras clave o acciones importantes.
    4. Elimina información irrelevante o distractora.
    
    Devuelve un JSON:
    {{
        "adapted_text": "El texto adaptado...",
        "structure_improvements": ["lista de mejoras estructurales"],
        "score": 0-100
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
            "processed_content": result.get("adapted_text", state['original_content']),
            "suggestions": result.get("structure_improvements", []),
            "confidence_score": result.get("score", 0) / 100,
            "errors": []
        }
    except Exception as e:
        return {
            **state,
            "processed_content": state['original_content'],
            "suggestions": [],
            "confidence_score": 0.0,
            "errors": [str(e)]
        }

# Definición del Grafo del Agente
from langgraph.graph import StateGraph, END

def create_content_agent_graph():
    workflow = StateGraph(ContentState)
    
    # Nodos
    workflow.add_node("simplify_text", simplify_for_easy_read)
    workflow.add_node("generate_alt", generate_alt_text)
    workflow.add_node("adapt_cognitive", adapt_cognitive_load)
    
    # Lógica de enrutamiento simple basada en el tipo de contenido
    def route_content(state: ContentState):
        if state['content_type'] == 'image_description':
            return "generate_alt"
        elif state['content_type'] == 'complex_language':
            return "adapt_cognitive"
        else: # Default a texto general
            return "simplify_text"
    
    # Nodo de entrada condicional (simulado aquí llamando directamente según tipo)
    # En una implementación más compleja usaríamos ConditionalEdges
    
    # Para este ejemplo, añadimos todos pero el flujo lógico se decide antes de invocar
    # O usamos un nodo distribuidor. Aquí haremos un flujo lineal simple para demo:
    
    workflow.set_entry_point("simplify_text") # Por defecto
    
    # Nota: Para un enrutamiento real dinámico, necesitaríamos un nodo 'router'
    # Pero para mantenerlo simple y funcional, exponemos las funciones individualmente
    # o asumimos un flujo principal.
    
    workflow.add_edge("simplify_text", END)
    workflow.add_edge("generate_alt", END)
    workflow.add_edge("adapt_cognitive", END)
    
    return workflow.compile()

content_agent = create_content_agent_graph()
