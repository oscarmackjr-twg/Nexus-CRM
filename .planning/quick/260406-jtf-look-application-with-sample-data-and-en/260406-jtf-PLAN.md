---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: false
requirements: []
must_haves:
  truths:
    - "Application is running and accessible at http://localhost:5173"
    - "Sample data is loaded and visible across all pages"
    - "All pages render correctly on desktop viewport"
  artifacts: []
  key_links: []
---

<objective>
Verify the Nexus CRM application is running with sample data and all pages are accessible on desktop.

Purpose: Ensure the current state of the application is functional and visually correct before proceeding with further development phases.
Output: Confirmed working application state with sample data populated.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Application is running via `make dev` (docker-compose). Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL on port 5432, Redis on port 6379

Login credentials: admin@demo.local / password123
Seed data includes: 1 org, 1 team, 1 admin user, 1 pipeline with 4 stages, 1 fund, 4 companies, 6 contacts, 6 deals (various stages).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Verify backend health and sample data availability</name>
  <files></files>
  <action>
    1. Hit the backend health endpoint to confirm the API is responding
    2. Authenticate as demo admin (POST /auth/login with admin@demo.local / password123)
    3. Query key API endpoints to confirm sample data is loaded:
       - GET /contacts — expect 6 contacts
       - GET /companies — expect 4 companies
       - GET /deals — expect 6 deals
       - GET /funds — expect 1 fund
    4. Report counts and any errors
  </action>
  <verify>
    <automated>curl -s http://localhost:8000/health | grep -i ok</automated>
  </verify>
  <done>Backend responds healthy, all sample data endpoints return expected record counts</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 2: Visual inspection of all application pages on desktop</name>
  <what-built>The application is running with sample data across all pages. Backend verification confirms data is loaded.</what-built>
  <how-to-verify>
    Open http://localhost:5173 in a desktop browser (full-width window). Walk through each page:

    1. **Login Page** — Enter admin@demo.local / password123 and log in
    2. **Dashboard** — Verify deal metrics display (pipeline value, deal counts, recent activity)
    3. **Deals Page** — Confirm 6 deals visible with correct stages (2 Qualified, 2 Proposal, 1 Won, 1 Lost)
    4. **Deal Detail** — Click into "Apex Distribution — Platform Buyout" and verify fields populated (value, dates, description, company link)
    5. **Contacts Page** — Confirm 6 contacts listed with names, emails, titles
    6. **Contact Detail** — Click into "James Whitmore" and verify company association and lifecycle stage
    7. **Companies Page** — Confirm 4 companies listed with industry and revenue
    8. **Company Detail** — Click into "Apex Distribution LLC" and verify associated contacts appear
    9. **Admin Page** — Verify reference data categories are accessible

    For each page, check:
    - Layout renders without overflow or clipping on desktop
    - Data is populated (not empty states)
    - Navigation sidebar works correctly
    - No console errors visible
  </how-to-verify>
  <resume-signal>Type "approved" if all pages look good, or describe any issues found</resume-signal>
</task>

</tasks>

<verification>
- Backend health endpoint returns OK
- All CRUD endpoints return sample data with expected counts
- User confirms all 9 pages render correctly with data on desktop
</verification>

<success_criteria>
Application is confirmed running, sample data is loaded and visible across all pages, and no visual or functional issues are observed on desktop viewport.
</success_criteria>

<output>
After completion, create `.planning/quick/260406-jtf-look-application-with-sample-data-and-en/260406-jtf-SUMMARY.md`
</output>
