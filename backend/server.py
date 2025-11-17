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
    This is a smart template-based approach that parses the description
    """
    try:
        # Map user-friendly diagram type to Kroki type
        kroki_type_mapping = {
            'flowchart': 'graphviz',
            'sequence': 'mermaid',
            'mindmap': 'mermaid',
            'process': 'graphviz',
            'organization': 'graphviz',
        }
        
        kroki_type = kroki_type_mapping.get(request.diagram_type, 'graphviz')
        desc_lower = request.description.lower()
        
        # Generate code based on diagram type and description keywords
        if request.diagram_type == 'flowchart' or request.diagram_type == 'process':
            # Parse for workflow keywords
            rankdir = 'LR' if request.diagram_type == 'process' else 'TB'
            nodes = []
            edges = []
            
            # Always include start and end
            nodes.append('start [label="Start", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]')
            
            # Detect workflow steps from description
            if 'review' in desc_lower or 'check' in desc_lower:
                nodes.append('review [label="Review Document", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]')
                edges.append('start -> review')
                last_node = 'review'
            else:
                last_node = 'start'
            
            if 'approve' in desc_lower or 'decision' in desc_lower or 'reject' in desc_lower:
                nodes.append('decision [label="Approve?", shape=diamond, style=filled, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#78350f"]')
                edges.append(f'{last_node} -> decision')
                
                if 'complete' in desc_lower or 'finish' in desc_lower:
                    nodes.append('complete [label="Complete", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]')
                    edges.append('decision -> complete [label="Approved", color="#64748b"]')
                    edges.append(f'decision -> {last_node} [label="Rejected", color="#64748b"]')
                    nodes.append('end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]')
                    edges.append('complete -> end')
                else:
                    nodes.append('end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]')
                    edges.append('decision -> end [label="Yes", color="#64748b"]')
                    edges.append(f'decision -> {last_node} [label="No", color="#64748b"]')
            else:
                nodes.append('end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]')
                edges.append(f'{last_node} -> end')
            
            code = f'''digraph G {{
  bgcolor="transparent"
  rankdir={rankdir}
  node [fontname="Arial", fontsize=12]
  edge [fontname="Arial", fontsize=10, color="#64748b"]
  
  {chr(10).join(f"  {node}" for node in nodes)}
  
  {chr(10).join(f"  {edge}" for edge in edges)}
}}'''
        
        elif request.diagram_type == 'sequence':
            # Generate sequence diagram
            code = '''sequenceDiagram
    participant User
    participant System
    participant Database
    
    User->>System: Send Request
    System->>Database: Query Data
    Database-->>System: Return Results
    System-->>User: Display Response'''
        
        elif request.diagram_type == 'mindmap':
            # Generate mindmap as graph
            code = '''graph TD
    A[Main Topic] --> B[Subtopic 1]
    A --> C[Subtopic 2]
    A --> D[Subtopic 3]
    B --> E[Detail 1]
    B --> F[Detail 2]
    C --> G[Detail 3]
    D --> H[Detail 4]'''
        
        elif request.diagram_type == 'organization':
            # Generate org chart
            code = '''digraph G {
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial", fontsize=12, shape=box, style="rounded,filled", fillcolor="#fce7f3", color="#db2777", fontcolor="#831843"]
  
  CEO [label="CEO"]
  CTO [label="CTO"]
  CFO [label="CFO"]
  Dev1 [label="Developer 1"]
  Dev2 [label="Developer 2"]
  Acc1 [label="Accountant"]
  
  CEO -> CTO
  CEO -> CFO
  CTO -> Dev1
  CTO -> Dev2
  CFO -> Acc1
}'''
        else:
            # Default simple flowchart
            code = '''digraph G {
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial", fontsize=12]
  
  start [label="Start", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]
  process [label="Process", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]
  end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]
  
  start -> process [color="#64748b"]
  process -> end [color="#64748b"]
}'''
        
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