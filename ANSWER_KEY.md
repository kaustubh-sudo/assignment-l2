# Answer Key - Bug Fixes (CONFIDENTIAL)

> ⚠️ **FOR ASSESSORS ONLY** - Do not share with candidates

---

## Summary

| Bug ID | Category | Difficulty | Points | File | Hint Marker |
|--------|----------|-----------|--------|------|-------------|
| AUTH-001 | Authentication | Easy | 5 | server.py | FIXME |
| AUTH-002 | Authentication | Easy | 5 | server.py | TODO |
| AUTH-003 | Authentication | Easy | 5 | AuthContext.js | FIXME |
| AUTH-004 | Authentication | Easy | 5 | server.py | TODO |
| SAVE-001 | Save/Load | Hard | 15 | server.py | FIXME |
| SAVE-002 | Save/Load | Medium | 10 | DiagramRenderer.js | TODO |
| SAVE-003 | Save/Load | Medium | 10 | DiagramRenderer.js | FIXME |
| SAVE-004 | Save/Load | Medium | 10 | DiagramRenderer.js | FIXME |
| SAVE-005 | Save/Load | Easy | 5 | SaveDiagramModal.js | TODO |
| LIST-001 | List/Display | Hard | 15 | server.py | FIXME |
| LIST-002 | List/Display | Medium | 10 | DiagramCard.js | FIXME |
| LIST-004 | List/Display | Medium | 10 | DiagramsList.js | FIXME |
| EXPORT-001 | Export | Easy | 5 | DiagramRenderer.js | TODO |
| EXPORT-002 | Export | Medium | 10 | DiagramRenderer.js | FIXME |
| EXPORT-003 | Export | Easy | 5 | PreviewPanel.js | TODO |
| SEARCH-002 | Search | Medium | 10 | DiagramsList.js | FIXME |
| SEARCH-003 | Search | Medium | 10 | DiagramsList.js | FIXME |
| SEARCH-004 | Search | Easy | 5 | DiagramsList.js | TODO |
| FOLDER-001 | Folders | Medium | 10 | server.py | FIXME |
| FOLDER-002 | Folders | Medium | 10 | DiagramRenderer.js | TODO |
| **Total** | | | **175** | | |

---

## Authentication Bugs

### AUTH-001: Email Case-Sensitive Login
**File:** `/app/backend/server.py`
```python
# Buggy (look for FIXME comment about letter casing)
# FIXME: Users report they can't login when using different letter casing
user_doc = await db.users.find_one({"email": credentials.email})

# Fixed
user_doc = await db.users.find_one({"email": credentials.email.lower()})
```

### AUTH-002: Duplicate Email Registration
**File:** `/app/backend/server.py`
```python
# Buggy (look for TODO comment - check is commented out)
# TODO: Re-enable duplicate email check - users can register same email multiple times!

# Fixed: uncomment and add .lower()
existing_user = await db.users.find_one({"email": user_data.email.lower()})
if existing_user:
    raise HTTPException(status_code=400, detail="Email already registered")
```

### AUTH-003: Logout Doesn't Clear Token
**File:** `/app/frontend/src/context/AuthContext.js`
```javascript
// Buggy (look for FIXME comment about token persistence)
const logout = () => {
  // FIXME: Users report staying logged in after logout - token persists somewhere
  setToken(null);
  setUser(null);
};

// Fixed
const logout = () => {
  localStorage.removeItem('token');
  setToken(null);
  setUser(null);
};
```

### AUTH-004: Password Minimum Length
**File:** `/app/backend/server.py`
```python
# Add before user creation
if len(user_data.password) < 6:
    raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
```

---

## Save/Load Bugs

### SAVE-001: Duplicate Entries
**File:** `/app/backend/server.py`
```python
# Add duplicate check before insert
existing_diagram = await db.diagrams.find_one({
    "user_id": current_user.user_id,
    "title": diagram_data.title
})
if existing_diagram:
    # Update existing instead
```

### SAVE-002: Load Doesn't Populate Description
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Add this line when loading
setUserInput(data.description || '');
```

### SAVE-003: Save Button Stays Disabled
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Add finally block
} finally {
  setIsSaving(false);
}
```

### SAVE-004: Timestamp Doesn't Update
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Use data.updated_at instead of savedDiagram?.updated_at
updated_at: data.updated_at
```

### SAVE-005: Title Doesn't Clear
**File:** `/app/frontend/src/components/SaveDiagramModal.js`
```javascript
// Add form reset after save
if (!existingTitle) {
  setTitle('');
  setDescription('');
}
```

---

## List/Display Bugs

### LIST-001: Shows Everyone's Diagrams
**File:** `/app/backend/server.py`
```python
# Add user filter
query_filter = {"user_id": current_user.user_id}
```

### LIST-002: Delete Wrong Diagram
**File:** `/app/frontend/src/components/DiagramCard.js`
```javascript
// Fix: pass correct diagram
onDelete(diagram);  // Not diagram with corrupted ID
```

### LIST-004: Count Doesn't Update
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Add state update
setDiagrams(prevDiagrams => prevDiagrams.filter(d => d.id !== deleteTarget.id));
```

### LIST-005: Raw Date Format
**File:** `/app/frontend/src/components/DiagramCard.js`
```javascript
// Use formatDate function
{formatDate(diagram.created_at)}
```

---

## Export Bugs

### EXPORT-001: Generic Filename
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Use title in filename
const sanitizedTitle = title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
return `${sanitizedTitle}.${format}`;
```

### EXPORT-002: Spinner Never Clears
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Add finally block
} finally {
  setIsExporting(false);
}
```

### EXPORT-003: Button Not Disabled
**File:** `/app/frontend/src/components/PreviewPanel.js`
```javascript
// Add disabled prop
<Button disabled={isExporting} ...>
```

---

## Search Bugs

### SEARCH-002: Ignores Folder Filter
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Apply folder filter BEFORE search filter (always)
// Not only when not searching
```

### SEARCH-003: Clear Button Doesn't Work
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Add setSearchQuery('')
const handleClearSearch = () => {
  setSearchQuery('');
};
```

### SEARCH-004: No Debounce
**File:** `/app/frontend/src/pages/DiagramsList.js`
```javascript
// Use debounced value
const debouncedSearchQuery = useDebounce(searchQuery, 300);
```

---

## Folder Bugs

### FOLDER-001: Shows All Users' Folders
**File:** `/app/backend/server.py`
```python
# Add user_id filter
folders = await db.folders.find(
    {"user_id": current_user.user_id},
    {"_id": 0}
)
```

### FOLDER-002: Folder Selection Not Saved
**File:** `/app/frontend/src/pages/DiagramRenderer.js`
```javascript
// Include folder_id in save data
const diagramData = {
  title,
  description,
  diagram_type: diagramType,
  diagram_code: generatedCode,
  folder_id: folder_id  // Add this line
};
```

---

## Quick Commands

```bash
# Check status
python manager.py status

# Inject all bugs
python inject_bugs.py

# Inject by category
python inject_bugs.py --category "Folders"

# Fix all bugs
python fix_bugs.py

# Evaluate
python evaluate.py --candidate "Name" --html
```

---

## Score Interpretation

| Score | Grade | Assessment |
|-------|-------|-----------|
| 150-185 | A | Excellent |
| 115-149 | B | Good |
| 80-114 | C | Average |
| 45-79 | D | Below Average |
| 0-44 | F | Needs Improvement |
