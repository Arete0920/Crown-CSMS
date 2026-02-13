# Crown Director Dashboard — Demo Script (7–9 minutes)

## Demo Environment Notice

This presentation runs from a frozen Git tag:
```
demo-feb16-gradebook-edit-pp-003
SHA: aec71930dffba0e1d186e49468ff67f77df5ead9
```

The demo code is immutable for presentation stability.

---

**Objective:** Demonstrate the Director Dashboard as a real-time decision support system for financial aid administration.

**Audience:** Leadership, Finance Team, Admin Staff

**Prerequisite:** See `DEMO_CHECKLIST.md` — run `.\runall.ps1` before starting.

---

## Opening (30 seconds)

> "Crown's Director Dashboard turns complex aid workflows into actionable insights. In less than 10 seconds, a director sees their top priorities, recent activity, and key metrics—all from one page. Let me show you what that looks like."

**Action:** Open browser to `http://127.0.0.1:8000/director/`

---

## Section 1: The Dashboard Overview (1.5 minutes)

**On-screen:** Director Dashboard page loads. Show the header and KPI row.

> "This is the Director Dashboard. At the top, we see the school and academic year. Then six key metrics that update in real-time:
>
> - **Aid Applications** — How many students applied?
> - **Awards Posted** — How many awards have we created?
> - **Aid Awarded** — Total dollars committed.
> - **Tuition Revenue** — Net tuition for the year.
> - **Net Receivable** — How much students still owe.
> - **Enrollment** — Total headcount.
>
> Each metric is a live query from the database. Click Refresh (top-left) to see them update."

**Action:** Click the **Refresh** button. Show the KPIs recompute in real-time.

> "Notice the Refresh button is always available. Directors can poll live data whenever they need confidence that they're looking at the latest numbers."

---

## Section 2: Priority Worklist (2 minutes)

**Scroll down to the left panel: "Priority Worklist (Top 10)"**

> "This is where the dashboard earns its name. On the left, we see the top 10 items a director needs to act on today—sorted by urgency.
>
> Each row shows:
> - **Score** — A composite urgency metric (missing docs, unusual amounts, incomplete workflows).
> - **Type** — Is it a missing document? A pending email? A compliance check?
> - **Summary** — What's the issue? 'Student needs to verify income' or 'Award amount exceeds tuition.'
> - **Amount** — For aid items, the dollar value involved.
> - **Action** — One-click button to handle it: 'Send Email,' 'Mark Complete,' 'Flag for Review,' etc.
>
> Let me show you an action in real-time."

**Action:** Find a row with an action button (e.g., "Send Needs-Info Email"). Click it.

> "I just clicked 'Send Email' on that item. Behind the scenes, Crown:
> 1. Sent a templated email to the student.
> 2. Logged the action with a timestamp.
> 3. Marked that item as 'in progress' in the audit trail.
> 4. Removed it from the top 10 (because it's been handled).
>
> One click. No tab-switching. No form-filling. Just action."

**Show the result:** Refresh the page. That item should disappear or change status.

> "The worklist adapts as you work. Items complete, new urgent issues bubble up. It's like a living to-do list."

---

## Section 3: Timeline (1.5 minutes)

**Scroll to the right panel: "Director Timeline (Recent)"**

> "On the right, we have an audit timeline. Every action a director takes is recorded here:
> - When the action happened
> - What type of action it was
> - A human-readable summary
>
> This serves two purposes:
>
> 1. **Transparency:** Leadership can see what decisions are being made and when.
> 2. **Accountability:** If a student disputes something ('I never got that email'), you have proof: 'Email sent 2024-12-15 at 14:32 UTC to student@example.com.'
>
> In a regulated environment like financial aid, this timeline is gold. It's your protection."

**Action:** Scroll the timeline to show multiple entries.

> "Notice the timestamps, the action types, the summaries. This is what compliance officers dream of. Every director interaction is recorded, never deleted, always auditable."

---

## Section 4: Under the Hood (1 minute) — *Optional, for technical audience*

**Scroll to the bottom: "Debug (for build only)"**

> "This is the raw JSON powering the dashboard. You see four API calls:
>
> 1. **dashboard** — The 6 KPIs and their data.
> 2. **priority** — The top 10 worklist items.
> 3. **timeline** — The recent actions.
> 4. **actions** — The available buttons for each item.
>
> All four return in under 500ms. The frontend fetches them in parallel and renders them. No server-side rendering delays. No page reloads. Pure real-time."

> "For developers: Each API is a simple JSON endpoint. You can use it for other apps—mobile, integrations, reports. It's designed to be tool-agnostic."

---

## Section 5: Real-World Scenario (2 minutes)

**Back to the top of the page. Narrate a day in the life.**

> "Let's walk through a real day. A director sits down at 9 AM. They open this dashboard.
>
> **9:00 AM:** Refresh loads. They see:
> - 127 Aid Applications (up 5 from yesterday)
> - 42 Awards Posted (on schedule)
> - $1.2M Awarded (tracking to target)
> - 3 items in the Priority Worklist
>
> **9:15 AM:** First item: 'Student hasn't verified income.' One click: email sent. Status updates.
>
> **9:30 AM:** Second item: 'Award exceeds net tuition.' Director flags for review. System logs it.
>
> **10:00 AM:** Check timeline. See all morning actions. Know exactly what's been touched.
>
> **10:15 AM:** Refresh to see if any new urgent items appeared overnight. None. Dashboard is clear.
>
> By 10:30 AM, the director has made 5 decisions, logged them automatically, and communicated with 3 students. No spreadsheets. No email hunting. No uncertainty about what was done."

> "That's Crown. That's efficiency."

---

## Closing (30 seconds)

> "The Crown Director Dashboard replaces scattered workflows with a single source of truth. It's faster to use, easier to audit, and built on the same data your existing systems trust.
>
> Questions?"

---

## Q&A Talking Points

**Q: How long does it take to learn?**
> "It's one page. Most directors grasp it in under 5 minutes. The refresh button and action buttons are self-explanatory."

**Q: What happens if the network goes down?**
> "The dashboard will show an error in the debug section. But the data is still in the database. Refresh when you're back online."

**Q: Can we customize the priority algorithm?**
> "Absolutely. The 'score' is configurable. You tell us what makes an item urgent for your school, and we adjust the weighting."

**Q: Does this work on mobile?**
> "Right now, it's desktop-optimized. Mobile support is a future roadmap item."

**Q: How often does data refresh?**
> "On-demand. Click Refresh whenever you want. We also have a scheduled refresh option (e.g., every 15 minutes) if you prefer."

---

## Post-Demo

- **Invite feedback** on the interface, language, and usefulness
- **Ask:** "What item would you add to the worklist that isn't there today?"
- **Mention:** "Audit trail is immutable. Finance loves this for compliance."
- **Next step:** "We can integrate with your SIS, financial system, or email platform. Let's talk about what matters most to you."
