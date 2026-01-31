# Developer Assessment - Bug Fixing Challenge

## Overview
You have been given access to a **Diagram Maker** web application that allows users to create, save, and manage diagrams. The application has several bugs that need to be identified and fixed.

**Time Limit:** 1 hour  
**Total Bugs:** 20  
**Total Points:** 170  
**Categories:** Authentication (4), Save/Load (5), List/Display (3), Export (3), Search (3), Folders (2)

> 💡 **Tip:** Look for `TODO`, `FIXME`, and hint comments in the code - they point to the bugs!

---

## Application Stack
- **Frontend:** React.js with Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB

## Key Files
- Backend: `/app/backend/server.py`
- Frontend: `/app/frontend/src/pages/`, `/app/frontend/src/components/`

---

## Authentication Bugs (4 bugs, 20 points)

### AUTH-001: Login Case Sensitivity Issue (5 pts)
**Difficulty:** Easy | **Time:** ~1 min

**How to Reproduce:**
1. Sign up with email: `Test@Example.com`
2. Log out
3. Try to log in with email: `test@example.com` (lowercase)
4. ❌ You get "Invalid credentials" error

**Expected:** Login should work regardless of email case

---

### AUTH-002: Duplicate Email Registration (5 pts)
**Difficulty:** Easy | **Time:** ~2 min

**How to Reproduce:**
1. Sign up with email: `test@example.com`
2. Log out
3. Sign up again with: `test@example.com`
4. ❌ Registration succeeds

**Expected:** Should show "Email already exists" error

---

### AUTH-003: Logout Token Persistence (5 pts) --> not getting injected token is getting removed
**Difficulty:** Easy | **Time:** ~1 min

**How to Reproduce:**
1. Log in as any user
2. Click "Logout" (redirects to login page)
3. Open DevTools → Application → Local Storage
4. ❌ Token is still present
5. Press Back button → Still logged in!

**Expected:** Logout should clear the token from localStorage

**Hint:** Check `AuthContext.js` for a `FIXME` comment

---

### AUTH-004: Password Minimum Length Not Enforced (5 pts) --> not getting injected (i think ui  side validation is there thats why not able to replicate)
**Difficulty:** Easy | **Time:** ~1 min

**How to Reproduce:**
1. Go to Sign Up page
2. Enter email: `test2@example.com`
3. Enter password: `12` (only 2 characters)
4. ❌ Registration succeeds

**Expected:** Should require 6+ characters

**Hint:** Check `server.py` signup endpoint for a `TODO` comment

---

## Save/Load Bugs (5 bugs, 50 points)

### SAVE-001: Save Creates Duplicate Entries (15 pts)
**Difficulty:** Hard | **Time:** ~4 min

**How to Reproduce:**
1. Create and save diagram with title "Test Diagram"
2. Go to "My Diagrams" → See 1 entry ✓
3. Go back to Editor, save again (same title)
4. Go to "My Diagrams" → ❌ See 2 entries

**Expected:** Saving with same title should update existing diagram

---

### SAVE-002: Load Diagram Doesn't Populate Description (10 pts)
**Difficulty:** Medium | **Time:** ~2 min

**How to Reproduce:**
1. Save a diagram with description "My test diagram"
2. Go to "My Diagrams"
3. Click the diagram to edit
4. ❌ Description textarea is empty

**Expected:** Loading should restore the description

---

### SAVE-003: Save Button Stays Disabled (10 pts)
**Difficulty:** Medium | **Time:** ~1.5 min

**How to Reproduce:**
1. Create and save a diagram
2. Modify the description
3. Click Save → Spinner shows
4. ❌ Save button remains grayed out after completion

**Expected:** Save button should re-enable after save completes

**Hint:** Check `DiagramRenderer.js` for a `FIXME` comment about button state

---

### SAVE-004: "Last Saved" Timestamp Doesn't Update (10 pts)
**Difficulty:** Medium | **Time:** ~2 min

**How to Reproduce:**
1. Save a diagram → Shows "Saved at 10:00 AM"
2. Wait a minute, make changes
3. Save again → ❌ Still shows "10:00 AM"

**Expected:** Timestamp should update after each save

---

### SAVE-005: Title Field Doesn't Clear After Save (5 pts)
**Difficulty:** Easy | **Time:** ~1 min

**How to Reproduce:**
1. Click Save, enter title "Diagram A"
2. Click Save button → Success
3. Click Save again for new diagram
4. ❌ Title still shows "Diagram A"

**Expected:** Form should reset for new diagrams

---

## List/Display Bugs (4 bugs, 40 points)

