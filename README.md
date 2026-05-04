# ArkScore — L10 Meeting Scorecard Dashboard

> An EOS-aligned weekly scorecard app for leadership L10 meetings, built with
> Python + Streamlit.

---

## Quick Start

### Prerequisites
- Python 3.11 or newer
- pip

### Install & run

```bash
# 1. Clone / open the project folder
cd "Arkdev Scorecard"

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

## Using the Utilization Module

### Export from Clockify
1. Log in to [Clockify](https://clockify.me)
2. Go to **Reports → Detailed**
3. Set your date range to the target week
4. Click **Export → Save as CSV**

### Upload in ArkScore
1. Navigate to **Utilization %** in the sidebar
2. Click **Browse files** and select the exported CSV
3. Confirm (or edit) the auto-detected week label
4. Click **Load Dashboard →**

### Dashboard sections
| Section | What you see |
|---------|-------------|
| Summary cards | Team Utilisation %, Total Billable %, Total Non-Billable %, Total Hours |
| Team Chart | Colour-coded horizontal bar chart with an 80 % target reference line |
| Team Details | Sortable table with a progress bar for each member's utilisation |
| Per-Person Breakdown | Expandable per-member view of every project and task entry |

### Status thresholds
| Threshold | Status |
|-----------|--------|
| ≥ 80 % | 🟢 On Target |
| 60 – 79 % | 🟡 Watch |
| < 60 % | 🔴 Critical |

Weekly target = **35 hours** (7 h/day × 5 days)

---

## Project Structure

```
Arkdev Scorecard/
├── app.py                      # Home / landing page
├── requirements.txt
├── .streamlit/
│   └── config.toml             # Dark-navy theme
├── pages/
│   ├── 1_Utilization.py        # ✅ Full utilisation module
│   ├── 2_Operational_Health.py # 🔒 Placeholder
│   ├── 3_Client_Health.py      # 🔒 Placeholder
│   ├── 4_Process_Compliance.py # 🔒 Placeholder
│   ├── 5_Revenue_per_Head.py   # 🔒 Placeholder
│   ├── 6_BD_Conversations.py   # 🔒 Placeholder
│   └── 7_Rock_Completion.py    # 🔒 Placeholder
└── utils/
    ├── __init__.py
    ├── constants.py            # TARGET_HOURS, thresholds, colours
    └── parse_clockify.py       # CSV parsing + calculation logic
```

---

## Clockify CSV Column Reference

The app expects Clockify's **Detailed Report** export, which includes these columns:

```
Project, Client, Description, Task, User, Group, Email, Tags,
Billable, Start Date, Start Time, End Date, End Time,
Duration (h), Duration (decimal), Billable Rate (EGP),
Billable Amount (EGP), Date of creation
```

Key fields used in calculations:

| Column | Usage |
|--------|-------|
| `User` | Team member identifier |
| `Billable` | `"Yes"` or `"No"` |
| `Duration (decimal)` | Numeric hours (e.g. `2.50`) — used for all maths |
| `Start Date` | `MM/DD/YYYY` format — used for week label auto-detection |

---

## Future Work

The following enhancements are planned but **not yet built**:

- **Direct Clockify API integration** — eliminate manual CSV uploads; pull data
  automatically via the Clockify REST API using an API key.
- **Historical data storage** — persist weekly snapshots in SQLite or Supabase
  so trends can be charted over time.
- **Additional scorecard modules** — complete modules 2–7 (Operational Health,
  Client Health, Process Compliance, Revenue per Head, BD Conversations, Rock
  Completion).
- **PDF / PNG export** — one-click export of the full dashboard for meeting
  records and async sharing.
- **Multi-workspace support** — separate data contexts for different teams or
  business units.

---

## Tech Stack

| Layer | Library |
|-------|---------|
| UI | [Streamlit](https://streamlit.io) ≥ 1.32 |
| Data | [pandas](https://pandas.pydata.org) ≥ 2.0 |
| Charts | [Plotly](https://plotly.com/python/) ≥ 5.18 |
| Language | Python 3.11+ |
