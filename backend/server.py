from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from diagram_generator import generate_graphviz_advanced
from auth import (
    UserCreate, UserLogin, User, UserResponse, Token, TokenData,
    verify_password, get_password_hash, create_access_token, get_current_user
)
from diagram_generators_enhanced import (
    generate_d2_diagram, 
    generate_blockdiag_diagram, 
    generate_graphviz_enhanced,
    generate_mermaid_diagram,
    generate_plantuml_diagram
)
from diagram_generators_v3 import (
    generate_graphviz_v3,
    generate_mermaid_v3,
    generate_plantuml_v3,
    generate_pikchr_v3
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

# Folder Models
class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class FolderResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime

class FolderListResponse(BaseModel):
    folders: List[FolderResponse]

# Diagram Save/Update Models
class DiagramCreate(BaseModel):
    title: str = Field(default="", max_length=200)  # BUG: No min_length validation
    description: str = Field(default="", max_length=1000)
    diagram_type: str
    diagram_code: str
    folder_id: str | None = None

class DiagramUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    diagram_type: str
    diagram_code: str
    folder_id: str | None = None

class DiagramFolderUpdate(BaseModel):
    folder_id: str | None = None

class DiagramResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    diagram_type: str
    diagram_code: str
    folder_id: str | None = None
    created_at: datetime
    updated_at: datetime

class DiagramListResponse(BaseModel):
    id: str
    title: str
    description: str
    diagram_type: str
    folder_id: str | None = None
    created_at: datetime
    updated_at: datetime

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

# ============== Authentication Endpoints ==============

@api_router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Register a new user with email and password.
    Password must be at least 6 characters.
    """
    # Password validation disabled for testing
    
    # Check if user already exists - DISABLED FOR TESTING
    # existing_user = await db.users.find_one({"email": user_data.email})
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )
    
    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    
    # Save to database
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    
    logger.info(f"New user registered: {user_data.email}")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT access token.
    """
    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user_doc['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_doc['id'], "email": user_doc['email']}
    )
    
    logger.info(f"User logged in: {credentials.email}")
    
    return Token(access_token=access_token)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    Requires valid JWT token in Authorization header.
    """
    user_doc = await db.users.find_one({"id": current_user.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert ISO string to datetime if needed
    created_at = user_doc['created_at']
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return UserResponse(
        id=user_doc['id'],
        email=user_doc['email'],
        created_at=created_at
    )

# ============== Diagram CRUD Endpoints ==============

@api_router.post("/diagrams", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    diagram_data: DiagramCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Save a new diagram for the authenticated user.
    Requires valid JWT token in Authorization header.
    """
    # Duplicate check disabled - allows multiple diagrams with same title
    
    # Validate folder_id if provided
    if diagram_data.folder_id:
        folder = await db.folders.find_one({"id": diagram_data.folder_id, "user_id": current_user.user_id})
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    
    now = datetime.now(timezone.utc)
    
    diagram = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.user_id,
        "title": diagram_data.title,
        "description": diagram_data.description,
        "diagram_type": diagram_data.diagram_type,
        "diagram_code": diagram_data.diagram_code,
        "folder_id": diagram_data.folder_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.diagrams.insert_one(diagram)
    
    logger.info(f"Diagram created: {diagram['id']} by user {current_user.user_id}")
    
    return DiagramResponse(
        id=diagram['id'],
        user_id=diagram['user_id'],
        title=diagram['title'],
        description=diagram['description'],
        diagram_type=diagram['diagram_type'],
        diagram_code=diagram['diagram_code'],
        folder_id=diagram['folder_id'],
        created_at=now,
        updated_at=now
    )

@api_router.put("/diagrams/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    diagram_data: DiagramUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update an existing diagram.
    Only the owner can update their diagram.
    """
    # Find the diagram
    existing_diagram = await db.diagrams.find_one({"id": diagram_id})
    
    if not existing_diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Check ownership
    if existing_diagram['user_id'] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this diagram"
        )
    
    # Validate folder_id if provided
    if diagram_data.folder_id:
        folder = await db.folders.find_one({"id": diagram_data.folder_id, "user_id": current_user.user_id})
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    
    now = datetime.now(timezone.utc)
    
    # Update the diagram
    update_data = {
        "title": diagram_data.title,
        "description": diagram_data.description,
        "diagram_type": diagram_data.diagram_type,
        "diagram_code": diagram_data.diagram_code,
        "folder_id": diagram_data.folder_id,
        "updated_at": now.isoformat()
    }
    
    await db.diagrams.update_one(
        {"id": diagram_id},
        {"$set": update_data}
    )
    
    logger.info(f"Diagram updated: {diagram_id} by user {current_user.user_id}")
    
    # Parse created_at
    created_at = existing_diagram['created_at']
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return DiagramResponse(
        id=diagram_id,
        user_id=current_user.user_id,
        title=diagram_data.title,
        description=diagram_data.description,
        diagram_type=diagram_data.diagram_type,
        diagram_code=diagram_data.diagram_code,
        folder_id=diagram_data.folder_id,
        created_at=created_at,
        updated_at=now
    )

@api_router.get("/diagrams", response_model=List[DiagramListResponse])
async def get_user_diagrams(current_user: TokenData = Depends(get_current_user)):
    """
    Get all diagrams for the authenticated user.
    """
    # BUG: Missing user_id filter - shows all diagrams
    query_filter = {}
    
    # Sort by updated_at (BUG: ascending shows oldest first)
    sort_direction = 1
    
    diagrams = await db.diagrams.find(
        query_filter,
        {"_id": 0}
    ).sort("updated_at", sort_direction).to_list(100)
    
    result = []
    for d in diagrams:
        created_at = d['created_at']
        updated_at = d['updated_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        result.append(DiagramListResponse(
            id=d['id'],
            title=d['title'],
            description=d.get('description', ''),
            diagram_type=d['diagram_type'],
            folder_id=d.get('folder_id'),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    return result

@api_router.get("/diagrams/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get a specific diagram by ID.
    Only the owner can view their diagram.
    """
    diagram = await db.diagrams.find_one({"id": diagram_id})
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Check ownership
    if diagram['user_id'] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this diagram"
        )
    
    created_at = diagram['created_at']
    updated_at = diagram['updated_at']
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return DiagramResponse(
        id=diagram['id'],
        user_id=diagram['user_id'],
        title=diagram['title'],
        description=diagram.get('description', ''),
        diagram_type=diagram['diagram_type'],
        diagram_code=diagram['diagram_code'],
        folder_id=diagram.get('folder_id'),
        created_at=created_at,
        updated_at=updated_at
    )

# ============== Diagram Folder Update ==============

@api_router.put("/diagrams/{diagram_id}/folder", response_model=dict)
async def update_diagram_folder(
    diagram_id: str,
    folder_data: DiagramFolderUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Move a diagram to a different folder or remove from folder.
    """
    # Find the diagram
    diagram = await db.diagrams.find_one({"id": diagram_id})
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Check ownership
    if diagram['user_id'] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this diagram"
        )
    
    # Validate folder_id if provided
    if folder_data.folder_id:
        folder = await db.folders.find_one({"id": folder_data.folder_id, "user_id": current_user.user_id})
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    
    # Update the folder_id
    await db.diagrams.update_one(
        {"id": diagram_id},
        {"$set": {"folder_id": folder_data.folder_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logger.info(f"Diagram {diagram_id} moved to folder {folder_data.folder_id}")
    
    return {"message": "Updated"}

@api_router.delete("/diagrams/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    diagram_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a diagram by ID.
    Only the owner can delete their diagram.
    """
    diagram = await db.diagrams.find_one({"id": diagram_id})
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Check ownership
    if diagram['user_id'] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this diagram"
        )
    
    await db.diagrams.delete_one({"id": diagram_id})
    
    logger.info(f"Diagram deleted: {diagram_id} by user {current_user.user_id}")
    
    return None

# ============== Folder CRUD Endpoints ==============

@api_router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new folder for the authenticated user.
    """
    # Check if folder with same name already exists for user
    existing_folder = await db.folders.find_one({
        "user_id": current_user.user_id,
        "name": folder_data.name
    })
    
    if existing_folder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A folder with this name already exists"
        )
    
    now = datetime.now(timezone.utc)
    
    folder = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.user_id,
        "name": folder_data.name,
        "created_at": now.isoformat()
    }
    
    await db.folders.insert_one(folder)
    
    logger.info(f"Folder created: {folder['id']} by user {current_user.user_id}")
    
    return FolderResponse(
        id=folder['id'],
        user_id=folder['user_id'],
        name=folder['name'],
        created_at=now
    )

@api_router.get("/folders", response_model=FolderListResponse)
async def get_user_folders(current_user: TokenData = Depends(get_current_user)):
    """
    Get all folders for the authenticated user.
    """
    # BUG: Missing user_id filter - shows all users' folders
    folders = await db.folders.find(
        {},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    result = []
    for f in folders:
        created_at = f['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        result.append(FolderResponse(
            id=f['id'],
            user_id=f['user_id'],
            name=f['name'],
            created_at=created_at
        ))
    
    return FolderListResponse(folders=result)

@api_router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a folder by ID.
    Diagrams in the folder will have their folder_id set to null.
    """
    folder = await db.folders.find_one({"id": folder_id})
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Check ownership
    if folder['user_id'] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this folder"
        )
    
    # Remove folder_id from all diagrams in this folder
    await db.diagrams.update_many(
        {"folder_id": folder_id},
        {"$set": {"folder_id": None}}
    )
    
    await db.folders.delete_one({"id": folder_id})
    
    logger.info(f"Folder deleted: {folder_id} by user {current_user.user_id}")
    
    return None

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
            # Use v3 generator for clean, properly labeled diagrams
            try:
                logger.info(f"Using GraphViz v3 generator for description length: {len(description)}")
                code = generate_graphviz_v3(description)
                logger.info(f"GraphViz v3 generator succeeded, code length: {len(code)}")
                return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
            except Exception as e:
                logger.error(f"GraphViz v3 generator failed: {str(e)}")
            
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
            # Use v3 generator for clean, properly labeled diagrams
            try:
                logger.info(f"Using Mermaid v3 generator for description length: {len(description)}")
                code = generate_mermaid_v3(description)
                logger.info(f"Mermaid v3 generator succeeded, code length: {len(code)}")
                return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
            except Exception as e:
                logger.error(f"Mermaid v3 generator failed: {str(e)}, using fallback")
                # Fallback to old logic
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
        
        elif request.diagram_type == 'pikchr':
            # Use Pikchr - reliable, simple diagram language
            try:
                logger.info(f"Using Pikchr v3 generator for description length: {len(description)}")
                code = generate_pikchr_v3(description)
                logger.info(f"Pikchr v3 generator succeeded, code length: {len(code)}")
                return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
            except Exception as e:
                logger.error(f"Pikchr v3 generator failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to generate Pikchr diagram: {str(e)}")
        
        elif request.diagram_type == 'plantuml':
            # Use v3 generator for clean, properly labeled diagrams
            try:
                logger.info(f"Using PlantUML v3 generator for description length: {len(description)}")
                code = generate_plantuml_v3(description)
                logger.info(f"PlantUML v3 generator succeeded, code length: {len(code)}")
                return DiagramGenerationResponse(code=code, kroki_type=kroki_type)
            except Exception as e:
                logger.error(f"PlantUML v3 generator failed: {str(e)}, using fallback")
                # Fallback to old logic
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