### LIST-001: My Diagrams Shows Everyone's Diagrams (15 pts)
**Difficulty:** Hard | **Time:** ~4 min

**How to Reproduce:**
1. Account A saves diagram "A's Diagram"
2. Logout, create Account B, save "B's Diagram"
3. In Account B's list → ❌ See BOTH diagrams

**Expected:** Each user should only see their own diagrams

---

### LIST-002: Delete Removes Wrong Diagram (10 pts)
**Difficulty:** Medium | **Time:** ~2.5 min

**How to Reproduce:**
1. Create and save 3 diagrams: A, B, C
2. Click Delete on diagram B
3. ❌ Delete fails or wrong diagram affected

**Expected:** Should delete the correct diagram

---

### LIST-004: Diagram Count Doesn't Update After Delete (10 pts)
**Difficulty:** Medium | **Time:** ~2 min

**How to Reproduce:**
1. Save 3 diagrams → Shows "3 diagrams" ✓
2. Delete 1 diagram
3. ❌ Still shows "3 diagrams"

**Expected:** Count should update to "2 diagrams"

---

## Export Bugs (3 bugs, 20 points)

### EXPORT-001: Export Filename Always "diagram.png" (5 pts)
**Difficulty:** Easy | **Time:** ~1 min

**How to Reproduce:**
1. Save diagram titled "My Flowchart"
2. Click Export → PNG
3. ❌ Downloads as "diagram.png"

**Expected:** Should download as "my-flowchart.png"

---

### EXPORT-002: Export Button Spinner Never Clears (10 pts)
**Difficulty:** Medium | **Time:** ~1.5 min

**How to Reproduce:**
1. Click Export button
2. Spinner appears, export completes
3. ❌ Spinner keeps spinning forever

**Expected:** Spinner should stop after export completes

---

### EXPORT-003: Export Multiple Times Downloads Duplicate Files (5 pts)
**Difficulty:** Easy | **Time:** ~1 min

**How to Reproduce:**
1. Click export button 3 times rapidly
2. ❌ Downloads 3 files

**Expected:** Button should be disabled during export to prevent duplicates

---

## Search Bugs (3 bugs, 25 points)

### SEARCH-002: Search Ignores Folder Filter (10 pts)
**Difficulty:** Medium | **Time:** ~2 min

**How to Reproduce:**
1. Create folder "Work"
2. Save "Diagram A" in Work folder
3. Save "Diagram B" outside Work folder
4. Select "Work" folder, search "Diagram"
5. ❌ Shows both A and B (should only show A)

**Expected:** Search should respect folder filter

---

### SEARCH-003: Clear Search Button Doesn't Work (10 pts)
**Difficulty:** Medium | **Time:** ~1.5 min

**How to Reproduce:**
1. Search "test" → Shows filtered results
2. Click X (clear) button
3. ❌ Still shows filtered results

**Expected:** Clicking clear should show all diagrams

---

### SEARCH-004: Search Doesn't Debounce (5 pts)
**Difficulty:** Easy | **Time:** ~1.5 min

**How to Reproduce:**
1. Type quickly in search box
2. ❌ Notice UI lag/stutter on every keystroke

**Expected:** Should debounce and only filter after typing stops

---

## Folder Bugs (2 bugs, 20 points)

### FOLDER-001: Folder Dropdown Shows All Users' Folders (10 pts)
**Difficulty:** Medium | **Time:** ~2 min

**How to Reproduce:**
1. Account A creates folder "Work"
2. Logout, create Account B
3. Open folder dropdown → ❌ Sees "Work" from Account A

**Expected:** Each user should only see their own folders

---

### FOLDER-002: Folder Selection Not Saved (10 pts)
**Difficulty:** Medium | **Time:** ~2 min

**How to Reproduce:**
1. Select folder from dropdown when saving
2. Save diagram → Success message
3. Reload page or check My Diagrams
4. ❌ Diagram not in the selected folder

**Expected:** Folder assignment should persist

**Hint:** Check `DiagramRenderer.js` for a `TODO` comment about folder_id

---

## Evaluation Criteria

| Category | Bugs | Points |
|----------|------|--------|
| Authentication | 4 | 20 |
| Save/Load | 5 | 50 |
| List/Display | 4 | 40 |
| Export | 3 | 20 |
| Search | 3 | 25 |
| Folders | 2 | 20 |
| **Total** | **21** | **175** |

---

## How to Run

```bash
# Check service status
sudo supervisorctl status

# Restart services if needed
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# View logs
tail -f /var/log/supervisor/backend.err.log
```

---

## Submission
```bash
python evaluate.py --candidate "Your Name"
```

Good luck! 🚀
