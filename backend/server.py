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
        
        if request.diagram_type == 'graphviz':
            # Generate GraphViz diagram - flowchart/network style
            # Extract steps from description
            # Look for patterns like: "Step 1, Step 2" or "A -> B -> C" or "First X, then Y, finally Z"
            steps = []
            
            # Split by common delimiters
            parts = re.split(r'[,;→\n]|->|then|next|after that|finally', description, flags=re.IGNORECASE)
            
            for part in parts:
                part = part.strip()
                if part and len(part) > 2:
                    # Clean up common prefixes
                    part = re.sub(r'^(step\s+\d+:?\s*|•\s*|-\s*|\d+\.\s*)', '', part, flags=re.IGNORECASE)
                    if part:
                        steps.append(part.strip())
            
            # Generate flowchart
            rankdir = 'TB'
            nodes = []
            edges = []
            
            # Add start node
            nodes.append('start [label="Start", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]')
            
            prev_node = 'start'
            for i, step in enumerate(steps):
                node_id = f'step{i+1}'
                # Detect if it's a decision
                is_decision = any(word in step.lower() for word in ['if', '?', 'decide', 'choice', 'check', 'approve', 'reject'])
                
                if is_decision:
                    label = step.replace('"', '\\"')[:40]  # Limit label length
                    nodes.append(f'{node_id} [label="{label}", shape=diamond, style=filled, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#78350f"]')
                else:
                    label = step.replace('"', '\\"')[:40]
                    nodes.append(f'{node_id} [label="{label}", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]')
                
                edges.append(f'{prev_node} -> {node_id}')
                prev_node = node_id
            
            # Add end node
            nodes.append('end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]')
            edges.append(f'{prev_node} -> end')
            
            code = f'''digraph G {{
  bgcolor="transparent"
  rankdir={rankdir}
  node [fontname="Arial", fontsize=12]
  edge [fontname="Arial", fontsize=10, color="#64748b"]
  
  {chr(10).join(f"  {node}" for node in nodes)}
  
  {chr(10).join(f"  {edge}" for edge in edges)}
}}'''
        
        elif request.diagram_type == 'mermaid':
            # Extract participants and interactions
            participants = []
            interactions = []
            
            # Look for entities (capitalized words or quoted text)
            words = description.split()
            for word in words:
                if word[0].isupper() and len(word) > 2 and word not in participants:
                    participants.append(word)
            
            # If no participants found, use generic ones
            if not participants:
                participants = ['User', 'System', 'Database']
            
            # Extract interactions
            parts = re.split(r'[,;.\n]|then|next|after', description, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if part and len(part) > 5:
                    interactions.append(part[:50])
            
            # Build sequence diagram
            code = 'sequenceDiagram\n'
            for p in participants[:6]:  # Limit to 6 participants
                code += f'    participant {p}\n'
            code += '\n'
            
            # Generate interactions between participants
            for i, interaction in enumerate(interactions[:8]):  # Limit interactions
                sender = participants[i % len(participants)]
                receiver = participants[(i + 1) % len(participants)]
                code += f'    {sender}->>{receiver}: {interaction}\n'
        
        elif request.diagram_type == 'plantuml':
            # Generate PlantUML diagram
            # Extract entities/steps
            parts = re.split(r'[,;.\n]|then|next|after', description, flags=re.IGNORECASE)
            steps = [p.strip() for p in parts if p.strip() and len(p.strip()) > 2][:8]
            
            code = '@startuml\n'
            code += 'skinparam backgroundColor transparent\n'
            code += 'start\n'
            
            for step in steps:
                step = step.replace('"', '\\"')[:40]
                code += f':{step};\n'
            
            code += 'stop\n@enduml'
        
        elif request.diagram_type == 'blockdiag':
            # Generate BlockDiag diagram
            parts = re.split(r'[,;→\n]|->|then', description, flags=re.IGNORECASE)
            nodes = [p.strip().replace('"', '')[:20] for p in parts if p.strip() and len(p.strip()) > 2][:8]
            
            code = 'blockdiag {\n'
            for i, node in enumerate(nodes):
                if i > 0:
                    code += f'  {nodes[i-1].replace(" ", "_")} -> {node.replace(" ", "_")};\n'
            code += '}'
        
        elif request.diagram_type == 'd2':
            # Generate D2 diagram
            parts = re.split(r'[,;.\n]|then|next', description, flags=re.IGNORECASE)
            steps = [p.strip().replace('"', '')[:30] for p in parts if p.strip() and len(p.strip()) > 2][:8]
            
            code = ''
            for i, step in enumerate(steps):
                safe_id = f"step{i}"
                code += f'{safe_id}: {step}\n'
                if i > 0:
                    code += f'step{i-1} -> {safe_id}\n'
        
        elif request.diagram_type == 'ditaa':
            # Generate Ditaa ASCII art
            parts = re.split(r'[,;.\n]|then|next', description, flags=re.IGNORECASE)
            steps = [p.strip()[:15] for p in parts if p.strip() and len(p.strip()) > 2][:5]
            
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
            steps = [p.strip()[:12] for p in parts if p.strip() and len(p.strip()) > 2][:4]
            
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()