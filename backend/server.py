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
        
        if request.diagram_type in ['flowchart', 'process']:
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
            rankdir = 'LR' if request.diagram_type == 'process' else 'TB'
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
        
        elif request.diagram_type == 'sequence':
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
        
        elif request.diagram_type == 'mindmap':
            # Extract topics and subtopics
            lines = [line.strip() for line in description.split('\n') if line.strip()]
            if not lines:
                lines = [part.strip() for part in description.split(',') if part.strip()]
            
            main_topic = lines[0] if lines else "Main Topic"
            subtopics = lines[1:] if len(lines) > 1 else ["Subtopic 1", "Subtopic 2"]
            
            code = f'''graph TD
    A[{main_topic[:30]}]'''
            
            for i, topic in enumerate(subtopics[:6]):  # Limit to 6 subtopics
                node_id = chr(66 + i)  # B, C, D, etc.
                code += f'\n    A --> {node_id}[{topic[:30]}]'
        
        elif request.diagram_type == 'organization':
            # Extract roles from description
            roles = []
            
            # Look for job titles or roles
            common_roles = ['CEO', 'CTO', 'CFO', 'COO', 'Manager', 'Director', 'Lead', 'Developer', 'Engineer', 
                          'Designer', 'Analyst', 'Accountant', 'HR', 'Sales', 'Marketing']
            
            for role in common_roles:
                if role.lower() in description.lower():
                    roles.append(role)
            
            # Extract custom roles (capitalized words)
            words = description.split()
            for word in words:
                if word[0].isupper() and len(word) > 3 and word not in roles:
                    roles.append(word)
            
            # If no roles found, use defaults
            if not roles:
                roles = ['CEO', 'Manager', 'Team Lead', 'Employee']
            
            # Build org chart with hierarchy
            nodes = []
            edges = []
            
            for i, role in enumerate(roles[:10]):  # Limit to 10 nodes
                node_id = f'node{i}'
                label = role.replace('"', '\\"')
                nodes.append(f'{node_id} [label="{label}"]')
                
                # Create hierarchy
                if i > 0:
                    parent_id = f'node{i // 2}'  # Simple tree structure
                    edges.append(f'{parent_id} -> {node_id}')
            
            code = f'''digraph G {{
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial", fontsize=12, shape=box, style="rounded,filled", fillcolor="#fce7f3", color="#db2777", fontcolor="#831843"]
  
  {chr(10).join(f"  {node}" for node in nodes)}
  
  {chr(10).join(f"  {edge}" for edge in edges)}
}}'''
        
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