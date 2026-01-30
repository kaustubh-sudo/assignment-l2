# Developer Assessment - Bug Fixing Challenge

## Overview
You have been given access to a **Diagram Maker** web application that allows users to create, save, and manage diagrams. The application has several bugs that need to be identified and fixed.

**Time Limit:** 1 hour  
**Total Bugs:** 3  
**Categories:** Authentication

---

## Application Stack
- **Frontend:** React.js with Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB

## Key Files
- Backend: `/app/backend/server.py`, `/app/backend/auth.py`
- Frontend: `/app/frontend/src/`

---

## Bugs to Find and Fix

### AUTH-001: Login Case Sensitivity Issue
**Category:** Authentication  
**Difficulty:** Easy  
**Estimated Time:** 1 minute

**How to Reproduce:**
1. Sign up with email: `Test@Example.com`
2. Log out
3. Try to log in with email: `test@example.com` (lowercase)
4. ❌ You get "Invalid credentials" error

**Expected Behavior:**
- Login should work regardless of email case
- `Test@Example.com` and `test@example.com` should be treated as the same user

---

### AUTH-002: Duplicate Email Registration
**Category:** Authentication  
**Difficulty:** Easy  
**Estimated Time:** 2 minutes

**How to Reproduce:**
1. Sign up with email: `test@example.com`
2. Log out
3. Sign up again with the same email: `test@example.com`
4. ❌ Registration succeeds (should show "Email already exists" error)

**Expected Behavior:**
- System should prevent duplicate email registrations
- User should see an error message when trying to register with an existing email

---

### AUTH-003: Logout Token Persistence
**Category:** Authentication  
**Difficulty:** Easy  
**Estimated Time:** 1 minute

**How to Reproduce:**
1. Log in as any user
2. Click "Logout" button (you get redirected to login page)
3. Open browser DevTools → Application → Local Storage
4. ❌ Token is still present in localStorage
5. Press browser Back button → You're still logged in!

**Expected Behavior:**
- Logout should completely clear the authentication token from localStorage
- User should not be able to access protected pages after logout

---

## Evaluation Criteria

| Criteria | Points |
|----------|--------|
| Bug found and properly fixed | 1 point per bug |
| Code quality and best practices | Bonus consideration |
| Clean, minimal changes | Bonus consideration |

---

## How to Run the Application

```bash
# Start services (if not already running)
cd /app
sudo supervisorctl status

# Test your changes
# Backend API: Use curl or Postman
# Frontend: Access via browser
```

---

## Submission
Your fixes will be automatically evaluated by running:
```bash
python evaluate.py --candidate "Your Name"
```

Good luck! 🚀
