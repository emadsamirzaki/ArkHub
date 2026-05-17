# ArkHub — Internal Systems Platform

> An EOS-aligned internal tools platform for Arkdev leadership, built with
> Python + Streamlit. ArkScore is the L10 meeting scorecard system within ArkHub.

---

## Quick Start

### Prerequisites
- Python 3.11 or newer
- pip

### Install & run

```bash
# 1. Clone / open the project folder
cd "ArkHub"

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

---

## Platform Overview

ArkHub is a multi-system internal platform. Each system is independently navigable from the home page or the sidebar.

| System | Status | Description |
|--------|--------|-------------|
| **ArkScore** | ✅ Active | EOS L10 weekly scorecard — utilization, operational health, and project tracking |
| **Workforce** | ✅ Active | Working patterns, live team availability, and daily schedules |
| **HR System** | 🔒 Coming Soon | Leave management, performance reviews, and employee records |
| **Finance** | 🔒 Coming Soon | Revenue tracking, headcount ratios, and financial reporting |
| **BD & Pipeline** | 🔒 Coming Soon | Business development conversations, pipeline activity, and conversion tracking |

---

## ArkScore System

ArkScore is built on the **Entrepreneurial Operating System (EOS)** framework, giving leadership a single place to track and present key operational metrics during weekly **L10 meetings**.

### Modules

| Module | Status | Description |
|--------|--------|-------------|
| Utilization % | ✅ Active | Team time utilisation vs. 35 h weekly target |
| Operational Health | ✅ Active | Project delivery status, weekly check-ins, health score |
| Client Health | 🔒 Coming Soon | NPS, satisfaction scores, escalation tracking |
| Process Compliance | 🔒 Coming Soon | Checklist adherence and process audit results |
| Revenue per Head | 🔒 Coming Soon | Revenue efficiency and headcount ratios |
| BD Conversations | 🔒 Coming Soon | Pipeline activity, outreach, and conversion |
| Rock Completion | 🔒 Coming Soon | Quarterly rock progress and completion rates |

---

### Utilization %

#### Utilization Check-in (`ArkScore → Utilization Check-in`)
1. Pick any day in the target week using the date picker — the full Sun–Thu week is used automatically
2. Upload a Clockify **Detailed Report** CSV
3. Preview auto-calculated metrics (team members, total hours, avg utilization)
4. Click **Save Report** — or **Confirm & Replace** if a report for that week already exists
5. Saved weeks are listed below the upload form with **View** and **Delete** actions

#### Utilization Dashboard (`ArkScore → Utilization Dashboard`)
- **Week selector** — switch between any saved week
- **Summary cards** — Team Utilization %, Total Billable %, Total Non-Billable %, Total Hours Logged
- **Team chart** — colour-coded horizontal bar chart with an 80% target reference line
- **Team details** — sortable table with a progress bar per member
- **Per-person breakdown** — expandable per-member view of every project and task entry
- **Week-over-week comparison** — delta table vs. the previous week (when 2+ weeks are saved)

#### Status thresholds
| Threshold | Status |
|-----------|--------|
| ≥ 80 % | 🟢 On Target |
| 60 – 79 % | 🟡 Watch |
| < 60 % | 🔴 Critical |

Weekly target = **35 hours** (7 h/day × 5 days)

---

### Operational Health

#### Project Management (`ArkScore → Project Management`)
- Add projects with a name, assigned PM, and Active/Inactive status
- Inline edit and save any project row
- Deactivate or reactivate projects without deleting them

#### Weekly Check-in (`ArkScore → Weekly Check-in`)
- PMs select any day in the week; the full Sun–Thu week is resolved automatically
- Submit a **Health Status** (On Track / Off Track) per project
- Optionally attach a note with type: **Note**, **Red Flag**, or **Success Story**
- Save entries individually or all at once; re-submitting updates the existing entry

#### Operational Health Dashboard (`ArkScore → Operational Health`)
- **Health score hero** — overall % of checked-in projects on track, coloured green/red
- Alert banner shown when the score drops below the 85% threshold
- **Project status cards** — colour-coded On Track / Off Track / Awaiting check-in per project
- **Summary table** — all projects sorted by status (Off Track → On Track → Awaiting), with note previews
- Week selector to review any historical week

---

### Clockify CSV Column Reference

The Utilization module expects Clockify's **Detailed Report** export. Key columns used:

| Column | Usage |
|--------|-------|
| `User` | Team member identifier |
| `Billable` | `"Yes"` or `"No"` |
| `Duration (decimal)` | Numeric hours (e.g. `2.50`) — used for all calculations |
| `Start Date` | `MM/DD/YYYY` format — used for week label auto-detection |
| `Project` | Project name — shown in per-person breakdown |
| `Description` | Task description — shown in per-person breakdown |

#### Export from Clockify
1. Log in to [Clockify](https://clockify.me)
2. Go to **Reports → Detailed**
3. Set your date range to the target week
4. Click **Export → Save as CSV**

---

## Workforce System

The Workforce system manages employee working patterns and shows live team availability.

### Employees (`Company → Employees`)
- Central employee directory used by all ArkHub systems
- Add employees with full name, email, and role
- Role picker supports existing roles or creating a new role on the fly
- Edit any employee inline; toggle status between Active and Inactive
- Delete employees with a confirmation prompt

### Working Patterns (`Workforce → Working Patterns`)
- Select any active employee from the dropdown
- Define weekly schedule across Sun–Thu using day tabs
- Each day supports multiple time slots with **Start**, **End**, and **Location** (Home / Office / Away)
- Add or remove slots freely; total working hours shown per day with a ≥ 7 h target indicator
- Save pattern; expand the preview panel to review the saved schedule

### Availability Now (`Workforce → Availability Now`)
- Live dashboard auto-refreshed on page load; displays Cairo local time
- **Right Now** cards — one card per employee showing current status (Working from Home / In the Office / Away / Not Working)
- **Changes in the Next Hour** — lists upcoming status transitions within 60 minutes
- **Today's Timeline** — visual horizontal bar per employee from 07:00–20:00, with a live "now" marker
- **Employee Schedules** — expandable full weekly schedule per employee
- On non-working days (Friday / Saturday) a schedule-only view is shown

---

## Project Structure

```
ArkHub/
├── app.py                              # ArkHub navigation controller
├── requirements.txt
├── .streamlit/
│   └── config.toml                     # Dark-navy theme
├── views/
│   └── home.py                         # Platform home page with system cards
├── systems/
│   ├── arkscore/                        # ArkScore — EOS L10 scorecard system
│   │   ├── home.py                     # ArkScore overview & module list
│   │   ├── utilization_dashboard.py    # Utilization % dashboard
│   │   ├── utilization_checkin.py      # Clockify CSV upload & saved weeks
│   │   ├── operational_health.py       # Operational Health dashboard
│   │   ├── weekly_checkin.py           # PM weekly check-in form
│   │   ├── project_management.py       # Project CRUD admin view
│   │   └── utils/
│   │       ├── constants.py            # Thresholds, colours, PM list
│   │       ├── parse_clockify.py       # CSV parsing + utilization calculation
│   │       ├── utilization_store.py    # Utilization report persistence
│   │       ├── entry_store.py          # Check-in entry persistence
│   │       └── project_store.py        # Project record persistence
│   └── people/                          # People & Workforce system
│       ├── employees.py                # Employee directory
│       ├── working_patterns.py         # Weekly schedule editor
│       ├── availability.py             # Live availability dashboard
│       └── utils/
│           ├── employee_store.py       # Employee record persistence
│           └── pattern_store.py        # Working pattern persistence
```

---

## Tech Stack

| Layer | Library |
|-------|---------|
| UI | [Streamlit](https://streamlit.io) ≥ 1.32 |
| Data | [pandas](https://pandas.pydata.org) ≥ 2.0 |
| Charts | [Plotly](https://plotly.com/python/) ≥ 5.18 |
| Language | Python 3.11+ |
| Timezone | `zoneinfo` (stdlib) — Africa/Cairo |
