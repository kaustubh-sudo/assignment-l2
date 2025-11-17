from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone
from openai import OpenAI
from diagram_generator import generate_graphviz_advanced
from diagram_generators_enhanced import (
    generate_d2_diagram, 
    generate_blockdiag_diagram, 
    generate_graphviz_enhanced,
    generate_mermaid_diagram,
    generate_plantuml_diagram
)

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class DiagramGenerationRequest(BaseModel):
    description: str
    diagram_type: str

class DiagramGenerationResponse(BaseModel):
    code: str
    kroki_type: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

@api_router.post("/generate-diagram", response_model=DiagramGenerationResponse)
async def generate_diagram(request: DiagramGenerationRequest):
    """
    Convert natural language description to diagram code
    Uses intelligent parsing to extract steps/entities from description
    """
    try:
        import re
        
        # Kroki type is passed directly from frontend
        kroki_type = request.diagram_type
        description = request.description
        
        # Common filler words to filter out
        FILLER_WORDS = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'can', 'must', 'shall', 'it', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
            'more', 'most', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'now'
        }
        
        def clean_step(text):
            """Clean and extract meaningful content from a step"""
            # Remove common prefixes
            text = re.sub(r'^(step\s+\d+:?\s*|•\s*|-\s*|\d+\.\s*)', '', text, flags=re.IGNORECASE)
            
            # Split into words
            words = text.split()
            
            # Filter out filler words but keep meaningful phrases
            if len(words) <= 3:
                # For short phrases, only remove pure filler words
                cleaned_words = [w for w in words if w.lower() not in FILLER_WORDS or len(w) > 4]
            else:
                # For longer phrases, be more aggressive
                cleaned_words = []
                for w in words:
                    word_lower = w.lower()
                    # Keep capitalized words (likely proper nouns/important terms)
                    if w[0].isupper() or word_lower not in FILLER_WORDS:
                        cleaned_words.append(w)
            
            result = ' '.join(cleaned_words).strip()
            return result if result else text  # Fallback to original if nothing left
        
        if request.diagram_type == 'graphviz':
            # Use enhanced GraphViz generator with better parsing
            try:
                logger.info(f"Using enhanced GraphViz generator for description length: {len(description)}")
                code = generate_graphviz_enhanced(description)
                logger.info(f"Enhanced GraphViz generator succeeded, code length: {len(code)}")
                return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
            except Exception as e:
                logger.error(f"Enhanced generator failed, trying fallback: {str(e)}")
                # Fallback to original advanced generator
                try:
                    code = generate_graphviz_advanced(description)
                    logger.info(f"Fallback GraphViz generator succeeded, code length: {len(code)}")
                    return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
                except Exception as e2:
                    logger.error(f"All GraphViz generators failed: {str(e2)}")
            
            # Last resort simple fallback
            logger.info("Using simple GraphViz fallback")
            desc_lower = description.lower()
            
            # Detect layout preference
            rankdir = 'LR' if 'left to right' in desc_lower or 'horizontal' in desc_lower else 'TB'
            if 'top to bottom' in desc_lower or 'vertical' in desc_lower:
                rankdir = 'TB'
            
            # Initialize structures
            nodes = []
            edges = []
            node_counter = 0
            node_map = {}
            
            # Helper to create node ID
            def make_node_id(text):
                nonlocal node_counter
                # Use meaningful names from text
                words = text.split()[:2]
                base = ''.join(w.capitalize() for w in words if w.lower() not in FILLER_WORDS)
                # Remove invalid characters for GraphViz IDs
                base = base.replace(':', '').replace('-', '').replace('.', '').replace(',', '').replace('(', '').replace(')', '')
                if not base or len(base) < 2:
                    base = f'Node{node_counter}'
                node_counter += 1
                return base
            
            # Parse description into logical segments
            # Look for conditional patterns (if/else, either/or)
            conditional_pattern = r'\b(if|when|either)\b.*?\b(else|otherwise|or)\b.*?(?=[,;.]|$)'
            conditionals = list(re.finditer(conditional_pattern, description, re.IGNORECASE | re.DOTALL))
            
            # Extract all steps including conditional branches
            steps = []
            conditions = []
            
            if conditionals:
                # Handle conditional logic
                for match in conditionals:
                    full_text = match.group(0)
                    
                    # Split on else/or/otherwise
                    if_part = re.split(r'\b(else|otherwise|or)\b', full_text, maxsplit=1, flags=re.IGNORECASE)
                    
                    # Extract condition
                    condition_text = if_part[0].strip()
                    condition_text = re.sub(r'^(if|when|either)\s+', '', condition_text, flags=re.IGNORECASE)
                    condition_text = clean_step(condition_text)
                    
                    if len(if_part) >= 3:
                        # Extract yes and no branches
                        yes_branch = if_part[0]
                        yes_branch = re.sub(r'^(if|when|either)\s+', '', yes_branch, flags=re.IGNORECASE)
                        # Extract what happens in yes case
                        yes_actions = re.findall(r'\b(show|display|go to|proceed to|execute|perform)\s+(\w+(?:\s+\w+){0,2})', yes_branch, re.IGNORECASE)
                        
                        no_branch = if_part[2]
                        no_actions = re.findall(r'\b(show|display|go to|proceed to|execute|perform)\s+(\w+(?:\s+\w+){0,2})', no_branch, re.IGNORECASE)
                        
                        conditions.append({
                            'condition': condition_text,
                            'yes': [clean_step(action[1]) for action in yes_actions] if yes_actions else [clean_step(yes_branch)],
                            'no': [clean_step(action[1]) for action in no_actions] if no_actions else [clean_step(no_branch)]
                        })
            
            # Extract regular steps (not part of conditionals)
            # Split by delimiters
            parts = re.split(r'[,;]|\bthen\b|\bnext\b|\bafter\b', description, flags=re.IGNORECASE)
            
            for part in parts:
                part = part.strip()
                # Skip if this part is inside a conditional we already processed
                is_conditional_part = False
                for cond_match in conditionals:
                    if part in cond_match.group(0):
                        is_conditional_part = True
                        break
                
                if not is_conditional_part and part and len(part) > 3:
                    cleaned = clean_step(part)
                    if cleaned and len(cleaned) > 1:
                        # Don't add if it's just a fragment
                        if not any(cleaned.lower().startswith(frag) for frag in ['if', 'else', 'when', 'or']):
                            steps.append({'type': 'step', 'text': cleaned})
            
            # Add conditions as part of steps
            for cond in conditions:
                steps.append({'type': 'condition', 'data': cond})
            
            if not steps:
                steps = [{'type': 'step', 'text': 'Start Process'}, {'type': 'step', 'text': 'Complete'}]
            
            # Build nodes with sophisticated types
            for item in steps:
                if item['type'] == 'step':
                    step = item['text']
                    node_id = make_node_id(step)
                    step_lower = step.lower()
                    label = step.replace('"', '\\"')[:50]  # Limit label length
                    
                    # Determine node type and styling
                    if any(word in step_lower for word in ['submit', 'start', 'begin', 'input', 'request', 'login', 'logs in']):
                        shape = 'ellipse'
                        style = 'filled'
                        fillcolor = '#dcfce7'
                        color = '#16a34a'
                    elif any(word in step_lower for word in ['route', 'decide', 'check', 'validate', 'if', '?', 'credentials']):
                        shape = 'diamond'
                        style = 'filled'
                        fillcolor = '#fef3c7'
                        color = '#f59e0b'
                    elif any(word in step_lower for word in ['worker', 'parallel', 'process', 'executor']):
                        shape = 'folder'
                        style = 'filled'
                        fillcolor = '#ddd6fe'
                        color = '#7c3aed'
                    elif any(word in step_lower for word in ['queue', 'enqueue', 'buffer']):
                        shape = 'cylinder'
                        style = 'filled'
                        fillcolor = '#fce7f3'
                        color = '#db2777'
                    elif any(word in step_lower for word in ['error', 'fail', 'dlq', 'dead-letter']):
                        shape = 'box'
                        style = 'filled,rounded'
                        fillcolor = '#fee2e2'
                        color = '#dc2626'
                    elif any(word in step_lower for word in ['alert', 'notify', 'webhook']):
                        shape = 'box'
                        style = 'filled,rounded'
                        fillcolor = '#fff7ed'
                        color = '#ea580c'
                    elif any(word in step_lower for word in ['archive', 'store', 'save', 's3', 'database']):
                        shape = 'box3d'
                        style = 'filled'
                        fillcolor = '#e0e7ff'
                        color = '#4f46e5'
                    elif any(word in step_lower for word in ['dashboard', 'page', 'screen', 'view']):
                        shape = 'box'
                        style = 'filled,rounded'
                        fillcolor = '#e0f2fe'
                        color = '#0284c7'
                    elif any(word in step_lower for word in ['logout', 'end', 'exit', 'complete']):
                        shape = 'ellipse'
                        style = 'filled'
                        fillcolor = '#dcfce7'
                        color = '#16a34a'
                    else:
                        shape = 'box'
                        style = 'filled,rounded'
                        fillcolor = '#e0f2fe'
                        color = '#0284c7'
                    
                    nodes.append(f'{node_id} [label="{label}", shape={shape}, style="{style}", fillcolor="{fillcolor}", color="{color}"]')
                    node_map[step] = node_id
                    
                elif item['type'] == 'condition':
                    cond_data = item['data']
                    # Create decision node
                    decision_id = make_node_id(cond_data['condition'])
                    decision_label = cond_data['condition'].replace('"', '\\"')[:40]
                    nodes.append(f'{decision_id} [label="{decision_label}?", shape=diamond, style="filled", fillcolor="#fef3c7", color="#f59e0b"]')
                    node_map[f"condition_{decision_id}"] = decision_id
                    
                    # Create yes branch nodes
                    for yes_step in cond_data['yes']:
                        yes_id = make_node_id(yes_step)
                        yes_label = yes_step.replace('"', '\\"')[:50]
                        nodes.append(f'{yes_id} [label="{yes_label}", shape=box, style="filled,rounded", fillcolor="#dcfce7", color="#16a34a"]')
                        node_map[yes_step] = yes_id
                        edges.append(f'{decision_id} -> {yes_id} [label="Yes", color="#16a34a"]')
                    
                    # Create no branch nodes
                    for no_step in cond_data['no']:
                        no_id = make_node_id(no_step)
                        no_label = no_step.replace('"', '\\"')[:50]
                        nodes.append(f'{no_id} [label="{no_label}", shape=box, style="filled,rounded", fillcolor="#fee2e2", color="#dc2626"]')
                        node_map[no_step] = no_id
                        edges.append(f'{decision_id} -> {no_id} [label="No", color="#dc2626"]')
            
            # Build sequential edges for regular steps
            prev_step_node = None
            for item in steps:
                if item['type'] == 'step':
                    step = item['text']
                    current_node = node_map.get(step)
                    
                    if prev_step_node and current_node and prev_step_node != current_node:
                        # Check if this edge already exists
                        edge_exists = any(f'{prev_step_node} -> {current_node}' in e for e in edges)
                        if not edge_exists:
                            edges.append(f'{prev_step_node} -> {current_node} [color="#64748b"]')
                    
                    prev_step_node = current_node
                elif item['type'] == 'condition':
                    # Connect previous node to decision
                    decision_id = node_map.get(f"condition_{make_node_id(item['data']['condition'])}")
                    if prev_step_node and decision_id:
                        edges.append(f'{prev_step_node} -> {decision_id} [color="#64748b"]')
            
            # Generate final code
            code = f'''digraph ComplexFlow {{
  bgcolor="transparent"
  rankdir={rankdir}
  node [fontname="Arial", fontsize=11]
  edge [fontname="Arial", fontsize=9]
  
  {chr(10).join(f"  {node}" for node in nodes)}
  
  {chr(10).join(f"  {edge}" for edge in edges)}
}}'''
        
        elif request.diagram_type == 'mermaid':
            # Generate Mermaid flowchart (not sequence diagram)
            # Detect if it's better as flowchart or sequence
            desc_lower = description.lower()
            
            # Check for sequence diagram indicators
            is_sequence = any(word in desc_lower for word in ['participant', 'actor', 'request', 'response', 'message', 'call', 'reply'])
            
            if is_sequence:
                # Generate sequence diagram
                participants = []
                interactions = []
                
                # Look for entities (capitalized words)
                words = description.split()
                for word in words:
                    word_clean = word.strip('.,;:!?')
                    if word_clean and len(word_clean) > 2 and word_clean[0].isupper() and word_clean.lower() not in FILLER_WORDS:
                        if word_clean not in participants:
                            participants.append(word_clean)
                
                if not participants:
                    participants = ['User', 'System', 'Database']
                
                # Extract interactions
                parts = re.split(r'[,;.\n]|then|next|after', description, flags=re.IGNORECASE)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 5:
                        cleaned = clean_step(part)
                        if cleaned:
                            interactions.append(cleaned[:50])
                
                # Build sequence diagram
                code = 'sequenceDiagram\n'
                for p in participants[:6]:
                    code += f'    participant {p}\n'
                code += '\n'
                
                for i, interaction in enumerate(interactions[:8]):
                    sender = participants[i % len(participants)]
                    receiver = participants[(i + 1) % len(participants)]
                    code += f'    {sender}->>{receiver}: {interaction}\n'
            else:
                # Generate flowchart with conditional logic
                code = 'flowchart TD\n'
                
                # Parse steps and conditions similar to GraphViz
                parts = re.split(r'[,;]|\bthen\b|\bnext\b', description, flags=re.IGNORECASE)
                node_id = ord('A')
                nodes = []
                edges = []
                prev_node = None
                
                # Look for conditionals
                conditional_match = re.search(r'\b(if|when)\s+(.+?)\s+(else|otherwise)\s+(.+?)(?:[,;.]|$)', description, re.IGNORECASE)
                
                for part in parts:
                    part = part.strip()
                    
                    # Skip if part of conditional
                    if conditional_match and part in conditional_match.group(0):
                        continue
                    
                    if part and len(part) > 3:
                        cleaned = clean_step(part)
                        if cleaned and len(cleaned) > 1:
                            current = chr(node_id)
                            node_id += 1
                            
                            # Determine node type
                            if 'login' in cleaned.lower() or 'start' in cleaned.lower():
                                nodes.append(f'    {current}(["{cleaned}"])')
                            elif 'validate' in cleaned.lower() or 'check' in cleaned.lower():
                                nodes.append(f'    {current}{{{{{cleaned}}}}}')  # Diamond
                            elif 'logout' in cleaned.lower() or 'end' in cleaned.lower():
                                nodes.append(f'    {current}(["{cleaned}"])')
                            else:
                                nodes.append(f'    {current}["{cleaned}"]')
                            
                            if prev_node:
                                edges.append(f'    {prev_node} --> {current}')
                            prev_node = current
                
                # Add conditional if found
                if conditional_match:
                    condition = clean_step(conditional_match.group(2))
                    yes_action = clean_step(conditional_match.group(4))
                    no_action = yes_action  # Extract from else part
                    
                    # Try to find the actual else action
                    else_text = conditional_match.group(0).split('else')[1] if 'else' in conditional_match.group(0) else conditional_match.group(0).split('otherwise')[1]
                    else_action = clean_step(else_text)
                    
                    decision_node = chr(node_id)
                    node_id += 1
                    yes_node = chr(node_id)
                    node_id += 1
                    no_node = chr(node_id)
                    
                    nodes.append(f'    {decision_node}{{{{{condition}?}}}}')
                    nodes.append(f'    {yes_node}["{yes_action}"]')
                    nodes.append(f'    {no_node}["{else_action}"]')
                    
                    if prev_node:
                        edges.append(f'    {prev_node} --> {decision_node}')
                    edges.append(f'    {decision_node} -->|Yes| {yes_node}')
                    edges.append(f'    {decision_node} -->|No| {no_node}')
                
                code += '\n'.join(nodes) + '\n' + '\n'.join(edges)
        
        elif request.diagram_type == 'excalidraw':
            # Generate Excalidraw JSON format
            import json
            
            # Extract steps
            parts = re.split(r'[,;.\n]|then|next|after', description, flags=re.IGNORECASE)
            steps = []
            for p in parts:
                p = p.strip()
                if p and len(p) > 2:
                    cleaned = clean_step(p)
                    if cleaned:
                        steps.append(cleaned.replace('"', '')[:30])
            steps = steps[:6]
            
            # Build Excalidraw elements
            elements = []
            y_pos = 100
            
            for i, step in enumerate(steps):
                # Add rectangle element
                element_id = f"element-{i}"
                elements.append({
                    "id": element_id,
                    "type": "rectangle",
                    "x": 100,
                    "y": y_pos,
                    "width": 200,
                    "height": 60,
                    "strokeColor": "#0284c7",
                    "backgroundColor": "#e0f2fe",
                    "fillStyle": "hachure",
                    "strokeWidth": 2,
                    "roughness": 1,
                    "opacity": 100
                })
                
                # Add text element
                elements.append({
                    "id": f"text-{i}",
                    "type": "text",
                    "x": 110,
                    "y": y_pos + 20,
                    "width": 180,
                    "height": 20,
                    "text": step,
                    "fontSize": 16,
                    "fontFamily": 1,
                    "textAlign": "center",
                    "verticalAlign": "middle"
                })
                
                # Add arrow to next element
                if i < len(steps) - 1:
                    elements.append({
                        "id": f"arrow-{i}",
                        "type": "arrow",
                        "x": 200,
                        "y": y_pos + 60,
                        "width": 0,
                        "height": 40,
                        "points": [[0, 0], [0, 40]],
                        "strokeColor": "#64748b",
                        "backgroundColor": "transparent",
                        "fillStyle": "solid",
                        "strokeWidth": 2,
                        "roughness": 1
                    })
                
                y_pos += 120
            
            # Create Excalidraw JSON
            excalidraw_data = {
                "type": "excalidraw",
                "version": 2,
                "source": "diagram-maker",
                "elements": elements,
                "appState": {
                    "viewBackgroundColor": "#ffffff"
                }
            }
            
            code = json.dumps(excalidraw_data)
        
        elif request.diagram_type == 'plantuml':
            # Generate sophisticated PlantUML diagram
            desc_lower = description.lower()
            
            parts = re.split(r'[,;.\n]|then|next|after', description, flags=re.IGNORECASE)
            steps = []
            for p in parts:
                p = p.strip()
                if p and len(p) > 2:
                    cleaned = clean_step(p)
                    if cleaned:
                        steps.append(cleaned)
            
            code = '@startuml\n'
            code += 'skinparam backgroundColor transparent\n'
            code += 'skinparam activity {\n'
            code += '  BackgroundColor #e0f2fe\n'
            code += '  BorderColor #0284c7\n'
            code += '  DiamondBackgroundColor #fef3c7\n'
            code += '  DiamondBorderColor #f59e0b\n'
            code += '}\n\n'
            code += 'start\n\n'
            
            for i, step in enumerate(steps):
                step_lower = step.lower()
                step_text = step.replace('"', '\\"')
                
                # Detect decision points
                if any(word in step_lower for word in ['route', 'decide', 'check', 'if', '?', 'either', 'or']):
                    # Create a decision diamond
                    code += f'if ({step_text}?) then (yes)\n'
                    if i < len(steps) - 1:
                        code += f'  :{steps[i+1]};\n'
                    code += 'else (no)\n'
                    code += '  :Alternative path;\n'
                    code += 'endif\n\n'
                # Detect parallel/fork points
                elif any(word in step_lower for word in ['parallel', 'concurrent', 'fork', 'split']):
                    code += f'fork\n'
                    code += f'  :{step_text};\n'
                    code += 'fork again\n'
                    code += '  :Parallel task 2;\n'
                    code += 'end fork\n\n'
                # Detect error handling
                elif any(word in step_lower for word in ['retry', 'error', 'fail']):
                    code += f':{step_text};\n'
                    code += 'note right\n'
                    code += '  Handle errors with\n'
                    code += '  exponential backoff\n'
                    code += 'end note\n\n'
                # Regular activity
                else:
                    # Add multiline support for long descriptions
                    if len(step_text) > 35:
                        parts = [step_text[i:i+35] for i in range(0, len(step_text), 35)]
                        formatted = '\\n'.join(parts[:2])
                        code += f':{formatted};\n'
                    else:
                        code += f':{step_text};\n'
            
            code += '\nstop\n@enduml'
        
        elif request.diagram_type == 'blockdiag':
            # Use enhanced BlockDiag generator with colors, groups, and styling
            try:
                logger.info(f"Using enhanced BlockDiag generator for description length: {len(description)}")
                code = generate_blockdiag_diagram(description)
                logger.info(f"Enhanced BlockDiag generator succeeded, code length: {len(code)}")
            except Exception as e:
                logger.error(f"Enhanced BlockDiag generator failed: {str(e)}, using simple fallback")
                # Simple fallback
                parts = re.split(r'[,;→\n]|->|then', description, flags=re.IGNORECASE)
                nodes = []
                for p in parts:
                    p = p.strip()
                    if p and len(p) > 2:
                        cleaned = clean_step(p).replace('"', '')
                        if cleaned:
                            nodes.append(cleaned[:20])
                nodes = nodes[:8]
                
                code = 'blockdiag {\n'
                for i, node in enumerate(nodes):
                    if i > 0:
                        code += f'  {nodes[i-1].replace(" ", "_")} -> {node.replace(" ", "_")};\n'
                code += '}'
        
        elif request.diagram_type == 'd2':
            # Use enhanced D2 generator with classes, shapes, and conditionals
            try:
                logger.info(f"Using enhanced D2 generator for description length: {len(description)}")
                code = generate_d2_diagram(description)
                logger.info(f"Enhanced D2 generator succeeded, code length: {len(code)}")
            except Exception as e:
                logger.error(f"Enhanced D2 generator failed: {str(e)}, using simple fallback")
                # Simple fallback
                parts = re.split(r'[,;.\n]|then|next', description, flags=re.IGNORECASE)
                steps = []
                for p in parts:
                    p = p.strip()
                    if p and len(p) > 2:
                        cleaned = clean_step(p).replace('"', '')
                        if cleaned:
                            steps.append(cleaned[:30])
                steps = steps[:8]
                
                code = 'direction: down\n\n'
                for i, step in enumerate(steps):
                    safe_id = f"step{i}"
                    code += f'{safe_id}: {step} {{\n'
                    code += f'  style: {{\n'
                    code += f'    fill: "#e0f2fe"\n'
                    code += f'    stroke: "#0284c7"\n'
                    code += f'    stroke-width: 2\n'
                    code += f'  }}\n'
                    code += f'}}\n'
                    if i > 0:
                        code += f'step{i-1} -> {safe_id}\n'
        
        elif request.diagram_type == 'ditaa':
            # Generate Ditaa ASCII art
            parts = re.split(r'[,;.\n]|then|next', description, flags=re.IGNORECASE)
            steps = []
            for p in parts:
                p = p.strip()
                if p and len(p) > 2:
                    cleaned = clean_step(p)
                    if cleaned:
                        steps.append(cleaned[:15])
            steps = steps[:5]
            
            code = '+' + '-' * 20 + '+\n'
            for step in steps:
                code += f'| {step:<18} |\n'
                code += '+' + '-' * 20 + '+\n'
                if step != steps[-1]:
                    code += '       |\n'
                    code += '       v\n'
        
        elif request.diagram_type == 'structurizr':
            # Generate Structurizr C4 model
            code = '''workspace {
    model {
        user = person "User"
        system = softwareSystem "System" {
            webapp = container "Web Application"
            database = container "Database"
        }
        
        user -> webapp "Uses"
        webapp -> database "Reads/Writes"
    }
    
    views {
        systemContext system {
            include *
            autolayout lr
        }
    }
}'''
        
        elif request.diagram_type == 'svgbob':
            # Generate Svgbob ASCII diagram
            parts = re.split(r'[,;.\n]|then|next', description, flags=re.IGNORECASE)
            steps = []
            for p in parts:
                p = p.strip()
                if p and len(p) > 2:
                    cleaned = clean_step(p)
                    if cleaned:
                        steps.append(cleaned[:12])
            steps = steps[:4]
            
            code = ''
            for i, step in enumerate(steps):
                code += f'  .-------.\n'
                code += f'  | {step:<5} |\n'
                code += f'  \'-------\'\n'
                if i < len(steps) - 1:
                    code += '      |\n'
                    code += '      v\n'
        
        elif request.diagram_type == 'symbolator':
            # Generate Symbolator timing diagram
            # This is a specialized format for hardware
            code = '''-- Example timing diagram
signal clk : std_logic;
signal data : std_logic_vector(7 downto 0);
signal valid : std_logic;

clk <= '0', '1' after 10 ns, '0' after 20 ns;
data <= x"AA", x"BB" after 15 ns;
valid <= '0', '1' after 5 ns, '0' after 25 ns;'''
        
        else:
            # Default fallback - simple diagram
            code = description
        
        logger.info(f"Generated diagram code for type: {request.diagram_type}")
        
        return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
        
    except Exception as e:
        logger.error(f"Error generating diagram: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate diagram: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()