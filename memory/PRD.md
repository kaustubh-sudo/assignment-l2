# Kroki Diagram Renderer - Product Requirements Document

## Original Problem Statement
Build an enhanced Kroki diagram renderer application with user authentication and diagram management features.

## User Personas
- **Primary Users**: Developers, architects, and technical writers who need to create and manage diagrams
- **Use Case**: Visualize processes, workflows, and system architectures using various diagram types

## Core Requirements

### 1. User Authentication
| ID | Requirement | Status |
|----|-------------|--------|
| US-1 | Signup - New users can create an account with unique email and password (min 6 chars) | ✅ DONE |
| US-2 | Login - Registered users can log in with credentials, receive JWT token | ✅ DONE |
| US-3 | Logout - Users can log out, clearing JWT from localStorage | ✅ DONE |
| US-4 | Protected Routes - Diagram pages inaccessible to non-logged-in users | ✅ DONE |

### 2. Diagram Management
| ID | Requirement | Status |
|----|-------------|--------|
| US-5 | Save Diagram - Logged-in users can save diagrams with title and description | ✅ DONE |
| US-6 | Update Diagram - Users can update existing diagrams | ✅ DONE |
| US-7 | List Diagrams - Users can view their saved diagrams sorted by date | ✅ DONE |
| US-8 | Delete Diagram - Users can delete diagrams with confirmation | ✅ DONE |
| US-9 | Load for Editing - Users can click saved diagram to open in editor | ✅ DONE |
| US-10 | Export Diagram - Users can export diagrams as PNG/SVG | ✅ DONE |
| US-11 | Search Diagrams - Users can search diagrams by title/description | ✅ DONE |

### 3. Folder Organization
| ID | Requirement | Status |
|----|-------------|--------|
| US-12 | Create Folders - Users can create folders to organize diagrams | ✅ DONE (Jan 30, 2026) |
| US-13 | Move Diagram to Folder - Users can assign diagrams to folders | ✅ DONE (Jan 30, 2026) |

### 4. Testing
| ID | Requirement | Status |
|----|-------------|--------|
| T-1 | Comprehensive testing suite | 🔄 IN PROGRESS |
| T-2 | 100% code coverage | ⏳ PENDING |

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: MongoDB (motor driver)
- **Authentication**: JWT tokens (python-jose), password hashing (passlib)
- **API Prefix**: `/api`

### Frontend (React)
- **Framework**: React with React Router
- **State Management**: React Context API (AuthContext)
- **Styling**: Tailwind CSS, Shadcn/UI components
- **Notifications**: sonner

### Key API Endpoints
```
# Auth
POST /api/auth/signup     - User registration
POST /api/auth/login      - User authentication
GET  /api/auth/me         - Get current user info

# Diagrams
POST /api/diagrams        - Create new diagram (with optional folder_id)
GET  /api/diagrams        - List user's diagrams (includes folder_id)
GET  /api/diagrams/{id}   - Get specific diagram
PUT  /api/diagrams/{id}   - Update diagram (with optional folder_id)
PUT  /api/diagrams/{id}/folder - Move diagram to folder
DELETE /api/diagrams/{id} - Delete diagram

# Folders
POST /api/folders         - Create new folder
GET  /api/folders         - List user's folders
DELETE /api/folders/{id}  - Delete folder (clears folder_id from diagrams)

# Generation
POST /api/generate-diagram - Generate diagram code from description
```

### Database Schema
```
users: { id, email, hashed_password, created_at }
diagrams: { id, user_id, title, description, diagram_type, diagram_code, folder_id, created_at, updated_at }
folders: { id, user_id, name, created_at }
```

## Known Issues

### ~~P1: Login Error Toast~~ ✅ FIXED (Jan 30, 2026)
- **Status**: RESOLVED
- **Issue**: Technical error was shown instead of "Invalid email or password"
- **Fix**: Updated response handling in AuthContext.js

### P2: Test Coverage
- **Status**: Not started
- **Current**: Backend 56%, Frontend 43%
- **Target**: 100%

## Test Credentials
```
Email: foldertest@example.com
Password: password123
```

