# Crown Demo — Pre-Demo Checklist (2 minutes)

## Before You Start (Do This Once)

### 1. Start the Full Stack
**Time: ~1 minute**

Open PowerShell in the Crown2026 folder and run:

```powershell
.\runall.ps1
```

**What it does:**
- Clears old Python cache
- Runs database migrations
- Seeds demo data (school, students, applications, awards, timeline actions)
- Starts Django server on port 8000

**Wait for:** The script should end with `✅ Server running on http://127.0.0.1:8000`

**If it fails:**
- Check [RUNALL_FAILURES.md](RUNALL_FAILURES.md) (troubleshooting guide)
- Or run manually:
  ```powershell
  cd backend
  .\venv\Scripts\python.exe manage.py migrate
  .\venv\Scripts\python.exe manage.py seed_demo_school --wipe
  .\venv\Scripts\python.exe manage.py seed_gradebook_demo --school-id <SCHOOL_UUID> --wipe
  .\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
  ```

**Note on Gradebook Demo Data:**
To ensure the gradebook grid is never empty during demos, run:
```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed_gradebook_demo --school-id b45b8c5a-6708-4597-aad9-a226627b2962 --wipe
```
This populates grade entries for all sections with enrolled students. The command is idempotent and safe to rerun.

---

### 2. Verify the Dashboard Loads
**Time: ~30 seconds**

Open your browser and navigate to:

```
http://127.0.0.1:8000/director/
```

**You should see:**
- ✅ **Header:** "Crown Director Dashboard" with school ID and year
- ✅ **KPI Cards:** 6 metrics (Aid Apps, Awards Posted, Aid Awarded, Tuition, Net Receivable, Enrollment)
- ✅ **Refresh Button:** Top-left, blue button
- ✅ **Left Panel:** "Priority Worklist (Top 10)" with a table
- ✅ **Right Panel:** "Director Timeline (Recent)" with action history
- ✅ **Debug Section (bottom):** Raw JSON (optional, for tech audience)

**If something is missing:**
- Check the browser console (F12 → Console tab) for errors
- Verify the server is running (check terminal)
- Try a hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

---

### 3. Test One Action
**Time: ~30 seconds**

Click the **Refresh** button. KPI numbers should blink/update.

Then, click an action button on the Priority Worklist (e.g., "Send Email" or "Mark Complete").

**You should see:**
- ✅ Button disables briefly
- ✅ A notification or status change
- ✅ The item disappears or moves in the worklist

**If the action fails:**
- Check the debug JSON (bottom of page) for error messages
- Verify the API is running: Try this in PowerShell:
  ```powershell
  Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/director/dashboard/?school_id=0c0d109f-3752-496b-906b-3b45e16a91fd&year_id=31cf07c5-38ee-4d0d-aef6-e6adb2704d13" `
    -Method GET
  ```
  Should return JSON with KPI data.

---

## During the Demo

### Before Audience Arrives
1. **Refresh the page** one more time to ensure fresh data
2. **Close any other tabs** (minimize distractions)
3. **Silence notifications** (Slack, Teams, etc.)
4. **Have the script printed or on a second monitor** for talking points

### Start
1. **Show the URL bar:** `http://127.0.0.1:8000/director/` — shows it's a real, running app
2. **Take a breath** before speaking
3. **Follow the script** (see `DEMO_SCRIPT.md`)

### If Something Breaks Mid-Demo
- **Don't panic.** Say: "Let me refresh and see what happened."
- Click **Refresh** button
- If that doesn't work, say: "The API is resetting. One second." and wait 3 seconds
- If the server is actually down, say: "We've hit a hiccup. Let me restart the server." (takes ~5 seconds), then reload the page

---

## After the Demo

- **Ask for feedback:** "What would make this more useful for you?"
- **Mention next steps:** "We can integrate with your systems, customize the priority algorithm, and add mobile support."
- **Offer a trial:** "Want to use this for a week with real data? We can set that up."

---

## Backup Plan (If Server Crashes Mid-Demo)

**Option 1: Quick Restart (30 seconds)**
```powershell
Get-Process python | Stop-Process -Force
Start-Sleep -Seconds 2
cd backend
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

Then refresh the browser page.

**Option 2: Use Screenshots (No Restart)**
- Have screenshots of the dashboard ready (saved before the demo)
- Walk through the screenshot and explain what each section does
- Say: "The server had a hiccup, but you've seen the interface. Here's what happens when you click Refresh..."

**Option 3: Skip to Q&A**
- "We've seen the main flow. Let me address the questions you might have..."
- Focus on use cases and integrations instead of live clicking

---

## Success Criteria

✅ Dashboard page loads in under 3 seconds  
✅ KPI metrics display (numbers, not dashes)  
✅ Priority Worklist has at least 3 items  
✅ Timeline shows at least 5 recent actions  
✅ Refresh button works and updates data  
✅ One action button executes without error  

**If all 6 are true:** You're ready to demo.

---

## URLs Reference

| Endpoint | Purpose |
|----------|---------|
| `http://127.0.0.1:8000/director/` | Main dashboard page |
| `http://127.0.0.1:8000/api/director/dashboard/` | KPI data API |
| `http://127.0.0.1:8000/api/director/priority/` | Priority worklist API |
| `http://127.0.0.1:8000/api/director/timeline/` | Timeline API |
| `http://127.0.0.1:8000/api/director/actions/` | Action execution API (POST) |

---

## Demo IDs (Hardcoded in Template)

```
school_id: 0c0d109f-3752-496b-906b-3b45e16a91fd
year_id:   31cf07c5-38ee-4d0d-aef6-e6adb2704d13
```

These are created by `runall.ps1` in the seed data. If you change the demo data, update these IDs in `backend/crown_api/templates/director_dashboard.html` (lines 10–13).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Page shows blank / error" | Hard refresh: `Ctrl+Shift+R`. Check server is running. |
| "KPI shows dashes (—)" | Check browser console (F12) for API errors. Verify demo school exists. |
| "Action button doesn't work" | Refresh page. Check debug JSON for error message. |
| "Server won't start" | Run `.\venv\Scripts\python.exe manage.py check` to see what's wrong. |
| "404 on /api/director/* endpoints" | Verify `backend/crown_api/api_urls.py` has the routes. Restart server. |

---

**Ready to demo?** Print this checklist and keep it by your laptop. You've got this.
