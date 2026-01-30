# Developer Assessment - Bug Fixing Challenge

## Overview
You have been given access to a **Diagram Maker** web application that allows users to create, save, and manage diagrams. The application has several bugs that need to be identified and fixed.

**Time Limit:** 1 hour  
**Total Bugs:** 10  
**Total Points:** 70  
**Categories:** Authentication (4 bugs), Save/Load (6 bugs)

---

## Application Stack
- **Frontend:** React.js with Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB

## Key Files
- Backend: `/app/backend/server.py`, `/app/backend/auth.py`
- Frontend: `/app/frontend/src/pages/`, `/app/frontend/src/components/`

---

## Authentication Bugs (4 bugs, 20 points)

### AUTH-001: Login Case Sensitivity Issue (5 pts)
**Difficulty:** Easy  
**Estimated Time:** 1 minute

**How to Reproduce:**
1. Sign up with email: `Test@Example.com`
2. Log out
3. Try to log in with email: `test@example.com` (lowercase)
4. ❌ You get "Invalid credentials" error

**Expected Behavior:**
- Login should work regardless of email case

---

### AUTH-002: Duplicate Email Registration (5 pts)
**Difficulty:** Easy  
**Estimated Time:** 2 minutes

**How to Reproduce:**
1. Sign up with email: `test@example.com`
2. Log out
3. Sign up again with the same email: `test@example.com`
4. ❌ Registration succeeds (should show "Email already exists" error)

**Expected Behavior:**
- System should prevent duplicate email registrations

---

### AUTH-003: Logout Token Persistence (5 pts)
**Difficulty:** Easy  
**Estimated Time:** 1 minute

**How to Reproduce:**
1. Log in as any user
2. Click "Logout" button (you get redirected to login page)
3. Open browser DevTools → Application → Local Storage
4. ❌ Token is still present in localStorage
5. Press browser Back button → You're still logged in!

**Expected Behavior:**
- Logout should completely clear the authentication token

---

### AUTH-004: Password Minimum Length Not Enforced (5 pts)
**Difficulty:** Easy  
**Estimated Time:** 1 minute

**How to Reproduce:**
1. Go to Sign Up page
2. Enter email: `test2@example.com`
3. Enter password: `12` (only 2 characters)
4. Click Sign Up
5. ❌ Registration succeeds (should require 6+ characters)

**Expected Behavior:**
- Should show error "Password must be at least 6 characters"

---

## Save/Load Bugs (6 bugs, 50 points)

### SAVE-001: Save Creates Duplicate Entries (15 pts)
**Difficulty:** Hard  
**Estimated Time:** 4 minutes

**How to Reproduce:**
1. Create a diagram and click "Generate"
2. Click Save → Enter title "Test Diagram"
3. Go to "My Diagrams" → See 1 entry ✓
4. Go back to Editor, click Save again (same title)
5. Go to "My Diagrams" → ❌ See 2 entries with same title

**Expected Behavior:**
- Saving with same title should update existing diagram, not create duplicate

---

### SAVE-002: Load Diagram Doesn't Populate Description (10 pts)
**Difficulty:** Medium  
**Estimated Time:** 2 minutes

**How to Reproduce:**
1. Save a diagram with title "Test" and description "My test diagram"
2. Go to "My Diagrams"
3. Click "Test" to edit/load it
4. ❌ The description textarea is empty

**Expected Behavior:**
- Loading a diagram should restore the description in the input field

---

### SAVE-003: Save Button Stays Disabled (10 pts)
**Difficulty:** Medium  
**Estimated Time:** 1.5 minutes

**How to Reproduce:**
1. Create and save a diagram
2. Modify the description
3. Click Save → Spinner shows briefly
4. ❌ Save button remains grayed out/disabled after save completes

**Expected Behavior:**
- Save button should re-enable after save operation completes

---

### SAVE-004: "Last Saved" Timestamp Doesn't Update (10 pts)
**Difficulty:** Medium  
**Estimated Time:** 2 minutes

**How to Reproduce:**
1. Save a diagram → Shows "Saved at 10:00 AM"
2. Wait a minute, make changes
3. Save again → ❌ Still shows "10:00 AM"

**Expected Behavior:**
- Timestamp should update to reflect the most recent save time

---

### SAVE-005: Title Field Doesn't Clear After Save (5 pts)
**Difficulty:** Easy  
**Estimated Time:** 1 minute

**How to Reproduce:**
1. Click Save, enter title "Diagram A"
2. Click Save button → Success
3. Click Save again
4. ❌ Title input still shows "Diagram A" (should be empty for new diagram)

**Expected Behavior:**
- For new diagrams, form should reset after successful save

---

### SAVE-006: Save Without Title Succeeds (5 pts)
**Difficulty:** Easy  
**Estimated Time:** 1.5 minutes

**How to Reproduce:**
1. Create a diagram
2. Click Save, leave title completely empty
3. Click Save button
4. ❌ Might succeed or show unclear error

**Expected Behavior:**
- Should show clear error "Title is required" and prevent save

---

## Evaluation Criteria

| Category | Bugs | Points |
|----------|------|--------|
| Authentication | 4 | 20 |
| Save/Load | 6 | 50 |
| **Total** | **10** | **70** |

### Scoring
- Each bug fixed correctly = Full points for that bug
- Points vary by difficulty (Easy: 5pts, Medium: 10pts, Hard: 15pts)

---

## How to Run the Application

```bash
# Check service status
sudo supervisorctl status

# Restart services if needed
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# View logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

---

## Submission
Your fixes will be automatically evaluated by running:
```bash
python evaluate.py --candidate "Your Name"
```

Good luck! 🚀