## File References
- `backend/server.py` - Main API endpoints including folder endpoints
- `backend/auth.py` - Authentication helpers
- `frontend/src/context/AuthContext.js` - Auth state management
- `frontend/src/pages/DiagramRenderer.js` - Main editor with load/save/folder selection
- `frontend/src/pages/DiagramsList.js` - Diagram list with folder sidebar and filtering
- `frontend/src/components/DiagramCard.js` - Diagram card with folder badge
- `frontend/src/components/CreateFolderModal.js` - Create folder modal
- `frontend/src/components/SaveDiagramModal.js` - Save modal with folder dropdown

## Changelog
- **Jan 30, 2026**: Light Theme & Responsiveness Update
  - Converted entire app from dark to light theme
  - Improved mobile responsiveness across all pages
  - Login/Signup pages: Clean white cards with blue gradient background
  - Diagrams list: Light sidebar, white cards, improved spacing
  - Editor: Light panels with proper mobile stacking
  - Mobile-friendly folder filters (horizontal scroll)
  - Compact buttons on smaller screens
- **Jan 30, 2026**: US-12 & US-13 Folder Organization - VERIFIED ✅
  - "New Folder" button opens create folder modal
  - Folder sidebar with All Diagrams, No Folder, and user folders with counts
  - Folder filtering shows diagrams in selected folder
  - Save modal has folder dropdown for assigning diagrams
  - Diagram cards display amber folder badge when assigned
  - Folders can be deleted (diagrams moved to "No Folder")
  - Backend: 14/14 folder tests passed
- **Jan 30, 2026**: US-11 Search Diagrams - VERIFIED ✅
- **Jan 30, 2026**: US-10 Export Diagram - VERIFIED ✅
- **Jan 30, 2026**: US-9 Load Saved Diagram for Editing - VERIFIED ✅
- **Jan 30, 2026**: P1 Bug Fix - Login error toast now shows "Invalid email or password"
- **Jan 31, 2026**: Developer Assessment Framework - COMPLETE ✅
  - Created bug injection/fix/evaluation framework in `/app/`
  - 23 bugs across 6 categories: Authentication, Save/Load, List/Display, Export, Search, Folders
  - Human-tolerant evaluation using regex-based logical checks (not strict string matching)
  - Scripts: `inject_bugs.py`, `fix_bugs.py`, `evaluate.py`, `manager.py`
  - Documentation: `PROBLEM_STATEMENT.md`, `ANSWER_KEY.md`
  - HTML and JSON report generation in `/app/reports/`

## Developer Assessment Framework

### Purpose
Transform this Kroki diagram app into a developer assessment tool by injecting bugs that candidates must fix.

### Scripts
| Script | Purpose |
|--------|---------|
| `inject_bugs.py` | Inject predefined bugs into codebase |
| `fix_bugs.py` | Revert all bugs to clean state |
| `evaluate.py` | Score candidate submissions with reports |
| `manager.py` | Manual control utility for assessors |

### Bug Categories (20 total, 170 points)
| Category | Bugs | Points |
|----------|------|--------|
| Authentication | 4 | 20 |
| Save/Load | 5 | 50 |
| List/Display | 3 | 35 |
| Export | 3 | 20 |
| Search | 3 | 25 |
| Folders | 2 | 20 |

### Hint Comments in Buggy Code
Each injected bug includes a hint comment (`TODO`, `FIXME`) that points candidates toward the issue without revealing the solution:
- `FIXME:` - Describes the user-facing symptom
- `TODO:` - Describes what needs to be implemented
- Comments do NOT include bug IDs to prevent direct lookup

### Human-Tolerant Evaluation
The evaluation uses regex-based logical checks, not strict string matching:
- Accepts syntactic variations (different comments, quotes, spacing)
- Detects if the bug is logically fixed, regardless of exact implementation
- Fair scoring for real-world developer candidates

### Usage
```bash
# Inject all bugs (prepare for assessment)
python inject_bugs.py

# Check current status
python inject_bugs.py --status

# Evaluate candidate submission
python evaluate.py --candidate "John Doe" --html

# Reset to clean state
python fix_bugs.py
```

