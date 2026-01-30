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
| US-10 | Export Diagram - Users can export diagrams as PNG/SVG | ✅ DONE (Jan 30, 2026) |

### 3. Testing
| ID | Requirement | Status |
|----|-------------|--------|
| T-1 | Comprehensive testing suite | 🔄 IN PROGRESS (56% backend, 43% frontend) |
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
- **Notifications**: react-hot-toast / sonner

### Key API Endpoints
```
POST /api/auth/signup     - User registration
POST /api/auth/login      - User authentication
GET  /api/auth/me         - Get current user info
POST /api/diagrams        - Create new diagram
GET  /api/diagrams        - List user's diagrams
GET  /api/diagrams/{id}   - Get specific diagram
PUT  /api/diagrams/{id}   - Update diagram
DELETE /api/diagrams/{id} - Delete diagram
POST /api/generate-diagram - Generate diagram code from description
```

### Database Schema
```
users: { id, email, hashed_password, created_at }
diagrams: { id, user_id, title, description, diagram_type, diagram_code, created_at, updated_at }
```

## Known Issues

### ~~P1: Login Error Toast~~ ✅ FIXED (Jan 30, 2026)
- **Status**: RESOLVED
- **Issue**: Technical error was shown instead of "Invalid email or password"
- **Root Cause**: React StrictMode causing double renders which consumed the response body twice
- **Fix**: Updated `AuthContext.js` to read response as text first, added fallback in `Login.js`
- **Files Changed**: `/app/frontend/src/context/AuthContext.js`, `/app/frontend/src/pages/Login.js`

### P2: Test Coverage
- **Status**: Not started
- **Current**: Backend 56%, Frontend 43%
- **Target**: 100%

## Test Credentials
```
Email: e2etest@example.com
Password: password123
```

## File References
- `backend/server.py` - Main API endpoints
- `backend/auth.py` - Authentication helpers
- `frontend/src/context/AuthContext.js` - Auth state management
- `frontend/src/pages/DiagramRenderer.js` - Main editor with load/save
- `frontend/src/pages/DiagramsList.js` - Diagram list page
- `frontend/src/components/DiagramCard.js` - Diagram card component

## Changelog
- **Jan 30, 2026**: US-9 Load Saved Diagram for Editing - VERIFIED ✅
  - Route `/diagrams/:id` navigates to editor with loaded diagram
  - All CRUD operations tested and working (100% backend tests pass)
