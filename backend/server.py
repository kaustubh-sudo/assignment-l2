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
    Convert natural language description to diagram code using AI
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
        
        # Initialize OpenAI client
        client = OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY'),
            base_url="https://api.openai.com/v1"
        )
        
        # Create detailed prompts for each diagram type
        prompts = {
            'flowchart': f"""You are a GraphViz DOT code generator. Convert the following description into a flowchart using GraphViz DOT syntax.

IMPORTANT STYLING RULES:
- Always set bgcolor="transparent"
- For START/END nodes: shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"
- For PROCESS steps: shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"
- For DECISION nodes: shape=diamond, style=filled, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#78350f"
- All edges: color="#64748b"
- Set: node [fontname="Arial", fontsize=12]
- Use rankdir=TB for top-to-bottom flow

USER'S DESCRIPTION:
{request.description}

Generate ONLY the GraphViz DOT code. Do NOT include markdown code blocks or explanations. Start with "digraph G {{".""",
            
            'sequence': f"""You are a Mermaid sequence diagram generator. Convert the following description into a sequence diagram using Mermaid syntax.

USER'S DESCRIPTION:
{request.description}

Generate ONLY the Mermaid code. Start with "sequenceDiagram" and do NOT include markdown code blocks or explanations.""",
            
            'mindmap': f"""You are a Mermaid graph diagram generator. Convert the following description into a graph diagram using Mermaid syntax.

USER'S DESCRIPTION:
{request.description}

Generate ONLY the Mermaid code. Start with "graph TD" (for top-down) and do NOT include markdown code blocks or explanations.""",
            
            'process': f"""You are a GraphViz DOT code generator for process diagrams. Convert the following description into a process diagram using GraphViz DOT syntax.

IMPORTANT STYLING RULES:
- Always set bgcolor="transparent"
- For process steps: shape=box, style=filled, fillcolor="#ddd6fe", color="#7c3aed", fontcolor="#4c1d95"
- All edges: color="#64748b"
- Set: node [fontname="Arial", fontsize=12]
- Use rankdir=LR for left-to-right flow

USER'S DESCRIPTION:
{request.description}

Generate ONLY the GraphViz DOT code. Do NOT include markdown code blocks or explanations. Start with "digraph G {{".""",
            
            'organization': f"""You are a GraphViz DOT code generator for organization charts. Convert the following description into an org chart using GraphViz DOT syntax.

IMPORTANT STYLING RULES:
- Always set bgcolor="transparent"
- For all nodes: shape=box, style="rounded,filled", fillcolor="#fce7f3", color="#db2777", fontcolor="#831843"
- Set: node [fontname="Arial", fontsize=12]
- Use rankdir=TB for top-to-bottom hierarchy

USER'S DESCRIPTION:
{request.description}

Generate ONLY the GraphViz DOT code. Do NOT include markdown code blocks or explanations. Start with "digraph G {{"."""
        }
        
        prompt = prompts.get(request.diagram_type, prompts['flowchart'])
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert diagram code generator. You generate clean, valid diagram code based on user descriptions. You ALWAYS return ONLY the code without any markdown formatting, explanations, or code block markers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        # Extract and clean the generated code
        code = response.choices[0].message.content.strip()
        
        # Remove any markdown artifacts
        code = code.replace('```dot', '').replace('```graphviz', '').replace('```mermaid', '').replace('```', '').strip()
        
        # Remove any text before the actual code starts
        if request.diagram_type in ['flowchart', 'process', 'organization']:
            if 'digraph' in code:
                code = 'digraph' + code.split('digraph', 1)[1]
        elif request.diagram_type == 'sequence':
            if 'sequenceDiagram' in code:
                code = 'sequenceDiagram' + code.split('sequenceDiagram', 1)[1]
        elif request.diagram_type == 'mindmap':
            if 'graph' in code:
                code = 'graph' + code.split('graph', 1)[1]
        
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